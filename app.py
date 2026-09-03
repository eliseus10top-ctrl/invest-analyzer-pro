# ================================================================
# INVEST ANALYZER PRO — Flask / Render
# Aplicativo completo em um único app.py
# ================================================================

from flask import Flask, request, render_template_string, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
import math
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# ----------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------

PORTFOLIO = []


# ----------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ----------------------------------------------------------------

def clean_number(value, default=0.0):
    try:
        if value is None:
            return default
        if isinstance(value, str):
            value = value.replace(".", "").replace(",", ".")
        return float(value)
    except Exception:
        return default


def br_money(value):
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def br_percent(value):
    try:
        return f"{float(value):.2f}%".replace(".", ",")
    except Exception:
        return "0,00%"


def safe_float(value):
    try:
        if value is None:
            return None
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    except Exception:
        return None


def get_info_value(info, *keys):
    for key in keys:
        value = info.get(key)
        if value is not None:
            return safe_float(value)
    return None


def normalize_ticker(ticker):
    ticker = (ticker or "").strip().upper()
    if not ticker:
        return ""
    # Yahoo Finance usa .SA para ações brasileiras.
    if ticker.isalpha() and ticker.endswith(("3", "4", "5", "6", "11")):
        pass
    return ticker


def yahoo_ticker(ticker):
    ticker = normalize_ticker(ticker)
    if not ticker:
        return ticker

    # Se o usuário informou explicitamente um mercado, respeitamos.
    if "." in ticker or "^" in ticker or "=" in ticker:
        return ticker

    # Principais ETFs/ações americanas continuam sem .SA.
    # Para tickers brasileiros comuns, adicionamos .SA.
    brazil_suffixes = ("3", "4", "5", "6", "11")
    if ticker.endswith(brazil_suffixes):
        return ticker + ".SA"

    return ticker


def download_history(ticker, period="1y", interval="1d"):
    symbol = yahoo_ticker(ticker)
    try:
        data = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False
        )
        if data is None or data.empty:
            return None

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.dropna(how="all")
        return data
    except Exception:
        return None


def get_asset_data(ticker):
    symbol = yahoo_ticker(ticker)

    try:
        obj = yf.Ticker(symbol)

        info = {}
        try:
            info = obj.info or {}
        except Exception:
            info = {}

        history = None
        try:
            history = obj.history(period="1y", interval="1d", auto_adjust=False)
        except Exception:
            history = download_history(symbol)

        if history is None or history.empty:
            return {
                "ok": False,
                "ticker": ticker,
                "symbol": symbol,
                "error": "Yahoo Finance não retornou dados para este ativo."
            }

        close = history["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        close = pd.to_numeric(close, errors="coerce").dropna()

        if close.empty:
            return {
                "ok": False,
                "ticker": ticker,
                "symbol": symbol,
                "error": "Não foi possível obter preços."
            }

        current = safe_float(close.iloc[-1]) or 0
        previous = safe_float(close.iloc[-2]) if len(close) > 1 else current

        change_day = ((current / previous) - 1) * 100 if previous else 0
        first = safe_float(close.iloc[0])
        change_year = ((current / first) - 1) * 100 if first else 0

        # Médias móveis
        sma20 = safe_float(close.rolling(20).mean().iloc[-1])
        sma50 = safe_float(close.rolling(50).mean().iloc[-1])
        sma200 = safe_float(close.rolling(200).mean().iloc[-1])

        # Volatilidade anualizada
        returns = close.pct_change().dropna()
        volatility = safe_float(returns.std() * np.sqrt(252) * 100)

        # RSI 14
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi_series = 100 - (100 / (1 + rs))
        rsi = safe_float(rsi_series.iloc[-1])

        # Máxima/mínima de 52 semanas
        high_52 = safe_float(close.max())
        low_52 = safe_float(close.min())

        # Fundamentais
        market_cap = get_info_value(info, "marketCap")
        pe = get_info_value(info, "trailingPE", "forwardPE")
        pb = get_info_value(info, "priceToBook")
        eps = get_info_value(info, "trailingEps")
        dividend_yield = get_info_value(info, "dividendYield")
        if dividend_yield is not None and dividend_yield < 1:
            dividend_yield *= 100

        roe = get_info_value(info, "returnOnEquity")
        if roe is not None and abs(roe) < 2:
            roe *= 100

        roa = get_info_value(info, "returnOnAssets")
        if roa is not None and abs(roa) < 2:
            roa *= 100

        debt_equity = get_info_value(info, "debtToEquity")
        revenue_growth = get_info_value(info, "revenueGrowth")
        if revenue_growth is not None and abs(revenue_growth) < 2:
            revenue_growth *= 100

        earnings_growth = get_info_value(info, "earningsGrowth")
        if earnings_growth is not None and abs(earnings_growth) < 2:
            earnings_growth *= 100

        target_price = get_info_value(info, "targetMeanPrice")
        fifty_two_high = get_info_value(info, "fiftyTwoWeekHigh")
        fifty_two_low = get_info_value(info, "fiftyTwoWeekLow")

        company = info.get("longName") or info.get("shortName") or ticker
        sector = info.get("sector") or "—"
        industry = info.get("industry") or "—"

        # Score simples e transparente
        score = 0
        score_items = 0

        if pe is not None:
            score_items += 1
            if 0 < pe <= 15:
                score += 2
            elif 15 < pe <= 25:
                score += 1

        if pb is not None:
            score_items += 1
            if 0 < pb <= 2:
                score += 2
            elif 2 < pb <= 4:
                score += 1

        if roe is not None:
            score_items += 1
            if roe >= 15:
                score += 2
            elif roe >= 8:
                score += 1

        if revenue_growth is not None:
            score_items += 1
            if revenue_growth > 10:
                score += 2
            elif revenue_growth > 0:
                score += 1

        if rsi is not None:
            score_items += 1
            if 35 <= rsi <= 65:
                score += 2
            elif 25 <= rsi < 35 or 65 < rsi <= 75:
                score += 1

        max_score = score_items * 2
        score_pct = (score / max_score * 100) if max_score else 0

        if score_pct >= 75:
            rating = "Excelente"
        elif score_pct >= 55:
            rating = "Boa"
        elif score_pct >= 35:
            rating = "Neutra"
        else:
            rating = "Atenção"

        # Dados para gráfico
        chart = []
        for idx, value in close.tail(180).items():
            try:
                chart.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "close": round(float(value), 4)
                })
            except Exception:
                pass

        return {
            "ok": True,
            "ticker": ticker,
            "symbol": symbol,
            "company": company,
            "sector": sector,
            "industry": industry,
            "price": current,
            "change_day": change_day,
            "change_year": change_year,
            "sma20": sma20,
            "sma50": sma50,
            "sma200": sma200,
            "rsi": rsi,
            "volatility": volatility,
            "high_52": high_52,
            "low_52": low_52,
            "market_cap": market_cap,
            "pe": pe,
            "pb": pb,
            "eps": eps,
            "dividend_yield": dividend_yield,
            "roe": roe,
            "roa": roa,
            "debt_equity": debt_equity,
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "target_price": target_price,
            "fifty_two_high": fifty_two_high,
            "fifty_two_low": fifty_two_low,
            "score": round(score_pct),
            "rating": rating,
            "chart": chart,
            "updated": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

    except Exception as exc:
        return {
            "ok": False,
            "ticker": ticker,
            "symbol": symbol,
            "error": f"Erro ao consultar Yahoo Finance: {exc}"
        }


def portfolio_summary():
    total_cost = 0
    total_value = 0
    positions = []

    for item in PORTFOLIO:
        ticker = item["ticker"]
        qty = item["quantity"]
        average = item["average"]

        data = get_asset_data(ticker)
        current = data.get("price", 0) if data.get("ok") else average

        cost = qty * average
        value = qty * current
        profit = value - cost
        profit_pct = (profit / cost * 100) if cost else 0

        total_cost += cost
        total_value += value

        positions.append({
            **item,
            "symbol": data.get("symbol", yahoo_ticker(ticker)),
            "company": data.get("company", ticker),
            "current": current,
            "cost": cost,
            "value": value,
            "profit": profit,
            "profit_pct": profit_pct
        })

    total_profit = total_value - total_cost
    total_profit_pct = (total_profit / total_cost * 100) if total_cost else 0

    return {
        "positions": positions,
        "total_cost": total_cost,
        "total_value": total_value,
        "total_profit": total_profit,
        "total_profit_pct": total_profit_pct
    }


# ----------------------------------------------------------------
# HTML
# ----------------------------------------------------------------

HTML = r"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Invest Analyzer Pro</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
:root {
    --bg:#08111f;
    --card:#101c2e;
    --card2:#14243a;
    --text:#f3f6fb;
    --muted:#9eacc0;
    --border:#253750;
    --accent:#4da3ff;
    --green:#39d98a;
    --red:#ff6574;
    --yellow:#f6c85f;
}
* { box-sizing:border-box; }
body {
    margin:0;
    font-family:Arial,Helvetica,sans-serif;
    background:linear-gradient(180deg,#07101c,#0b1524);
    color:var(--text);
}
.container { max-width:1400px; margin:auto; padding:20px; }
header {
    display:flex; justify-content:space-between; align-items:center;
    gap:20px; margin-bottom:20px; flex-wrap:wrap;
}
.logo { font-size:25px; font-weight:800; }
.subtitle { color:var(--muted); font-size:13px; margin-top:4px; }
.search {
    display:flex; gap:8px; width:min(520px,100%);
}
input, button, select {
    border:1px solid var(--border);
    border-radius:10px;
    padding:12px;
    background:#0c1728;
    color:var(--text);
    font-size:14px;
}
input { flex:1; min-width:0; }
button {
    background:var(--accent);
    color:white;
    font-weight:700;
    cursor:pointer;
}
button:hover { opacity:.9; }
.nav {
    display:flex; gap:8px; flex-wrap:wrap; margin-bottom:18px;
}
.nav button { background:var(--card); border:1px solid var(--border); }
.nav button.active { background:var(--accent); }
.grid {
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:14px;
}
.card {
    background:rgba(16,28,46,.95);
    border:1px solid var(--border);
    border-radius:15px;
    padding:17px;
    box-shadow:0 8px 30px rgba(0,0,0,.15);
}
.metric-title { color:var(--muted); font-size:12px; }
.metric { font-size:25px; font-weight:800; margin-top:8px; }
.small { color:var(--muted); font-size:12px; }
.green { color:var(--green); }
.red { color:var(--red); }
.yellow { color:var(--yellow); }
.section { margin-top:16px; }
.section h2 { margin:0 0 12px; font-size:19px; }
.two { display:grid; grid-template-columns:2fr 1fr; gap:14px; }
.table-wrap { overflow:auto; }
table { width:100%; border-collapse:collapse; min-width:700px; }
th,td { padding:12px 10px; border-bottom:1px solid var(--border); text-align:left; }
th { color:var(--muted); font-size:12px; }
.form-grid {
    display:grid; grid-template-columns:1fr 1fr 1fr auto; gap:8px;
}
.badge {
    display:inline-block; padding:6px 9px; border-radius:999px;
    background:var(--card2); font-size:12px;
}
.bar {
    height:9px; border-radius:99px; background:#22334b; overflow:hidden;
    margin-top:8px;
}
.bar > div { height:100%; background:var(--accent); }
.empty { color:var(--muted); padding:25px 0; }
.alert {
    padding:13px; border-radius:10px; background:#25151a;
    border:1px solid #6b2935; color:#ffb6bf; margin-bottom:15px;
}
footer { color:var(--muted); text-align:center; padding:35px 0 15px; font-size:12px; }
@media(max-width:1000px) {
    .grid { grid-template-columns:repeat(2,1fr); }
    .two { grid-template-columns:1fr; }
}
@media(max-width:600px) {
    .container { padding:12px; }
    .grid { grid-template-columns:1fr 1fr; gap:8px; }
    .metric { font-size:19px; }
    .form-grid { grid-template-columns:1fr; }
    header { align-items:stretch; }
    .search { width:100%; }
}
</style>
</head>
<body>
<div class="container">

<header>
    <div>
        <div class="logo">📊 Invest Analyzer Pro</div>
        <div class="subtitle">Carteira • Yahoo Finance • Fundamentalista • Técnica • Gráficos</div>
    </div>
    <form class="search" method="get" action="/">
        <input name="ticker" placeholder="Digite um ticker: PETR4, VALE3, AAPL, MSFT..." value="{{ ticker or '' }}">
        <button type="submit">Analisar</button>
    </form>
</header>

<div class="nav">
    <button class="active" onclick="showSection('dashboard')">Dashboard</button>
    <button onclick="showSection('portfolio')">Carteira</button>
    <button onclick="showSection('analysis')">Análise</button>
</div>

{% if error %}
<div class="alert">{{ error }}</div>
{% endif %}

<section id="dashboard">
<div class="grid">
    <div class="card">
        <div class="metric-title">Patrimônio</div>
        <div class="metric">{{ summary.total_value|money }}</div>
    </div>
    <div class="card">
        <div class="metric-title">Custo da carteira</div>
        <div class="metric">{{ summary.total_cost|money }}</div>
    </div>
    <div class="card">
        <div class="metric-title">Lucro / Prejuízo</div>
        <div class="metric {{ 'green' if summary.total_profit >= 0 else 'red' }}">
            {{ summary.total_profit|money }}
        </div>
    </div>
    <div class="card">
        <div class="metric-title">Rentabilidade</div>
        <div class="metric {{ 'green' if summary.total_profit_pct >= 0 else 'red' }}">
            {{ summary.total_profit_pct|percent }}
        </div>
    </div>
</div>

<div class="section two">
    <div class="card">
        <h2>📈 Mercado</h2>
        {% if asset %}
            <div class="grid">
                <div>
                    <div class="metric-title">{{ asset.company }}</div>
                    <div class="metric">{{ asset.price|money }}</div>
                    <div class="{{ 'green' if asset.change_day >= 0 else 'red' }}">
                        Hoje: {{ asset.change_day|percent }}
                    </div>
                </div>
                <div>
                    <div class="metric-title">1 ano</div>
                    <div class="metric {{ 'green' if asset.change_year >= 0 else 'red' }}">
                        {{ asset.change_year|percent }}
                    </div>
                </div>
                <div>
                    <div class="metric-title">RSI 14</div>
                    <div class="metric">{{ asset.rsi|number }}</div>
                </div>
                <div>
                    <div class="metric-title">Score</div>
                    <div class="metric">{{ asset.score }}/100</div>
                </div>
            </div>
            <div id="chart" style="height:430px;"></div>
        {% else %}
            <div class="empty">Pesquise um ativo acima para carregar os dados do Yahoo Finance.</div>
        {% endif %}
    </div>

    <div class="card">
        <h2>🧠 Indicadores</h2>
        {% if asset %}
            <p><span class="badge">{{ asset.rating }}</span></p>
            <p>P/L: <b>{{ asset.pe|number }}</b></p>
            <p>P/VP: <b>{{ asset.pb|number }}</b></p>
            <p>Dividend Yield: <b>{{ asset.dividend_yield|percent }}</b></p>
            <p>ROE: <b>{{ asset.roe|percent }}</b></p>
            <p>Dívida/Patrimônio: <b>{{ asset.debt_equity|number }}</b></p>
            <p>Crescimento receita: <b>{{ asset.revenue_growth|percent }}</b></p>
            <p>Volatilidade: <b>{{ asset.volatility|percent }}</b></p>
        {% else %}
            <div class="empty">Sem ativo selecionado.</div>
        {% endif %}
    </div>
</div>
</section>

<section id="portfolio" class="section">
<div class="card">
    <h2>💼 Minha Carteira</h2>
    <form method="post" action="/portfolio/add">
        <div class="form-grid">
            <input name="ticker" placeholder="Ticker (ex.: PETR4)" required>
            <input name="quantity" type="number" step="any" min="0" placeholder="Quantidade" required>
            <input name="average" type="number" step="any" min="0" placeholder="Preço médio" required>
            <button type="submit">Adicionar</button>
        </div>
    </form>

    {% if summary.positions %}
    <div class="table-wrap" style="margin-top:15px;">
    <table>
        <thead>
        <tr>
            <th>Ativo</th><th>Qtd.</th><th>Preço médio</th><th>Atual</th>
            <th>Patrimônio</th><th>Resultado</th><th></th>
        </tr>
        </thead>
        <tbody>
        {% for p in summary.positions %}
        <tr>
            <td><b>{{ p.ticker }}</b><br><span class="small">{{ p.company }}</span></td>
            <td>{{ p.quantity|number }}</td>
            <td>{{ p.average|money }}</td>
            <td>{{ p.current|money }}</td>
            <td>{{ p.value|money }}</td>
            <td class="{{ 'green' if p.profit >= 0 else 'red' }}">
                {{ p.profit|money }}<br>{{ p.profit_pct|percent }}
            </td>
            <td>
                <form method="post" action="/portfolio/remove">
                    <input type="hidden" name="ticker" value="{{ p.ticker }}">
                    <button type="submit">Excluir</button>
                </form>
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
    </div>
    {% else %}
        <div class="empty">Sua carteira está vazia. Adicione seu primeiro ativo.</div>
    {% endif %}
</div>
</section>

<section id="analysis" class="section">
<div class="card">
    <h2>🔎 Análise completa</h2>
    {% if asset %}
        <div class="grid">
            <div>
                <div class="metric-title">Empresa</div>
                <b>{{ asset.company }}</b>
            </div>
            <div>
                <div class="metric-title">Setor</div>
                <b>{{ asset.sector }}</b>
            </div>
            <div>
                <div class="metric-title">Indústria</div>
                <b>{{ asset.industry }}</b>
            </div>
            <div>
                <div class="metric-title">Atualização</div>
                <b>{{ asset.updated }}</b>
            </div>
        </div>

        <div class="grid" style="margin-top:15px;">
            <div class="card">
                <div class="metric-title">Média 20 dias</div>
                <div class="metric">{{ asset.sma20|money }}</div>
            </div>
            <div class="card">
                <div class="metric-title">Média 50 dias</div>
                <div class="metric">{{ asset.sma50|money }}</div>
            </div>
            <div class="card">
                <div class="metric-title">Média 200 dias</div>
                <div class="metric">{{ asset.sma200|money }}</div>
            </div>
            <div class="card">
                <div class="metric-title">Máxima 1 ano</div>
                <div class="metric">{{ asset.high_52|money }}</div>
            </div>
        </div>

        <div style="margin-top:18px;">
            <h3>Leitura dos indicadores</h3>
            <ul>
                <li>RSI: {% if asset.rsi is not none %}{{ asset.rsi|number }}{% else %}sem dado{% endif %}. Valores muito baixos podem indicar sobrevenda e valores muito altos podem indicar sobrecompra.</li>
                <li>P/L: {% if asset.pe is not none %}{{ asset.pe|number }}{% else %}sem dado{% endif %}. Deve ser comparado com empresas do mesmo setor.</li>
                <li>ROE: {% if asset.roe is not none %}{{ asset.roe|percent }}{% else %}sem dado{% endif %}. Quanto maior e sustentável, melhor tende a ser a eficiência do capital.</li>
                <li>Dividend Yield: {% if asset.dividend_yield is not none %}{{ asset.dividend_yield|percent }}{% else %}sem dado{% endif %}.</li>
                <li>Score interno: <b>{{ asset.score }}/100</b> — não é recomendação de compra ou venda.</li>
            </ul>
        </div>
    {% else %}
        <div class="empty">Digite um ticker para gerar a análise.</div>
    {% endif %}
</div>
</section>

<footer>
    Invest Analyzer Pro • Dados de mercado fornecidos pelo Yahoo Finance.
    Ferramenta educacional; não constitui recomendação de investimento.
</footer>

</div>

<script>
function showSection(id) {
    document.querySelectorAll('section').forEach(s => s.style.display = 'none');
    document.getElementById(id).style.display = 'block';
}
showSection('dashboard');

{% if asset and asset.chart %}
const chart = {{ asset.chart|tojson }};
Plotly.newPlot('chart', [{
    x: chart.map(x => x.date),
    y: chart.map(x => x.close),
    type: 'scatter',
    mode: 'lines',
    name: '{{ asset.ticker }}'
}], {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: {color:'#f3f6fb'},
    margin: {l:45,r:20,t:20,b:45},
    xaxis: {gridcolor:'#253750'},
    yaxis: {gridcolor:'#253750', tickprefix:'R$ '},
    hovermode:'x unified'
}, {responsive:true, displaylogo:false});
{% endif %}
</script>
</body>
</html>
"""


# ----------------------------------------------------------------
# FILTROS JINJA
# ----------------------------------------------------------------

@app.template_filter("money")
def money_filter(value):
    return br_money(value)


@app.template_filter("percent")
def percent_filter(value):
    if value is None:
        return "—"
    return br_percent(value)


@app.template_filter("number")
def number_filter(value):
    if value is None:
        return "—"
    try:
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


# ----------------------------------------------------------------
# ROTAS
# ----------------------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    ticker = request.args.get("ticker", "").strip().upper()
    asset = None
    error = None

    if ticker:
        asset = get_asset_data(ticker)
        if not asset.get("ok"):
            error = asset.get("error", "Não foi possível analisar o ativo.")

    summary = portfolio_summary()

    return render_template_string(
        HTML,
        ticker=ticker,
        asset=asset,
        summary=summary,
        error=error
    )


@app.route("/portfolio/add", methods=["POST"])
def add_portfolio():
    ticker = request.form.get("ticker", "").strip().upper()
    quantity = clean_number(request.form.get("quantity"))
    average = clean_number(request.form.get("average"))

    if ticker and quantity > 0 and average >= 0:
        # Se já existir, soma a posição usando custo total.
        existing = next((x for x in PORTFOLIO if x["ticker"] == ticker), None)

        if existing:
            old_qty = existing["quantity"]
            old_avg = existing["average"]
            total_cost = old_qty * old_avg + quantity * average
            new_qty = old_qty + quantity
            existing["quantity"] = new_qty
            existing["average"] = total_cost / new_qty if new_qty else 0
        else:
            PORTFOLIO.append({
                "ticker": ticker,
                "quantity": quantity,
                "average": average
            })

    return home()


@app.route("/portfolio/remove", methods=["POST"])
def remove_portfolio():
    ticker = request.form.get("ticker", "").strip().upper()
    PORTFOLIO[:] = [x for x in PORTFOLIO if x["ticker"] != ticker]
    return home()


@app.route("/api/analyze/<ticker>", methods=["GET"])
def api_analyze(ticker):
    data = get_asset_data(ticker)
    return jsonify(data)


@app.route("/api/portfolio", methods=["GET"])
def api_portfolio():
    return jsonify(portfolio_summary())


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Invest Analyzer Pro",
        "time": datetime.now().isoformat()
    })


# ----------------------------------------------------------------
# RENDER / PRODUÇÃO
# ----------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False)
