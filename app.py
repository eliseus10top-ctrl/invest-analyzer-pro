# ================================================================
# 🚀 INVEST ANALYZER 5.0 — FLASK / RENDER
# ================================================================
# ✔ Compatível com Render
# ✔ Sem Google Colab
# ✔ Sem IPython
# ✔ Cadastro de carteira
# ✔ Quantidade de ativos
# ✔ Preço médio
# ✔ Preço atual via Yahoo Finance
# ✔ Patrimônio total
# ✔ Lucro / prejuízo
# ✔ Dividend Yield
# ✔ P/L
# ✔ P/VP
# ✔ ROE
# ✔ Dívida
# ✔ Nota
# ✔ Risco
# ✔ Conclusão
# ================================================================

from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import math
import os

app = Flask(__name__)


# ================================================================
# FUNÇÕES AUXILIARES
# ================================================================

def numero(valor, padrao=0.0):
    """Converte texto para número com segurança."""
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
    """Formata valor em reais."""
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def percentual(valor):
    """Formata percentual."""
    try:
        return f"{valor:.2f}%".replace(".", ",")
    except Exception:
        return "0,00%"


def seguro(valor, casas=2):
    """Evita NaN/inf vindos do Yahoo Finance."""
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
    """
    Busca informações do ativo utilizando Yahoo Finance.
    """

    ticker = ticker.upper().strip()

    # Permite que o usuário digite PETR4 ou PETR4.SA
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

        # --------------------------------------------------------
        # PREÇO ATUAL
        # --------------------------------------------------------

        preco = 0

        try:
            fast_info = ativo.fast_info

            if hasattr(fast_info, "last_price"):
                preco = fast_info.last_price

        except Exception:
            pass

        # Segunda tentativa
        if not preco:

            try:
                historico = ativo.history(period="5d")

                if not historico.empty:
                    preco = historico["Close"].dropna().iloc[-1]

            except Exception:
                pass

        resultado["preco"] = seguro(preco)

        # --------------------------------------------------------
        # INFORMAÇÕES FUNDAMENTALISTAS
        # --------------------------------------------------------

        try:
            info = ativo.info
        except Exception:
            info = {}

        # Dividend Yield
        dy = info.get("dividendYield", 0)

        if dy is None:
            dy = 0

        # Yahoo normalmente retorna decimal
        if dy < 1:
            dy = dy * 100

        resultado["dividend_yield"] = seguro(dy)

        # P/L
        pl = info.get("trailingPE", 0)

        if pl is None:
            pl = 0

        resultado["pl"] = seguro(pl)

        # P/VP
        pvp = info.get("priceToBook", 0)

        if pvp is None:
            pvp = 0

        resultado["pvp"] = seguro(pvp)

        # ROE
        roe = info.get("returnOnEquity", 0)

        if roe is None:
            roe = 0

        if roe < 1:
            roe = roe * 100

        resultado["roe"] = seguro(roe)

        # Dívida
        divida = info.get("debtToEquity", 0)

        if divida is None:
            divida = 0

        resultado["divida"] = seguro(divida)

        # --------------------------------------------------------
        # IDENTIFICAR TIPO
        # --------------------------------------------------------

        quote_type = info.get("quoteType", "")

        if quote_type == "ETF":
            resultado["tipo"] = "ETF"

        elif "REIT" in str(quote_type).upper():
            resultado["tipo"] = "FII"

        elif ticker.upper().endswith("11"):
            resultado["tipo"] = "FII"

        else:
            resultado["tipo"] = "Ação"

        # --------------------------------------------------------
        # NOTA
        # --------------------------------------------------------

        pontos = 0
        criterios = 0

        # Dividend Yield
        if resultado["dividend_yield"] > 0:
            criterios += 1

            if resultado["dividend_yield"] >= 8:
                pontos += 2
            elif resultado["dividend_yield"] >= 5:
                pontos += 1

        # P/L
        if resultado["pl"] > 0:
            criterios += 1

            if resultado["pl"] <= 10:
                pontos += 2
            elif resultado["pl"] <= 18:
                pontos += 1

        # P/VP
        if resultado["pvp"] > 0:
            criterios += 1

            if resultado["pvp"] <= 1.2:
                pontos += 2
            elif resultado["pvp"] <= 2:
                pontos += 1

        # ROE
        if resultado["roe"] > 0:
            criterios += 1

            if resultado["roe"] >= 20:
                pontos += 2
            elif resultado["roe"] >= 12:
                pontos += 1

        # Dívida
        if resultado["divida"] >= 0:
            criterios += 1

            if resultado["divida"] <= 50:
                pontos += 2
            elif resultado["divida"] <= 100:
                pontos += 1

        # Nota de 0 a 10
        if criterios > 0:
            nota = (pontos / (criterios * 2)) * 10
        else:
            nota = 0

        resultado["nota"] = seguro(nota)

        # --------------------------------------------------------
        # RISCO
        # --------------------------------------------------------

        if resultado["nota"] >= 8:
            resultado["risco"] = "Baixo"

        elif resultado["nota"] >= 6:
            resultado["risco"] = "Moderado"

        elif resultado["nota"] >= 4:
            resultado["risco"] = "Alto"

        else:
            resultado["risco"] = "Muito alto"

        # --------------------------------------------------------
        # CONCLUSÃO
        # --------------------------------------------------------

        if resultado["nota"] >= 8:
            resultado["conclusao"] = (
                "Favorável. O ativo apresenta indicadores interessantes "
                "dentro dos critérios utilizados pelo analisador."
            )

        elif resultado["nota"] >= 6:
            resultado["conclusao"] = (
                "Moderadamente favorável. O ativo apresenta alguns "
                "indicadores positivos, mas merece acompanhamento."
            )

        elif resultado["nota"] >= 4:
            resultado["conclusao"] = (
                "Atenção. Existem indicadores que merecem uma análise "
                "mais cuidadosa antes de investir."
            )

        else:
            resultado["conclusao"] = (
                "Desfavorável pelos critérios atuais. Faça uma análise "
                "mais aprofundada antes de tomar qualquer decisão."
            )

    except Exception as erro:

        print(f"Erro ao consultar {ticker}: {erro}")

    return resultado


# ================================================================
# ANÁLISE DA CARTEIRA
# ================================================================

def analisar_carteira(ativos):
    """
    Recebe os ativos cadastrados e calcula:
    patrimônio, custo, lucro e rentabilidade.
    """

    carteira = []

    patrimonio_total = 0
    custo_total = 0

    for item in ativos:

        ticker = item.get("ticker", "").upper().strip()

        if not ticker:
            continue

        quantidade = numero(item.get("quantidade"))
        preco_medio = numero(item.get("preco_medio"))

        if quantidade <= 0:
            continue

        dados = buscar_ativo(ticker)

        preco_atual = dados["preco"]

        custo = quantidade * preco_medio
        valor_atual = quantidade * preco_atual

        lucro = valor_atual - custo

        if custo > 0:
            rentabilidade = (lucro / custo) * 100
        else:
            rentabilidade = 0

        registro = {
            "ticker": dados["ticker"],
            "quantidade": quantidade,
            "preco_medio": preco_medio,
            "preco_atual": preco_atual,
            "custo": custo,
            "valor_atual": valor_atual,
            "lucro": lucro,
            "rentabilidade": rentabilidade,
            "dividend_yield": dados["dividend_yield"],
            "pl": dados["pl"],
            "pvp": dados["pvp"],
            "roe": dados["roe"],
            "divida": dados["divida"],
            "nota": dados["nota"],
            "risco": dados["risco"],
            "conclusao": dados["conclusao"],
            "tipo": dados["tipo"]
        }

        carteira.append(registro)

        custo_total += custo
        patrimonio_total += valor_atual

    lucro_total = patrimonio_total - custo_total

    if custo_total > 0:
        rentabilidade_total = (lucro_total / custo_total) * 100
    else:
        rentabilidade_total = 0

    return {
        "carteira": carteira,
        "custo_total": custo_total,
        "patrimonio_total": patrimonio_total,
        "lucro_total": lucro_total,
        "rentabilidade_total": rentabilidade_total
    }


# ================================================================
# ROTA PRINCIPAL
# ================================================================

@app.route("/", methods=["GET", "POST"])
def index():

    resultado = None
    erro = None

    if request.method == "POST":

        try:

            tickers = request.form.getlist("ticker[]")
            quantidades = request.form.getlist("quantidade[]")
            precos_medios = request.form.getlist("preco_medio[]")

            ativos = []

            for i in range(len(tickers)):

                ticker = tickers[i].strip()

                quantidade = (
                    quantidades[i]
                    if i < len(quantidades)
                    else "0"
                )

                preco_medio = (
                    precos_medios[i]
                    if i < len(precos_medios)
                    else "0"
                )

                if ticker:

                    ativos.append({
                        "ticker": ticker,
                        "quantidade": quantidade,
                        "preco_medio": preco_medio
                    })

            if not ativos:

                erro = "Adicione pelo menos um ativo."

            else:

                resultado = analisar_carteira(ativos)

        except Exception as e:

            print("Erro:", e)

            erro = (
                "Ocorreu um erro ao processar sua carteira. "
                "Verifique os dados informados."
            )

    return render_template(
        "index.html",
        resultado=resultado,
        erro=erro
    )


# ================================================================
# ROTA PARA PESQUISA INDIVIDUAL
# ================================================================

@app.route("/ativo", methods=["GET", "POST"])
def ativo():

    dados = None
    erro = None
    ticker = ""

    if request.method == "POST":

        ticker = request.form.get("ticker", "").strip().upper()

    else:

        ticker = request.args.get("ticker", "").strip().upper()

    if ticker:

        try:

            dados = buscar_ativo(ticker)

            if dados["preco"] == 0:

                erro = (
                    "Não foi possível encontrar dados para esse ticker."
                )

        except Exception as e:

            print("Erro na análise:", e)

            erro = "Não foi possível analisar o ativo."

    return render_template(
        "index.html",
        resultado=None,
        ativo=dados,
        ticker=ticker,
        erro=erro
    )


# ================================================================
# HEALTH CHECK
# ================================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "app": "INVEST ANALYZER 5.0"
    }


# ================================================================
# EXECUÇÃO
# ================================================================

if __name__ == "__main__":

    # Render fornece a porta através da variável PORT.
    # Localmente, utiliza 5000.

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
