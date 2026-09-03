import os
import re
import time
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, request, session, render_template_string
import yfinance as yf

# ============================================================
# INVEST ANALYZER PRO
# Flask + Render + Yahoo Finance
# Carteira com cache para evitar "Too Many Requests"
# ============================================================

app = Flask(__name__)

# Use a strong SECRET_KEY environment variable on Render.
app.secret_key = os.environ.get("SECRET_KEY", "invest-analyzer-change-this-key")

# ------------------------------------------------------------
# Configuração do cache
# ------------------------------------------------------------
CACHE_TTL_SECONDS = int(os.environ.get("YAHOO_CACHE_TTL", "600"))  # 10 min
REQUEST_DELAY_SECONDS = float(os.environ.get("YAHOO_REQUEST_DELAY", "1.0"))

_price_cache = {}
_cache_lock = threading.Lock()
_last_yahoo_request = 0.0
_request_lock = threading.Lock()


# ============================================================
# UTILIDADES
# ============================================================

def normalize_symbol(symbol):
    """
    Converte automaticamente ações brasileiras:
      XPLG11 -> XPLG11.SA
      PETR4  -> PETR4.SA
      VALE3  -> VALE3.SA

    Símbolos americanos continuam iguais:
      AAPL -> AAPL
      MSFT -> MSFT
      NVDA -> NVDA

    Se o usuário já informar .SA, mantém.
    """
    if not symbol:
        return ""

    symbol = str(symbol).strip().upper().replace(" ", "")

    if symbol.endswith(".SA"):
        return symbol

    # A maioria dos tickers B3 possui 4 letras + 1 ou 2 números.
    if re.fullmatch(r"[A-Z]{4}\d{1,2}", symbol):
        return symbol + ".SA"

    return symbol


def display_symbol(symbol):
    """Remove .SA apenas para exibição."""
    symbol = normalize_symbol(symbol)
    return symbol[:-3] if symbol.endswith(".SA") else symbol


def to_float(value, default=0.0):
    try:
        value = float(value)
        if value != value:  # NaN
            return default
        return value
    except (TypeError, ValueError):
        return default


def format_brl(value):
    value = to_float(value)
    text = f"{value:,.2f}"
    return "R$ " + text.replace(",", "X").replace(".", ",").replace("X", ".")


def now_timestamp():
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# CACHE / YAHOO FINANCE
# ============================================================

def get_cached_price(symbol):
    """
    Retorna preço em cache se ainda estiver dentro do TTL.
    """
    with _cache_lock:
        item = _price_cache.get(symbol)

        if not item:
            return None

        age = time.time() - item["timestamp"]

        if age <= CACHE_TTL_SECONDS:
            return item.copy()

        # Mantemos o item expirado como fallback.
        return {
            **item,
            "expired": True,
            "age": age
        }


def save_price_cache(symbol, data):
    with _cache_lock:
        _price_cache[symbol] = {
            **data,
            "timestamp": time.time(),
            "updated_at": now_timestamp()
        }


def wait_before_yahoo_request():
    """
    Evita disparar várias requisições seguidas.
    """
    global _last_yahoo_request

    with _request_lock:
        elapsed = time.time() - _last_yahoo_request

        if elapsed < REQUEST_DELAY_SECONDS:
            time.sleep(REQUEST_DELAY_SECONDS - elapsed)

        _last_yahoo_request = time.time()


def fetch_yahoo_price(symbol):
    """
    Busca o último preço disponível no Yahoo Finance.
    Usa histórico de poucos dias para reduzir chamadas e
    evita Ticker.info, que costuma gerar muitas requisições.
    """
    yahoo_symbol = normalize_symbol(symbol)

    # 1) Cache válido
    cached = get_cached_price(yahoo_symbol)
    if cached and not cached.get("expired"):
        return {
            "ok": True,
            "symbol": yahoo_symbol,
            "price": cached["price"],
            "currency": cached.get("currency", "BRL" if yahoo_symbol.endswith(".SA") else "USD"),
            "source": "cache",
            "updated_at": cached.get("updated_at")
        }

    # 2) Se existe cache expirado, tentamos atualizar.
    # Se o Yahoo falhar, o último preço ainda poderá ser usado.
    stale_cache = cached

    try:
        wait_before_yahoo_request()

        ticker = yf.Ticker(yahoo_symbol)

        # Uma única chamada de histórico.
        history = ticker.history(
            period="5d",
            interval="1d",
            auto_adjust=False,
            actions=False
        )

        if history is None or history.empty:
            raise RuntimeError("Yahoo Finance não retornou dados para este ativo.")

        # Último fechamento/preço disponível.
        close_series = history["Close"].dropna()

        if close_series.empty:
            raise RuntimeError("Não foi possível encontrar um preço válido.")

        price = to_float(close_series.iloc[-1])

        if price <= 0:
            raise RuntimeError("Yahoo Finance retornou um preço inválido.")

        currency = "BRL" if yahoo_symbol.endswith(".SA") else "USD"

        data = {
            "price": price,
            "currency": currency,
            "source": "Yahoo Finance"
        }

        save_price_cache(yahoo_symbol, data)

        return {
            "ok": True,
            "symbol": yahoo_symbol,
            "price": price,
            "currency": currency,
            "source": "Yahoo Finance",
            "updated_at": now_timestamp()
        }

    except Exception as exc:
        error_text = str(exc)

        # 3) Fallback: último preço conhecido
        if stale_cache and stale_cache.get("price"):
            return {
                "ok": True,
                "symbol": yahoo_symbol,
                "price": stale_cache["price"],
                "currency": stale_cache.get(
                    "currency",
                    "BRL" if yahoo_symbol.endswith(".SA") else "USD"
                ),
                "source": "último preço em cache",
                "warning": "Yahoo Finance está temporariamente indisponível ou limitou as requisições.",
                "updated_at": stale_cache.get("updated_at")
            }

        return {
            "ok": False,
            "symbol": yahoo_symbol,
            "price": None,
            "error": (
                "Não foi possível consultar o Yahoo Finance agora. "
                "Aguarde alguns minutos e tente novamente."
            ),
            "details": error_text[:300]
        }


# ============================================================
# CARTEIRA
# ============================================================

def get_portfolio():
    portfolio = session.get("portfolio", [])
    if not isinstance(portfolio, list):
        portfolio = []
    return portfolio


def save_portfolio(portfolio):
    session["portfolio"] = portfolio
    session.modified = True


def calculate_portfolio(refresh_prices=False):
    portfolio = get_portfolio()

    total_invested = 0.0
    total_value = 0.0
    items = []

    for item in portfolio:
        symbol = normalize_symbol(item.get("symbol", ""))
        quantity = to_float(item.get("quantity", 0))
        average_price = to_float(item.get("average_price", 0))

        invested = quantity * average_price
        total_invested += invested

        price_data = fetch_yahoo_price(symbol)
        current_price = price_data.get("price") if price_data.get("ok") else None

        if current_price is not None:
            current_value = quantity * current_price
        else:
            current_value = 0.0

        profit = current_value - invested

        profitability = (profit / invested * 100) if invested else 0.0

        items.append({
            "symbol": display_symbol(symbol),
            "yahoo_symbol": symbol,
            "quantity": quantity,
            "average_price": average_price,
            "invested": invested,
            "current_price": current_price,
            "current_value": current_value,
            "profit": profit,
            "profitability": profitability,
            "currency": price_data.get("currency"),
            "price_source": price_data.get("source"),
            "warning": price_data.get("warning"),
            "error": price_data.get("error")
        })

        total_value += current_value

    profit_total = total_value - total_invested
    profitability_total = (
        profit_total / total_invested * 100
        if total_invested
        else 0.0
    )

    return {
        "items": items,
        "summary": {
            "invested": total_invested,
            "value": total_value,
            "profit": profit_total,
            "profitability": profitability_total
        }
    }


# ============================================================
# ROTAS API
# ============================================================

@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "Invest Analyzer Pro",
        "time": now_timestamp()
    })


@app.get("/api/portfolio")
def api_portfolio():
    try:
        return jsonify({
            "ok": True,
            **calculate_portfolio()
        })
    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 500


@app.post("/api/portfolio/add")
def add_asset():
    data = request.get_json(silent=True) or request.form

    symbol = normalize_symbol(data.get("symbol", ""))
    quantity = to_float(data.get("quantity"))
    average_price = to_float(
        data.get("average_price", data.get("price"))
    )

    if not symbol:
        return jsonify({"ok": False, "error": "Informe o código do ativo."}), 400

    if quantity <= 0:
        return jsonify({"ok": False, "error": "A quantidade deve ser maior que zero."}), 400

    if average_price <= 0:
        return jsonify({"ok": False, "error": "O preço médio deve ser maior que zero."}), 400

    portfolio = get_portfolio()

    # Se o ativo já existir, soma a posição usando preço médio ponderado.
    existing = next(
        (x for x in portfolio if normalize_symbol(x.get("symbol")) == symbol),
        None
    )

    if existing:
        old_quantity = to_float(existing.get("quantity"))
        old_average = to_float(existing.get("average_price"))

        new_quantity = old_quantity + quantity
        new_average = (
            (old_quantity * old_average) +
            (quantity * average_price)
        ) / new_quantity

        existing["quantity"] = new_quantity
        existing["average_price"] = new_average
    else:
        portfolio.append({
            "symbol": symbol,
            "quantity": quantity,
            "average_price": average_price
        })

    save_portfolio(portfolio)

    return jsonify({
        "ok": True,
        "message": f"{display_symbol(symbol)} adicionado à carteira.",
        **calculate_portfolio()
    })


@app.post("/api/portfolio/remove")
def remove_asset():
    data = request.get_json(silent=True) or request.form
    symbol = normalize_symbol(data.get("symbol", ""))

    if not symbol:
        return jsonify({"ok": False, "error": "Informe o ativo."}), 400

    portfolio = [
        item for item in get_portfolio()
        if normalize_symbol(item.get("symbol", "")) != symbol
    ]

    save_portfolio(portfolio)

    return jsonify({
        "ok": True,
        "message": f"{display_symbol(symbol)} removido.",
        **calculate_portfolio()
    })


@app.post("/api/portfolio/clear")
def clear_portfolio():
    session.pop("portfolio", None)

    return jsonify({
        "ok": True,
        "message": "Carteira limpa.",
        "items": [],
        "summary": {
            "invested": 0,
            "value": 0,
            "profit": 0,
            "profitability": 0
        }
    })


@app.get("/api/price/<symbol>")
def api_price(symbol):
    result = fetch_yahoo_price(symbol)
    status = 200 if result.get("ok") else 503
    return jsonify(result), status


# ============================================================
# PÁGINA
# ============================================================

HTML = r"""
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Invest Analyzer Pro</title>
<style>
*{box-sizing:border-box}
body{
    margin:0;
    background:#080b10;
    color:#f2f4f8;
    font-family:Arial,Helvetica,sans-serif;
}
.container{
    width:min(100%,760px);
    margin:auto;
    padding:22px;
}
.hero,.card{
    background:#10151c;
    border:1px solid #26303d;
    border-radius:26px;
    padding:28px;
    margin-bottom:22px;
}
.hero{
    background:#141b2b;
}
h1{font-size:34px;margin:0 0 12px}
h2{font-size:25px;margin:0 0 22px}
.subtitle{
    color:#aeb7c7;
    font-size:20px;
    line-height:1.35;
}
.grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:22px;
}
.stat{
    background:#10151c;
    border:1px solid #26303d;
    border-radius:25px;
    padding:28px;
}
.label{color:#aeb7c7;font-size:19px;margin-bottom:15px}
.value{font-size:31px;font-weight:700}
.negative{color:#f06c87}
.positive{color:#51d69b}
input{
    width:100%;
    background:#090d12;
    color:#f4f6f8;
    border:1px solid #354154;
    border-radius:17px;
    padding:19px 20px;
    font-size:20px;
    margin-bottom:16px;
    outline:none;
}
button{
    width:100%;
    border:0;
    border-radius:17px;
    padding:19px;
    background:#2d67e8;
    color:white;
    font-size:20px;
    font-weight:700;
    cursor:pointer;
}
button.secondary{
    background:#242c38;
}
button.danger{
    background:#6b2637;
}
.asset{
    border:1px solid #293442;
    border-radius:18px;
    padding:18px;
    margin-top:14px;
    background:#0c1117;
}
.asset-top{
    display:flex;
    justify-content:space-between;
    gap:15px;
}
.asset-symbol{font-size:23px;font-weight:700}
.small{color:#9fa9b8;font-size:15px;margin-top:5px}
.message{
    margin-top:15px;
    color:#aeb7c7;
    font-size:17px;
    line-height:1.4;
}
.footer{
    text-align:center;
    color:#707b8c;
    padding:10px 0 30px;
}
@media(max-width:600px){
    .container{padding:22px}
    .grid{gap:16px}
    .hero,.card,.stat{padding:24px}
    h1{font-size:31px}
    .subtitle{font-size:18px}
    .value{font-size:27px}
}
</style>
</head>
<body>
<div class="container">

<div class="hero">
    <h1>📈 Invest Analyzer Pro</h1>
    <div class="subtitle">
        Carteira + preços de ações com dados do Yahoo Finance
    </div>
</div>

<div class="grid">
    <div class="stat">
        <div class="label">Patrimônio</div>
        <div id="value">R$ 0,00</div>
    </div>
    <div class="stat">
        <div class="label">Investido</div>
        <div id="invested">R$ 0,00</div>
    </div>
    <div class="stat">
        <div class="label">Lucro / Prejuízo</div>
        <div id="profit">R$ 0,00</div>
    </div>
    <div class="stat">
        <div class="label">Rentabilidade</div>
        <div id="profitability">0,00%</div>
    </div>
</div>

<div class="card">
    <h2>➕ Adicionar ativo</h2>

    <input id="symbol" placeholder="Código — ex.: XPLG11, PETR4 ou AAPL">
    <input id="quantity" type="number" min="0" step="any" placeholder="Quantidade">
    <input id="average_price" type="number" min="0" step="any" placeholder="Preço médio">

    <button onclick="addAsset()">Adicionar</button>

    <div id="message" class="message"></div>
</div>

<div class="card">
    <h2>💼 Minha carteira</h2>
    <div id="portfolio">Carregando...</div>
</div>

<div class="card">
    <h2>🔎 Consultar ação</h2>
    <input id="searchSymbol" placeholder="Ex.: AAPL, MSFT, XPLG11">
    <button onclick="searchPrice()">Consultar preço</button>
    <div id="searchResult" class="message"></div>
</div>

<div class="footer">
    Dados de mercado: Yahoo Finance · Cache automático para reduzir bloqueios
</div>

</div>

<script>
function brl(v){
    return new Intl.NumberFormat('pt-BR',{
        style:'currency',
        currency:'BRL'
    }).format(Number(v || 0));
}

function pct(v){
    return Number(v || 0).toFixed(2).replace('.',',') + '%';
}

function setProfitClass(el, value){
    el.className = Number(value) < 0 ? 'value negative' :
                   Number(value) > 0 ? 'value positive' : 'value';
}

async function loadPortfolio(){
    try{
        const response = await fetch('/api/portfolio');
        const data = await response.json();

        if(!data.ok){
            throw new Error(data.error || 'Erro ao carregar carteira.');
        }

        const s = data.summary || {};

        document.getElementById('value').textContent = brl(s.value);
        document.getElementById('invested').textContent = brl(s.invested);

        const profit = document.getElementById('profit');
        profit.textContent = brl(s.profit);
        setProfitClass(profit, s.profit);

        const profitability = document.getElementById('profitability');
        profitability.textContent = pct(s.profitability);
        setProfitClass(profitability, s.profitability);

        const box = document.getElementById('portfolio');

        if(!data.items || data.items.length === 0){
            box.innerHTML = '<div class="message">Nenhum ativo cadastrado ainda.</div>';
            return;
        }

        box.innerHTML = data.items.map(item => {
            const price = item.current_price == null
                ? 'Indisponível'
                : brl(item.current_price);

            const profitClass = Number(item.profit) < 0
                ? 'negative'
                : Number(item.profit) > 0
                    ? 'positive'
                    : '';

            return `
                <div class="asset">
                    <div class="asset-top">
                        <div>
                            <div class="asset-symbol">${escapeHtml(item.symbol)}</div>
                            <div class="small">
                                ${item.quantity} cotas · PM ${brl(item.average_price)}
                            </div>
                        </div>
                        <div style="text-align:right">
                            <div>${price}</div>
                            <div class="${profitClass}">
                                ${brl(item.profit)}
                            </div>
                        </div>
                    </div>
                    <div class="small">
                        Fonte: ${escapeHtml(item.price_source || 'Yahoo Finance')}
                    </div>
                    ${item.warning ? `<div class="message">${escapeHtml(item.warning)}</div>` : ''}
                    ${item.error ? `<div class="message">${escapeHtml(item.error)}</div>` : ''}
                    <button class="danger" style="margin-top:14px"
                        onclick="removeAsset('${encodeURIComponent(item.yahoo_symbol)}')">
                        Remover
                    </button>
                </div>
            `;
        }).join('');

    }catch(error){
        document.getElementById('portfolio').innerHTML =
            '<div class="message">Erro: ' + escapeHtml(error.message) + '</div>';
    }
}

function escapeHtml(text){
    return String(text ?? '')
        .replaceAll('&','&amp;')
        .replaceAll('<','&lt;')
        .replaceAll('>','&gt;')
        .replaceAll('"','&quot;')
        .replaceAll("'","&#039;");
}

async function addAsset(){
    const symbol = document.getElementById('symbol').value.trim();
    const quantity = document.getElementById('quantity').value;
    const average_price = document.getElementById('average_price').value;
    const message = document.getElementById('message');

    if(!symbol || !quantity || !average_price){
        message.textContent = 'Preencha código, quantidade e preço médio.';
        return;
    }

    message.textContent = 'Adicionando ativo...';

    try{
        const response = await fetch('/api/portfolio/add',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({
                symbol,
                quantity,
                average_price
            })
        });

        const data = await response.json();

        if(!data.ok){
            throw new Error(data.error || 'Não foi possível adicionar.');
        }

        message.textContent = data.message;

        document.getElementById('symbol').value = '';
        document.getElementById('quantity').value = '';
        document.getElementById('average_price').value = '';

        renderFromData(data);

    }catch(error){
        message.textContent = error.message;
    }
}

async function removeAsset(symbol){
    try{
        const response = await fetch('/api/portfolio/remove',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({
                symbol:decodeURIComponent(symbol)
            })
        });

        const data = await response.json();

        if(!data.ok){
            throw new Error(data.error || 'Erro ao remover.');
        }

        renderFromData(data);
    }catch(error){
        document.getElementById('message').textContent = error.message;
    }
}

function renderFromData(data){
    const s = data.summary || {};

    document.getElementById('value').textContent = brl(s.value);
    document.getElementById('invested').textContent = brl(s.invested);

    const profit = document.getElementById('profit');
    profit.textContent = brl(s.profit);
    setProfitClass(profit, s.profit);

    const profitability = document.getElementById('profitability');
    profitability.textContent = pct(s.profitability);
    setProfitClass(profitability, s.profitability);

    loadPortfolio();
}

async function searchPrice(){
    const symbol = document.getElementById('searchSymbol').value.trim();
    const result = document.getElementById('searchResult');

    if(!symbol){
        result.textContent = 'Informe um código de ação.';
        return;
    }

    result.textContent = 'Consultando Yahoo Finance...';

    try{
        const response = await fetch('/api/price/' + encodeURIComponent(symbol));
        const data = await response.json();

        if(!data.ok){
            throw new Error(data.error || 'Preço indisponível.');
        }

        result.innerHTML =
            '<strong>' + escapeHtml(data.symbol) + '</strong><br>' +
            'Preço: <strong>' + brl(data.price) + '</strong><br>' +
            'Fonte: ' + escapeHtml(data.source || 'Yahoo Finance');

        if(data.warning){
            result.innerHTML += '<br>' + escapeHtml(data.warning);
        }

    }catch(error){
        result.textContent = error.message;
    }
}

loadPortfolio();
</script>
</body>
</html>
"""


@app.get("/")
def home():
    return render_template_string(HTML)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False)
