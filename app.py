import os
import math
import time
from datetime import datetime

import requests
import pandas as pd
import yfinance as yf
from flask import Flask, jsonify, render_template_string, request, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "invest-analyzer-render-change-this-key")

# ============================================================
# INVEST ANALYZER PRO
# Flask + Render + Yahoo Finance
# ============================================================

HTML = r"""
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Invest Analyzer Pro</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#0b0f14;color:#f2f5f7;font-family:Arial,Helvetica,sans-serif}
.container{max-width:1180px;margin:auto;padding:20px}
header{background:linear-gradient(135deg,#111827,#172033);border:1px solid #263244;border-radius:18px;padding:22px;margin-bottom:18px}
h1{margin:0 0 7px;font-size:28px}
.sub{color:#aab4c0}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px}
.card{background:#11161d;border:1px solid #25303d;border-radius:16px;padding:17px}
.label{font-size:13px;color:#98a4b2;margin-bottom:8px}
.value{font-size:23px;font-weight:700}
.form{display:grid;grid-template-columns:1.1fr .8fr .9fr auto;gap:10px}
input,button,select{width:100%;border:1px solid #344253;border-radius:10px;padding:13px;background:#0c1117;color:#fff;font-size:15px}
button{cursor:pointer;background:#2563eb;border-color:#2563eb;font-weight:700}
button.secondary{background:#1b2430;border-color:#344253}
button.danger{background:#b91c1c;border-color:#b91c1c}
button:hover{filter:brightness(1.1)}
.section{background:#11161d;border:1px solid #25303d;border-radius:16px;padding:18px;margin-bottom:18px}
.section h2{margin-top:0;font-size:19px}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:12px 8px;border-bottom:1px solid #26303b;font-size:14px}
th{color:#9eabb8}
.positive{color:#34d399}.negative{color:#fb7185}.muted{color:#9eabb8}
.actions{display:flex;gap:8px;flex-wrap:wrap}
.status{margin-top:10px;min-height:20px;color:#9eabb8}
.result{display:none;margin-top:15px}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.metric{background:#0c1117;border:1px solid #273341;border-radius:12px;padding:13px}
.metric b{display:block;margin-top:5px;font-size:17px}
.badge{display:inline-block;border-radius:999px;padding:5px 9px;background:#1e293b;color:#cbd5e1;font-size:12px}
@media(max-width:850px){.grid{grid-template-columns:repeat(2,1fr)}.form{grid-template-columns:1fr 1fr}.form button{grid-column:1/-1}.metrics{grid-template-columns:1fr 1fr}}
@media(max-width:520px){.container{padding:12px}header{padding:18px}.grid{grid-template-columns:1fr 1fr}.value{font-size:18px}.form{grid-template-columns:1fr}.form button{grid-column:auto}th,td{padding:9px 5px;font-size:12px}.hide-mobile{display:none}.metrics{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="container">
<header>
<h1>📈 Invest Analyzer Pro</h1>
<div class="sub">Carteira + análise de ações com dados do Yahoo Finance</div>
</header>

<div class="grid">
<div class="card"><div class="label">Patrimônio</div><div id="patrimonio" class="value">R$ 0,00</div></div>
<div class="card"><div class="label">Investido</div><div id="investido" class="value">R$ 0,00</div></div>
<div class="card"><div class="label">Lucro / Prejuízo</div><div id="lucro" class="value">R$ 0,00</div></div>
<div class="card"><div class="label">Rentabilidade</div><div id="rentabilidade" class="value">0,00%</div></div>
</div>

<div class="section">
<h2>➕ Adicionar ativo</h2>
<div class="form">
<input id="symbol" placeholder="Ticker: AAPL, MSFT, NVDA..." autocomplete="off">
<input id="quantity" type="number" step="any" min="0" placeholder="Quantidade">
<input id="avg_price" type="number" step="any" min="0" placeholder="Preço médio (USD)">
<button onclick="addAsset()">Adicionar</button>
</div>
<div id="status" class="status"></div>
</div>

<div class="section">
<h2>🔎 Analisar ação</h2>
<div class="form">
<input id="analysisSymbol" placeholder="Ex.: AAPL">
<button onclick="analyze()" style="grid-column:auto">Analisar</button>
</div>
<div id="analysisResult" class="result"></div>
</div>

<div class="section">
<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
<h2 style="margin-bottom:0">💼 Minha carteira</h2>
<button class="danger" style="width:auto" onclick="clearPortfolio()">Limpar carteira</button>
</div>
<div style="overflow-x:auto;margin-top:10px">
<table>
<thead><tr><th>Ativo</th><th>Qtd.</th><th>Preço médio</th><th>Atual</th><th>Valor</th><th>Resultado</th><th></th></tr></thead>
<tbody id="portfolio"></tbody>
</table>
</div>
</div>
</div>

<script>
function money(v){return new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(v)||0)}
function usd(v){return '$ '+(Number(v)||0).toFixed(2)}
function pct(v){return (Number(v)||0).toFixed(2)+'%'}
function esc(s){return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]))}

async function loadPortfolio(){
  const r=await fetch('/api/portfolio');
  const d=await r.json();
  if(!d.ok){document.getElementById('status').textContent=d.error||'Erro';return}
  document.getElementById('patrimonio').textContent=money(d.summary.market_value_brl);
  document.getElementById('investido').textContent=money(d.summary.invested_brl);
  const l=document.getElementById('lucro');
  l.textContent=money(d.summary.profit_brl);
  l.className='value '+(d.summary.profit_brl>=0?'positive':'negative');
  const rr=document.getElementById('rentabilidade');
  rr.textContent=pct(d.summary.return_pct);
  rr.className='value '+(d.summary.return_pct>=0?'positive':'negative');

  const body=document.getElementById('portfolio');
  if(!d.items.length){body.innerHTML='<tr><td colspan="7" class="muted">Nenhum ativo cadastrado.</td></tr>';return}
  body.innerHTML=d.items.map((x,i)=>`
  <tr>
    <td><b>${esc(x.symbol)}</b></td>
    <td>${x.quantity}</td>
    <td>${usd(x.avg_price)}</td>
    <td>${x.price===null?'—':usd(x.price)}</td>
    <td>${money(x.market_value_brl)}</td>
    <td class="${x.profit>=0?'positive':'negative'}">${money(x.profit_brl)}</td>
    <td><button class="danger" style="width:auto;padding:7px 10px" onclick="removeAsset(${i})">X</button></td>
  </tr>`).join('');
}

async function addAsset(){
  const symbol=document.getElementById('symbol').value.trim().toUpperCase();
  const quantity=Number(document.getElementById('quantity').value);
  const avg_price=Number(document.getElementById('avg_price').value);
  const s=document.getElementById('status');
  if(!symbol||quantity<=0||avg_price<0){s.textContent='Preencha ticker, quantidade e preço médio.';return}
  s.textContent='Consultando Yahoo Finance...';
  const r=await fetch('/api/portfolio',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({symbol,quantity,avg_price})});
  const d=await r.json();
  s.textContent=d.ok?'Ativo adicionado.':(d.error||'Erro ao adicionar.');
  if(d.ok){document.getElementById('symbol').value='';document.getElementById('quantity').value='';document.getElementById('avg_price').value='';loadPortfolio()}
}
async function removeAsset(i){
  await fetch('/api/portfolio/'+i,{method:'DELETE'});
  loadPortfolio();
}
async function clearPortfolio(){
  if(!confirm('Deseja realmente limpar a carteira?'))return;
  await fetch('/api/portfolio',{method:'DELETE'});
  loadPortfolio();
}
async function analyze(){
  const symbol=document.getElementById('analysisSymbol').value.trim().toUpperCase();
  const box=document.getElementById('analysisResult');
  if(!symbol){box.style.display='block';box.innerHTML='<span class="negative">Digite um ticker.</span>';return}
  box.style.display='block';box.innerHTML='Consultando dados...';
  const r=await fetch('/api/analyze/'+encodeURIComponent(symbol));
  const d=await r.json();
  if(!d.ok){box.innerHTML='<span class="negative">'+esc(d.error||'Não foi possível analisar.')+'</span>';return}
  const x=d.data;
  box.innerHTML=`
  <div style="margin-bottom:12px"><b>${esc(x.symbol)}</b> — ${esc(x.name||'Empresa não identificada')}
  <span class="badge">${esc(x.currency||'USD')}</span></div>
  <div class="metrics">
    <div class="metric">Preço atual<b>${usd(x.price)}</b></div>
    <div class="metric">Variação 1D<b class="${x.change_pct>=0?'positive':'negative'}">${pct(x.change_pct)}</b></div>
    <div class="metric">P/L<b>${x.pe===null?'—':Number(x.pe).toFixed(2)}</b></div>
    <div class="metric">Dividend Yield<b>${x.dividend_yield===null?'—':pct(x.dividend_yield)}</b></div>
    <div class="metric">Market Cap<b>${x.market_cap===null?'—':Number(x.market_cap).toLocaleString('en-US')}</b></div>
    <div class="metric">52 semanas<b>${x.low52===null?'—':usd(x.low52)} — ${x.high52===null?'—':usd(x.high52)}</b></div>
  </div>
  <p class="muted" style="margin-bottom:0">${esc(x.comment)}</p>`;
}
loadPortfolio();
</script>
</body>
</html>
"""

def clean_number(value):
    try:
        value = float(value)
        if not math.isfinite(value):
            return None
        return value
    except Exception:
        return None

def brl_rate():
    """USD/BRL rate. Falls back safely if Yahoo is temporarily unavailable."""
    try:
        t = yf.Ticker("USDBRL=X")
        hist = t.history(period="2d", auto_adjust=False)
        if hist is not None and not hist.empty:
            value = clean_number(hist["Close"].dropna().iloc[-1])
            if value and value > 0:
                return value
    except Exception:
        pass
    return 5.50

def get_quote(symbol):
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Informe um ticker.")

    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="5d", auto_adjust=False)

    if hist is None or hist.empty:
        raise ValueError(f"Não encontrei dados para {symbol}. Use um ticker válido, como AAPL ou MSFT.")

    close = hist["Close"].dropna()
    price = clean_number(close.iloc[-1])
    previous = clean_number(close.iloc[-2]) if len(close) >= 2 else price

    if price is None:
        raise ValueError(f"O Yahoo Finance não retornou preço para {symbol}.")

    change_pct = ((price / previous) - 1) * 100 if previous else 0.0

    info = {}
    try:
        info = ticker.info or {}
    except Exception:
        info = {}

    name = info.get("longName") or info.get("shortName") or symbol
    currency = info.get("currency") or "USD"
    pe = clean_number(info.get("trailingPE"))
    div = clean_number(info.get("dividendYield"))
    if div is not None and div < 1:
        div *= 100

    market_cap = clean_number(info.get("marketCap"))
    low52 = clean_number(info.get("fiftyTwoWeekLow"))
    high52 = clean_number(info.get("fiftyTwoWeekHigh"))

    return {
        "symbol": symbol,
        "name": name,
        "currency": currency,
        "price": price,
        "previous": previous,
        "change_pct": change_pct,
        "pe": pe,
        "dividend_yield": div,
        "market_cap": market_cap,
        "low52": low52,
        "high52": high52,
    }

def get_portfolio():
    return session.get("portfolio", [])

def save_portfolio(items):
    session["portfolio"] = items
    session.modified = True

@app.get("/")
def home():
    return render_template_string(HTML)

@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "invest-analyzer-pro"})

@app.get("/api/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"ok": True, "results": []})

    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/search",
            params={"q": q, "quotesCount": 8, "newsCount": 0},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        results = []
        for item in data.get("quotes", []):
            symbol = item.get("symbol")
            if symbol:
                results.append({
                    "symbol": symbol,
                    "name": item.get("longname") or item.get("shortname") or symbol,
                    "exchange": item.get("exchange"),
                    "type": item.get("quoteType"),
                })
        return jsonify({"ok": True, "results": results})
    except Exception as e:
        return jsonify({"ok": False, "error": f"Busca indisponível no momento: {e}"}), 502

@app.get("/api/quote/<symbol>")
def quote(symbol):
    try:
        return jsonify({"ok": True, "data": get_quote(symbol)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.get("/api/analyze/<symbol>")
def analyze(symbol):
    try:
        data = get_quote(symbol)
        pe = data["pe"]
        div = data["dividend_yield"]
        if pe is not None and pe > 0 and pe < 15:
            comment = "P/L relativamente baixo, mas deve ser comparado com o setor e com o crescimento da empresa."
        elif pe is not None and pe > 30:
            comment = "P/L elevado. Isso pode indicar expectativas altas de crescimento; compare com o setor."
        elif div is not None and div >= 3:
            comment = "Dividend Yield relevante. Verifique histórico de dividendos, payout e sustentabilidade."
        else:
            comment = "Use os indicadores como ponto de partida e combine-os com fundamentos e análise de risco."
        data["comment"] = comment
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.get("/api/portfolio")
def portfolio_get():
    items = get_portfolio()
    rate = brl_rate()
    output = []
    invested_brl = 0.0
    market_value_brl = 0.0

    for item in items:
        qty = float(item["quantity"])
        avg = float(item["avg_price"])
        invested_usd = qty * avg
        invested = invested_usd * rate

        try:
            q = get_quote(item["symbol"])
            price = q["price"]
            market_usd = qty * price
            market_brl = market_usd * rate
            profit_usd = market_usd - invested_usd
            profit_brl = profit_usd * rate
        except Exception:
            price = None
            market_brl = invested
            profit_brl = 0.0

        invested_brl += invested
        market_value_brl += market_brl

        output.append({
            "symbol": item["symbol"],
            "quantity": qty,
            "avg_price": avg,
            "price": price,
            "market_value_brl": market_brl,
            "profit_brl": profit_brl,
        })

    profit_brl = market_value_brl - invested_brl
    return jsonify({
        "ok": True,
        "usd_brl": rate,
        "items": output,
        "summary": {
            "invested_brl": invested_brl,
            "market_value_brl": market_value_brl,
            "profit_brl": profit_brl,
            "return_pct": (profit_brl / invested_brl * 100) if invested_brl else 0.0,
        },
    })

@app.post("/api/portfolio")
def portfolio_add():
    data = request.get_json(silent=True) or {}
    symbol = str(data.get("symbol", "")).strip().upper()
    quantity = clean_number(data.get("quantity"))
    avg_price = clean_number(data.get("avg_price"))

    if not symbol:
        return jsonify({"ok": False, "error": "Informe o ticker."}), 400
    if quantity is None or quantity <= 0:
        return jsonify({"ok": False, "error": "Quantidade inválida."}), 400
    if avg_price is None or avg_price < 0:
        return jsonify({"ok": False, "error": "Preço médio inválido."}), 400

    try:
        get_quote(symbol)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    items = get_portfolio()
    items.append({
        "symbol": symbol,
        "quantity": quantity,
        "avg_price": avg_price,
    })
    save_portfolio(items)
    return jsonify({"ok": True, "message": "Ativo adicionado."})

@app.delete("/api/portfolio/<int:index>")
def portfolio_remove(index):
    items = get_portfolio()
    if index < 0 or index >= len(items):
        return jsonify({"ok": False, "error": "Ativo não encontrado."}), 404
    items.pop(index)
    save_portfolio(items)
    return jsonify({"ok": True})

@app.delete("/api/portfolio")
def portfolio_clear():
    save_portfolio([])
    return jsonify({"ok": True})

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "Endpoint não encontrado."}), 404
    return "Página não encontrada.", 404

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "Erro interno do servidor."}), 500
    return "Erro interno do servidor.", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False)
