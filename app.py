# ================================================================
# INVEST ANALYZER 5.0 — FLASK / RENDER
# ================================================================
# Aplicação web para análise de ações e FIIs brasileiros.
# Compatível com Render / Gunicorn.
# ================================================================

import io
import math
import os
import time
from datetime import datetime

from flask import Flask, jsonify, request, render_template_string, send_file
import pandas as pd
import yfinance as yf

app = Flask(__name__)

# ----------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------
CACHE = {}
CACHE_SECONDS = 300  # 5 minutos

# Ativos de exemplo para as telas de ações/FIIs
ACOES = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA",
    "WEGE3.SA", "ABEV3.SA", "ELET3.SA", "SUZB3.SA", "PRIO3.SA"
]

FIIS = [
    "MXRF11.SA", "HGLG11.SA", "KNRI11.SA", "XPML11.SA",
    "VISC11.SA", "BTLG11.SA", "XPLG11.SA", "HGRU11.SA"
]

# ----------------------------------------------------------------
# UTILITÁRIOS
# ----------------------------------------------------------------
def normalizar_ticker(ticker):
    ticker = (ticker or "").strip().upper()

    if not ticker:
        return ""

    # Permite o usuário digitar PETR4 ou PETR4.SA
    if not ticker.endswith(".SA"):
        ticker += ".SA"

    return ticker


def numero(valor, casas=2):
    try:
        valor = float(valor)
        if math.isnan(valor) or math.isinf(valor):
            return None
        return round(valor, casas)
    except Exception:
        return None


def cache_get(chave):
    item = CACHE.get(chave)

    if not item:
        return None

    momento, valor = item

    if time.time() - momento > CACHE_SECONDS:
        CACHE.pop(chave, None)
        return None

    return valor


def cache_set(chave, valor):
    CACHE[chave] = (time.time(), valor)


def buscar_yahoo(ticker, periodo="1y", tentativas=3):
    """
    Consulta o Yahoo Finance com algumas tentativas.
    Retorna (ticker_obj, histórico) ou (None, None).
    """
    ticker = normalizar_ticker(ticker)

    if not ticker:
        return None, None

    chave = f"{ticker}:{periodo}"
    cache = cache_get(chave)

    if cache is not None:
        return cache

    ultimo_erro = None

    for tentativa in range(tentativas):
        try:
            ativo = yf.Ticker(ticker)

            historico = ativo.history(
                period=periodo,
                interval="1d",
                auto_adjust=False,
                actions=False,
            )

            if historico is not None and not historico.empty:
                resultado = (ativo, historico)
                cache_set(chave, resultado)
                return resultado

        except Exception as erro:
            ultimo_erro = erro

        time.sleep(1.5 * (tentativa + 1))

    print(f"[YAHOO] Falha em {ticker}: {ultimo_erro}")
    return None, None


def extrair_info(ativo, historico, ticker):
    """Monta indicadores sem quebrar quando algum dado não existir."""
    try:
        fechamento = pd.to_numeric(historico["Close"], errors="coerce").dropna()

        if fechamento.empty:
            return None

        preco = float(fechamento.iloc[-1])

        anterior = float(fechamento.iloc[-2]) if len(fechamento) >= 2 else preco
        variacao_dia = ((preco / anterior) - 1) * 100 if anterior else 0

        fechamento_30 = (
            float(fechamento.iloc[-31])
            if len(fechamento) >= 31
            else float(fechamento.iloc[0])
        )

        variacao_periodo = ((preco / fechamento_30) - 1) * 100 if fechamento_30 else 0

        media_20 = float(fechamento.tail(20).mean())
        media_50 = float(fechamento.tail(50).mean()) if len(fechamento) >= 50 else media_20

        try:
            info = ativo.info or {}
        except Exception as erro:
            print(f"[YAHOO INFO] {ticker}: {erro}")
            info = {}

        def info_num(*nomes):
            for nome in nomes:
                valor = info.get(nome)
                if valor is not None:
                    try:
                        valor = float(valor)
                        if math.isfinite(valor):
                            return valor
                    except Exception:
                        pass
            return None

        market_cap = info_num("marketCap")
        pl = info_num("trailingPE", "forwardPE")
        pvp = info_num("priceToBook")
        dividend_yield = info_num("dividendYield")

        # Yahoo costuma retornar dividendYield como percentual em alguns
        # endpoints e como decimal em outros. Normalizamos para %.
        if dividend_yield is not None and dividend_yield <= 1:
            dividend_yield *= 100

        beta = info_num("beta")
        roe = info_num("returnOnEquity")
        if roe is not None and abs(roe) <= 1:
            roe *= 100

        high_52 = info_num("fiftyTwoWeekHigh")
        low_52 = info_num("fiftyTwoWeekLow")

        if high_52 and low_52 and high_52 != low_52:
            posicao_52 = ((preco - low_52) / (high_52 - low_52)) * 100
        else:
            posicao_52 = None

        # Nota simples de 0 a 10 baseada em indicadores disponíveis.
        pontos = 5.0

        if variacao_periodo > 0:
            pontos += 1
        else:
            pontos -= 1

        if preco >= media_20:
            pontos += 0.8
        else:
            pontos -= 0.8

        if pl is not None:
            if 0 < pl <= 12:
                pontos += 1
            elif pl > 30:
                pontos -= 1

        if pvp is not None:
            if 0 < pvp <= 2:
                pontos += 0.8
            elif pvp > 4:
                pontos -= 0.8

        if dividend_yield is not None and dividend_yield >= 6:
            pontos += 0.8

        if roe is not None and roe >= 15:
            pontos += 0.8

        nota = max(0, min(10, round(pontos, 1)))

        if nota >= 8:
            conclusao = "Muito interessante"
        elif nota >= 6.5:
            conclusao = "Interessante"
        elif nota >= 5:
            conclusao = "Neutro"
        elif nota >= 3.5:
            conclusao = "Atenção"
        else:
            conclusao = "Risco elevado"

        # Volatilidade simples
        retornos = fechamento.pct_change().dropna()
        volatilidade = (
            float(retornos.std() * math.sqrt(252) * 100)
            if not retornos.empty
            else None
        )

        risco = (
            "Baixo" if volatilidade is not None and volatilidade < 20
            else "Moderado" if volatilidade is not None and volatilidade < 35
            else "Alto"
        )

        return {
            "ticker": ticker.replace(".SA", ""),
            "ticker_yahoo": ticker,
            "preco": numero(preco),
            "variacao_dia": numero(variacao_dia),
            "variacao_periodo": numero(variacao_periodo),
            "media_20": numero(media_20),
            "media_50": numero(media_50),
            "pl": numero(pl),
            "pvp": numero(pvp),
            "dividend_yield": numero(dividend_yield),
            "roe": numero(roe),
            "beta": numero(beta),
            "market_cap": numero(market_cap, 0),
            "high_52": numero(high_52),
            "low_52": numero(low_52),
            "posicao_52": numero(posicao_52),
            "volatilidade": numero(volatilidade),
            "risco": risco,
            "nota": nota,
            "conclusao": conclusao,
            "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }

    except Exception as erro:
        print(f"[ANÁLISE] {ticker}: {erro}")
        return None


def analisar(ticker):
    ticker = normalizar_ticker(ticker)

    if not ticker:
        return None, "Informe um ticker."

    ativo, historico = buscar_yahoo(ticker, "1y")

    if historico is None or historico.empty:
        return None, (
            f"Não foi possível carregar os dados de {ticker.replace('.SA', '')}. "
            "O Yahoo Finance pode estar temporariamente indisponível ou ter "
            "limitado a consulta. Tente novamente em alguns segundos."
        )

    dados = extrair_info(ativo, historico, ticker)

    if dados is None:
        return None, "Os dados recebidos estão vazios ou incompletos."

    # Dados para o gráfico
    ultimos = historico.tail(90).copy()
    ultimos["Close"] = pd.to_numeric(ultimos["Close"], errors="coerce")
    ultimos = ultimos.dropna(subset=["Close"])

    dados["grafico"] = [
        {
            "data": idx.strftime("%d/%m"),
            "preco": numero(row["Close"])
        }
        for idx, row in ultimos.iterrows()
    ]

    return dados, None


# ----------------------------------------------------------------
# FRONTEND
# ----------------------------------------------------------------
HTML = r"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Invest Analyzer 5.0</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    background: #0d0f14;
    color: #f3f4f6;
    font-family: Arial, Helvetica, sans-serif;
}

.container {
    width: min(1100px, 94%);
    margin: 0 auto;
    padding: 28px 0 60px;
}

header {
    text-align: center;
    margin-bottom: 28px;
}

h1 {
    font-size: clamp(30px, 7vw, 48px);
    margin: 0 0 8px;
}

.subtitle {
    color: #aeb4c0;
    font-size: 20px;
    line-height: 1.4;
}

.search {
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
    margin-bottom: 20px;
}

input {
    width: 100%;
    background: #191d25;
    border: 1px solid #303744;
    color: white;
    border-radius: 18px;
    padding: 19px 22px;
    font-size: 20px;
    outline: none;
}

input:focus {
    border-color: #3584f4;
}

button {
    border: 0;
    border-radius: 16px;
    padding: 17px 18px;
    color: white;
    background: #202633;
    font-size: 17px;
    font-weight: 700;
    cursor: pointer;
}

button:hover {
    filter: brightness(1.12);
}

.primary {
    background: #2f80ed;
}

.buttons {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 20px;
}

.card {
    background: #181c24;
    border: 1px solid #2d3441;
    border-radius: 20px;
    padding: 20px;
    margin: 14px 0;
}

.card h2 {
    margin-top: 0;
}

.error {
    border-color: #6d2730;
    background: #24171b;
    color: #ffb4bc;
}

.success {
    border-color: #245b3a;
    background: #14251b;
}

.hidden {
    display: none;
}

.grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
}

.metric {
    background: #20252f;
    border-radius: 15px;
    padding: 16px;
}

.metric span {
    display: block;
    color: #aeb4c0;
    font-size: 14px;
    margin-bottom: 8px;
}

.metric strong {
    font-size: 20px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 12px 8px;
    border-bottom: 1px solid #303744;
    text-align: left;
}

th {
    color: #aeb4c0;
}

.small {
    color: #aeb4c0;
    font-size: 14px;
}

.loading {
    text-align: center;
    padding: 25px;
    color: #aeb4c0;
}

canvas {
    max-height: 330px;
}

@media (max-width: 800px) {
    .buttons {
        grid-template-columns: 1fr 1fr;
    }

    .grid {
        grid-template-columns: 1fr 1fr;
    }
}

@media (max-width: 520px) {
    .buttons {
        grid-template-columns: 1fr 1fr;
    }

    .grid {
        grid-template-columns: 1fr 1fr;
    }

    .container {
        width: 94%;
    }
}
</style>
</head>

<body>
<div class="container">

<header>
    <h1>📊 INVEST ANALYZER 5.0</h1>
    <div class="subtitle">
        Ações • FIIs • Indicadores • Nota • Risco • Gráficos • Ranking
    </div>
</header>

<div class="search">
    <input id="ticker" value="PETR4.SA" placeholder="Digite o ativo. Ex.: PETR4 ou PETR4.SA">
    <button class="primary" onclick="analisarAtivo()">📊 Analisar ativo</button>
</div>

<div class="buttons">
    <button onclick="carregarLista('acoes')">📈 Ver ações</button>
    <button onclick="carregarLista('fiis')">🏢 Ver FIIs</button>
    <button onclick="oportunidades()">🔥 Oportunidades</button>
    <button onclick="ranking()">🏆 Ranking</button>
    <button onclick="location.reload()">🔄 Atualizar</button>
    <button onclick="exportar()">📊 Exportar Excel</button>
</div>

<div id="mensagem"></div>
<div id="resultado"></div>

<div class="card small">
⚠️ A Nota, Risco e Conclusão são cálculos automáticos baseados em dados
públicos. Não constituem recomendação personalizada de compra ou venda.
</div>

</div>

<script>
let chart = null;

function mensagem(texto, tipo="error") {
    document.getElementById("mensagem").innerHTML =
        `<div class="card ${tipo}">${texto}</div>`;
}

function limparMensagem() {
    document.getElementById("mensagem").innerHTML = "";
}

function moeda(v) {
    if (v === null || v === undefined) return "N/D";
    return "R$ " + Number(v).toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function pct(v) {
    if (v === null || v === undefined) return "N/D";
    return Number(v).toFixed(2).replace(".", ",") + "%";
}

async function analisarAtivo() {
    const ticker = document.getElementById("ticker").value.trim();

    if (!ticker) {
        mensagem("❌ Digite um ticker.");
        return;
    }

    limparMensagem();
    document.getElementById("resultado").innerHTML =
        '<div class="card loading">⏳ Carregando dados do mercado...</div>';

    try {
        const resposta = await fetch("/api/analisar?ticker=" + encodeURIComponent(ticker));
        const dados = await resposta.json();

        if (!resposta.ok || !dados.ok) {
            throw new Error(dados.erro || "Erro ao carregar mercado.");
        }

        mostrarAnalise(dados.dados);
    } catch (erro) {
        document.getElementById("resultado").innerHTML = "";
        mensagem("❌ " + erro.message);
    }
}

function mostrarAnalise(d) {
    document.getElementById("resultado").innerHTML = `
        <div class="card">
            <h2>📊 ${d.ticker}</h2>
            <div class="grid">
                <div class="metric"><span>Preço atual</span><strong>${moeda(d.preco)}</strong></div>
                <div class="metric"><span>Variação do dia</span><strong>${pct(d.variacao_dia)}</strong></div>
                <div class="metric"><span>Variação 1 ano</span><strong>${pct(d.variacao_periodo)}</strong></div>
                <div class="metric"><span>Nota</span><strong>${d.nota}/10</strong></div>
                <div class="metric"><span>Risco</span><strong>${d.risco}</strong></div>
                <div class="metric"><span>P/L</span><strong>${d.pl ?? "N/D"}</strong></div>
                <div class="metric"><span>P/VP</span><strong>${d.pvp ?? "N/D"}</strong></div>
                <div class="metric"><span>Dividend Yield</span><strong>${d.dividend_yield == null ? "N/D" : pct(d.dividend_yield)}</strong></div>
                <div class="metric"><span>ROE</span><strong>${d.roe == null ? "N/D" : pct(d.roe)}</strong></div>
                <div class="metric"><span>Beta</span><strong>${d.beta ?? "N/D"}</strong></div>
                <div class="metric"><span>Média 20 dias</span><strong>${moeda(d.media_20)}</strong></div>
                <div class="metric"><span>Média 50 dias</span><strong>${moeda(d.media_50)}</strong></div>
            </div>
        </div>

        <div class="card">
            <h2>📈 Gráfico — últimos 90 pregões</h2>
            <canvas id="grafico"></canvas>
        </div>

        <div class="card">
            <h2>🎯 Conclusão automática</h2>
            <p><strong>${d.conclusao}</strong></p>
            <p class="small">
                Última atualização: ${d.ultima_atualizacao}
            </p>
        </div>
    `;

    const ctx = document.getElementById("grafico").getContext("2d");

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: "line",
        data: {
            labels: d.grafico.map(x => x.data),
            datasets: [{
                label: d.ticker,
                data: d.grafico.map(x => x.preco),
                tension: 0.25,
                fill: false
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true }
            }
        }
    });
}

async function carregarLista(tipo) {
    limparMensagem();
    document.getElementById("resultado").innerHTML =
        '<div class="card loading">⏳ Carregando lista...</div>';

    try {
        const resposta = await fetch("/api/lista/" + tipo);
        const dados = await resposta.json();

        if (!dados.ok) throw new Error(dados.erro);

        mostrarTabela(dados.itens, tipo === "fiis" ? "FIIs" : "Ações");
    } catch (erro) {
        mensagem("❌ " + erro.message);
        document.getElementById("resultado").innerHTML = "";
    }
}

function mostrarTabela(itens, titulo) {
    document.getElementById("resultado").innerHTML = `
        <div class="card">
            <h2>📋 ${titulo}</h2>
            <table>
                <thead>
                    <tr>
                        <th>Ativo</th>
                        <th>Preço</th>
                        <th>Dia</th>
                        <th>1 ano</th>
                        <th>Nota</th>
                        <th>Risco</th>
                    </tr>
                </thead>
                <tbody>
                    ${itens.map(x => `
                        <tr>
                            <td><strong>${x.ticker}</strong></td>
                            <td>${moeda(x.preco)}</td>
                            <td>${pct(x.variacao_dia)}</td>
                            <td>${pct(x.variacao_periodo)}</td>
                            <td>${x.nota}/10</td>
                            <td>${x.risco}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        </div>
    `;
}

async function oportunidades() {
    await listaEspecial("/api/oportunidades", "🔥 Oportunidades");
}

async function ranking() {
    await listaEspecial("/api/ranking", "🏆 Ranking");
}

async function listaEspecial(url, titulo) {
    limparMensagem();
    document.getElementById("resultado").innerHTML =
        '<div class="card loading">⏳ Calculando...</div>';

    try {
        const resposta = await fetch(url);
        const dados = await resposta.json();

        if (!dados.ok) throw new Error(dados.erro);

        mostrarTabela(dados.itens, titulo);
    } catch (erro) {
        mensagem("❌ " + erro.message);
        document.getElementById("resultado").innerHTML = "";
    }
}

function exportar() {
    window.location.href = "/exportar";
}

// Analisa PETR4 automaticamente ao abrir.
window.addEventListener("load", () => {
    analisarAtivo();
});
</script>
</body>
</html>
"""


# ----------------------------------------------------------------
# ROTAS
# ----------------------------------------------------------------
@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "app": "Invest Analyzer 5.0"
    })


@app.route("/api/analisar")
def api_analisar():
    ticker = request.args.get("ticker", "")

    dados, erro = analisar(ticker)

    if erro:
        return jsonify({
            "ok": False,
            "erro": erro
        }), 503

    return jsonify({
        "ok": True,
        "dados": dados
    })


def montar_lista(lista):
    itens = []

    for ticker in lista:
        dados, erro = analisar(ticker)

        if dados:
            itens.append(dados)

    return itens


@app.route("/api/lista/acoes")
def lista_acoes():
    itens = montar_lista(ACOES)

    return jsonify({
        "ok": True,
        "itens": itens
    })


@app.route("/api/lista/fiis")
def lista_fiis():
    itens = montar_lista(FIIS)

    return jsonify({
        "ok": True,
        "itens": itens
    })


@app.route("/api/ranking")
def api_ranking():
    itens = montar_lista(ACOES + FIIS)
    itens.sort(key=lambda x: x.get("nota") or 0, reverse=True)

    return jsonify({
        "ok": True,
        "itens": itens
    })


@app.route("/api/oportunidades")
def api_oportunidades():
    itens = montar_lista(ACOES + FIIS)

    # Filtra ativos com nota >= 6
    itens = [x for x in itens if (x.get("nota") or 0) >= 6]
    itens.sort(
        key=lambda x: (
            x.get("nota") or 0,
            x.get("dividend_yield") or 0,
            x.get("variacao_periodo") or -999
        ),
        reverse=True
    )

    return jsonify({
        "ok": True,
        "itens": itens
    })


@app.route("/exportar")
def exportar():
    itens = montar_lista(ACOES + FIIS)

    if not itens:
        return "Não foi possível obter dados para exportação.", 503

    df = pd.DataFrame(itens)

    # Não exporta o gráfico dentro da planilha
    if "grafico" in df.columns:
        df = df.drop(columns=["grafico"])

    arquivo = io.BytesIO()

    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Invest Analyzer")

    arquivo.seek(0)

    return send_file(
        arquivo,
        as_attachment=True,
        download_name="invest_analyzer.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ----------------------------------------------------------------
# EXECUÇÃO LOCAL
# ----------------------------------------------------------------
if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=False)
