# ================================================================
# 🚀 INVEST ANALYZER 5.0 — FLASK / RENDER — VERSÃO CORRIGIDA
# ================================================================

from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import math
import os

app = Flask(__name__)
# ✅ CORRIGIDO: Adicionada SECRET_KEY que estava faltando!
app.secret_key = "invest_analyzer_chave_secreta_2026"


# ================================================================
# FUNÇÕES AUXILIARES
# ================================================================

def numero(valor, padrao=0.0):
    try:
        if valor is None:
            return padrao
        valor = str(valor).strip().replace(",", ".")
        if valor == "":
            return padrao
        return float(valor)
    except Exception:
        return padrao


def moeda(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def percentual(valor):
    try:
        return f"{valor:.2f}%".replace(".", ",")
    except Exception:
        return "0,00%"


def seguro(valor, casas=2):
    try:
        valor = float(valor)
        if math.isnan(valor) or math.isinf(valor):
            return 0
        return round(valor, casas)
    except Exception:
        return 0


# ================================================================
# BUSCAR DADOS DO ATIVO
# ================================================================

def buscar_ativo(ticker):
    ticker = ticker.upper().strip()
    
    if not ticker.endswith(".SA"):
        ticker_yahoo = ticker + ".SA"
    else:
        ticker_yahoo = ticker

    resultado = {
        "ticker": ticker.replace(".SA", ""),
        "preco": 0,
        "dividend_yield": 0,
        "pl": 0,
        "pvp": 0,
        "roe": 0,
        "divida": 0,
        "tipo": "Ação/FII",
        "nota": 0,
        "risco": "Indeterminado",
        "conclusao": "Não foi possível obter dados suficientes."
    }

    try:
        ativo = yf.Ticker(ticker_yahoo)
        
        # PREÇO
        preco = 0
        try:
            fast_info = ativo.fast_info
            if hasattr(fast_info, "last_price"):
                preco = fast_info.last_price
        except Exception:
            pass
        
        if not preco:
            try:
                historico = ativo.history(period="5d")
                if not historico.empty:
                    preco = historico["Close"].dropna().iloc[-1]
            except Exception:
                pass
        
        resultado["preco"] = seguro(preco)
        
        # INFORMAÇÕES FUNDAMENTALISTAS
        try:
            info = ativo.info
        except Exception:
            info = {}

        dy = info.get("dividendYield", 0)
        if dy is None: dy = 0
        if dy < 1: dy = dy * 100
        resultado["dividend_yield"] = seguro(dy)

        pl = info.get("trailingPE", 0) or info.get("forwardPE", 0)
        resultado["pl"] = seguro(pl)

        pvp = info.get("priceToBook", 0)
        resultado["pvp"] = seguro(pvp)

        roe = info.get("returnOnEquity", 0)
        if roe < 1: roe = roe * 100
        resultado["roe"] = seguro(roe)

        divida = info.get("debtToEquity", 0)
        resultado["divida"] = seguro(divida)

        # TIPO DE ATIVO
        quote_type = info.get("quoteType", "")
        if quote_type == "ETF":
            resultado["tipo"] = "ETF"
        elif "REIT" in str(quote_type).upper():
            resultado["tipo"] = "FII"
        elif ticker.upper().endswith("11"):
            resultado["tipo"] = "FII"
        else:
            resultado["tipo"] = "Ação"

        # NOTA
        pontos = 0
        criterios = 0
        if resultado["dividend_yield"] > 0:
            criterios += 1
            if resultado["dividend_yield"] >= 8: pontos += 2
            elif resultado["dividend_yield"] >= 5: pontos += 1
        if resultado["pl"] > 0:
            criterios += 1
            if resultado["pl"] <= 10: pontos += 2
            elif resultado["pl"] <= 18: pontos += 1
        if resultado["pvp"] > 0:
            criterios += 1
            if resultado["pvp"] <= 1.2: pontos += 2
            elif resultado["pvp"] <= 2: pontos += 1
        if resultado["roe"] > 0:
            criterios += 1
            if resultado["roe"] >= 20: pontos += 2
            elif resultado["roe"] >= 12: pontos += 1
        if resultado["divida"] >= 0:
            criterios += 1
            if resultado["divida"] <= 50: pontos += 2
            elif resultado["divida"] <= 100: pontos += 1

        nota = (pontos / (criterios * 2)) * 10 if criterios > 0 else 0
        resultado["nota"] = seguro(nota)

        # RISCO
        if resultado["nota"] >= 8:
            resultado["risco"] = "Baixo"
        elif resultado["nota"] >= 6:
            resultado["risco"] = "Moderado"
        elif resultado["nota"] >= 4:
            resultado["risco"] = "Alto"
        else:
            resultado["risco"] = "Muito alto"

        # CONCLUSÃO
        if resultado["nota"] >= 8:
            resultado["conclusao"] = "Favorável. O ativo apresenta indicadores interessantes."
        elif resultado["nota"] >= 6:
            resultado["conclusao"] = "Moderadamente favorável. Merece acompanhamento."
        elif resultado["nota"] >= 4:
            resultado["conclusao"] = "Atenção. Analise com cuidado antes de investir."
        else:
            resultado["conclusao"] = "Desfavorável. Faça uma análise mais aprofundada."

    except Exception as erro:
        print(f"Erro ao consultar {ticker}: {erro}")

    return resultado


# ================================================================
# ROTA PRINCIPAL — PESQUISA INDIVIDUAL
# ================================================================

@app.route("/", methods=["GET", "POST"])
def index():
    dados = None
    erro = None
    ticker = ""

    if request.method == "POST":
        ticker = request.form.get("ticker", "").strip().upper()
        if ticker:
            dados = buscar_ativo(ticker)
            if dados["preco"] == 0:
                erro = "Não foi possível encontrar dados para esse ticker. Verifique o código e tente novamente."
        else:
            erro = "Digite um ticker para pesquisar."

    return render_template(
        "index.html",
        dados=dados,
        ticker=ticker,
        erro=erro
    )


# ================================================================
# EXECUÇÃO
# ================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
