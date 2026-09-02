# ================================================================
# 🚀 INVEST ANALYZER PRO 7.0
# Analisador de Ações e FIIs
# Google Colab - VERSÃO COMPLETA EM UMA ÚNICA CÉLULA
# ================================================================

# ================================================================
# 1. INSTALAÇÃO AUTOMÁTICA
# ================================================================

import sys
import subprocess
import importlib.util
import warnings

warnings.filterwarnings("ignore")


def instalar(pacote):
    try:
        if importlib.util.find_spec(pacote) is None:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-q", pacote]
            )
    except Exception as e:
        print(f"⚠️ Não foi possível instalar {pacote}: {e}")


for pacote in ["yfinance", "ipywidgets", "plotly", "openpyxl"]:
    instalar(pacote)


# ================================================================
# 2. IMPORTAÇÕES
# ================================================================

import yfinance as yf
import pandas as pd
import numpy as np
import ipywidgets as widgets

from IPython.display import display, HTML, clear_output

import plotly.graph_objects as go


# ================================================================
# 3. CONFIGURAÇÃO
# ================================================================

VERSAO = "7.0 PRO"

CACHE = {}
ranking_atual = pd.DataFrame()


# ================================================================
# 4. LISTAS DE ATIVOS
# ================================================================

ACOES = [
    "PETR4.SA",
    "VALE3.SA",
    "ITUB4.SA",
    "BBAS3.SA",
    "BBDC4.SA",
    "WEGE3.SA",
    "ABEV3.SA",
    "EGIE3.SA",
    "TAEE11.SA",
    "BBSE3.SA",
    "ITSA4.SA",
    "CMIG4.SA",
    "CPLE6.SA",
    "VIVT3.SA",
    "SAPR11.SA"
]


FIIS = [
    "MXRF11.SA",
    "HGLG11.SA",
    "KNRI11.SA",
    "BTLG11.SA",
    "TRXF11.SA",
    "XPLG11.SA",
    "VISC11.SA",
    "XPML11.SA",
    "CPTS11.SA",
    "RECR11.SA",
    "HGRU11.SA",
    "MALL11.SA"
]


# ================================================================
# 5. ESTILO
# ================================================================

display(HTML("""
<style>

.ia-title {
    font-size: 30px;
    font-weight: bold;
    margin-top: 10px;
}

.ia-subtitle {
    color: #666;
    font-size: 15px;
    margin-bottom: 20px;
}

.ia-box {
    background: #f7f7f7;
    border: 1px solid #ddd;
    border-radius: 14px;
    padding: 18px;
    margin: 12px 0;
}

.ia-card {
    display: inline-block;
    vertical-align: top;
    background: white;
    border: 1px solid #ddd;
    border-radius: 12px;
    padding: 14px;
    margin: 5px;
    min-width: 135px;
}

.ia-label {
    font-size: 12px;
    color: #666;
}

.ia-value {
    font-size: 20px;
    font-weight: bold;
    margin-top: 5px;
}

.ia-good {
    color: #16833b;
}

.ia-medium {
    color: #b06b00;
}

.ia-bad {
    color: #c62828;
}

.ia-big {
    font-size: 25px;
    font-weight: bold;
}

</style>
"""))


display(HTML(f"""
<div class="ia-title">📊 INVEST ANALYZER PRO {VERSAO}</div>

<div class="ia-subtitle">
Análise automática de ações e FIIs • Indicadores • Risco • Nota • Ranking • Comparação
</div>
"""))


# ================================================================
# 6. FUNÇÕES BÁSICAS
# ================================================================

def numero(valor, padrao=np.nan):

    try:

        if valor is None:
            return padrao

        if isinstance(valor, str):

            valor = (
                valor
                .replace("%", "")
                .replace(",", ".")
                .strip()
            )

        valor = float(valor)

        if np.isfinite(valor):
            return valor

    except Exception:
        pass

    return padrao


def moeda(valor):

    if pd.isna(valor):
        return "N/D"

    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def numero_formatado(valor):

    if pd.isna(valor):
        return "N/D"

    return (
        f"{valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def percentual(valor):

    if pd.isna(valor):
        return "N/D"

    return f"{valor:.2f}%".replace(".", ",")


def ticker_limpo(ticker):

    ticker = str(ticker).upper().strip()

    ticker = ticker.replace(" ", "")

    if not ticker:
        return ""

    if "." not in ticker:
        ticker += ".SA"

    return ticker


def ticker_display(ticker):

    return str(ticker).replace(".SA", "")


# ================================================================
# 7. OBJETO YFINANCE
# ================================================================

def obter_ativo(ticker):

    ticker = ticker_limpo(ticker)

    if ticker not in CACHE:
        CACHE[ticker] = yf.Ticker(ticker)

    return CACHE[ticker]


# ================================================================
# 8. BUSCAR DADOS
# ================================================================

def buscar_dados(ticker):

    try:

        ticker = ticker_limpo(ticker)

        if not ticker:
            return None, {}, pd.DataFrame()

        ativo = obter_ativo(ticker)

        try:
            info = ativo.info
        except Exception:
            info = {}

        try:
            hist = ativo.history(
                period="1y",
                auto_adjust=False
            )
        except Exception:
            hist = pd.DataFrame()

        return ativo, info, hist

    except Exception as erro:

        print("Erro:", erro)

        return None, {}, pd.DataFrame()


# ================================================================
# 9. EXTRAIR INDICADORES
# ================================================================

def extrair_indicadores(ticker, info, hist):

    ticker = ticker_limpo(ticker)

    # ------------------------------------------------------------
    # PREÇO
    # ------------------------------------------------------------

    preco = numero(info.get("currentPrice"))

    if pd.isna(preco):
        preco = numero(info.get("regularMarketPrice"))

    if pd.isna(preco) and hist is not None and not hist.empty:

        try:
            preco = numero(
                hist["Close"].dropna().iloc[-1]
            )
        except Exception:
            pass


    # ------------------------------------------------------------
    # DIVIDEND YIELD
    # ------------------------------------------------------------

    dy = numero(info.get("dividendYield"))

    if not pd.isna(dy):

        if dy < 1:
            dy *= 100


    # ------------------------------------------------------------
    # P/L
    # ------------------------------------------------------------

    pl = numero(info.get("trailingPE"))

    if pd.isna(pl):
        pl = numero(info.get("forwardPE"))


    # ------------------------------------------------------------
    # P/VP
    # ------------------------------------------------------------

    pvp = numero(info.get("priceToBook"))


    # ------------------------------------------------------------
    # ROE
    # ------------------------------------------------------------

    roe = numero(info.get("returnOnEquity"))

    if not pd.isna(roe) and abs(roe) <= 1:
        roe *= 100


    # ------------------------------------------------------------
    # DÍVIDA
    # ------------------------------------------------------------

    divida = numero(info.get("debtToEquity"))


    # ------------------------------------------------------------
    # MARGEM
    # ------------------------------------------------------------

    margem = numero(info.get("profitMargins"))

    if not pd.isna(margem) and abs(margem) <= 1:
        margem *= 100


    # ------------------------------------------------------------
    # CRESCIMENTO
    # ------------------------------------------------------------

    crescimento = numero(info.get("revenueGrowth"))

    if not pd.isna(crescimento) and abs(crescimento) <= 1:
        crescimento *= 100


    # ------------------------------------------------------------
    # BETA
    # ------------------------------------------------------------

    beta = numero(info.get("beta"))


    # ------------------------------------------------------------
    # ROIC / RETORNO
    # ------------------------------------------------------------

    roic = numero(info.get("returnOnAssets"))

    if not pd.isna(roic) and abs(roic) <= 1:
        roic *= 100


    # ------------------------------------------------------------
    # MARKET CAP
    # ------------------------------------------------------------

    market_cap = numero(info.get("marketCap"))


    # ------------------------------------------------------------
    # NOME
    # ------------------------------------------------------------

    nome = (
        info.get("longName")
        or info.get("shortName")
        or ticker
    )


    setor = info.get("sector") or "N/D"

    industria = info.get("industry") or "N/D"


    return {

        "ticker": ticker,

        "nome": nome,

        "setor": setor,

        "industria": industria,

        "preco": preco,

        "dividend_yield": dy,

        "pl": pl,

        "pvp": pvp,

        "roe": roe,

        "divida": divida,

        "margem": margem,

        "crescimento": crescimento,

        "beta": beta,

        "roa": roic,

        "market_cap": market_cap
    }


# ================================================================
# 10. PONTUAÇÃO - DIVIDENDOS
# ================================================================

def nota_dividendos(dy):

    if pd.isna(dy):
        return np.nan

    if dy >= 10:
        return 10

    if dy >= 8:
        return 9.5

    if dy >= 6:
        return 8.5

    if dy >= 4:
        return 7

    if dy >= 2:
        return 5

    return 3


# ================================================================
# 11. PONTUAÇÃO - ROE
# ================================================================

def nota_roe(roe):

    if pd.isna(roe):
        return np.nan

    if roe >= 25:
        return 10

    if roe >= 20:
        return 9

    if roe >= 15:
        return 8

    if roe >= 10:
        return 6

    if roe >= 5:
        return 4

    return 2


# ================================================================
# 12. PONTUAÇÃO - P/L
# ================================================================

def nota_pl(pl):

    if pd.isna(pl) or pl <= 0:
        return np.nan

    if pl <= 8:
        return 10

    if pl <= 12:
        return 9

    if pl <= 16:
        return 8

    if pl <= 22:
        return 6

    if pl <= 30:
        return 4

    return 2


# ================================================================
# 13. PONTUAÇÃO - P/VP
# ================================================================

def nota_pvp(pvp):

    if pd.isna(pvp) or pvp <= 0:
        return np.nan

    if pvp <= 0.8:
        return 10

    if pvp <= 1.0:
        return 9

    if pvp <= 1.2:
        return 8

    if pvp <= 1.5:
        return 6

    if pvp <= 2:
        return 4

    return 2


# ================================================================
# 14. PONTUAÇÃO - DÍVIDA
# ================================================================

def nota_divida(divida):

    if pd.isna(divida):
        return np.nan

    if divida <= 30:
        return 10

    if divida <= 60:
        return 8.5

    if divida <= 100:
        return 7

    if divida <= 150:
        return 5

    return 2


# ================================================================
# 15. PONTUAÇÃO - CRESCIMENTO
# ================================================================

def nota_crescimento(crescimento):

    if pd.isna(crescimento):
        return np.nan

    if crescimento >= 20:
        return 10

    if crescimento >= 10:
        return 8.5

    if crescimento >= 5:
        return 7

    if crescimento >= 0:
        return 5

    return 2


# ================================================================
# 16. NOTA FINAL
# ================================================================

def calcular_nota_completa(d):

    notas = []

    pesos = []

    # Dividendos
    n = nota_dividendos(d["dividend_yield"])

    if not pd.isna(n):
        notas.append(n)
        pesos.append(1.5)

    # ROE
    n = nota_roe(d["roe"])

    if not pd.isna(n):
        notas.append(n)
        pesos.append(1.5)

    # P/L
    n = nota_pl(d["pl"])

    if not pd.isna(n):
        notas.append(n)
        pesos.append(1.2)

    # P/VP
    n = nota_pvp(d["pvp"])

    if not pd.isna(n):
        notas.append(n)
        pesos.append(1.2)

    # Dívida
    n = nota_divida(d["divida"])

    if not pd.isna(n):
        notas.append(n)
        pesos.append(1.2)

    # Crescimento
    n = nota_crescimento(d["crescimento"])

    if not pd.isna(n):
        notas.append(n)
        pesos.append(1.2)

    if not notas:
        return 0

    nota = np.average(
        notas,
        weights=pesos
    )

    return round(
        max(0, min(10, nota)),
        1
    )


# ================================================================
# 17. ANÁLISE DE RISCO
# ================================================================

def calcular_risco(d):

    pontos = 0

    beta = d["beta"]
    divida = d["divida"]
    pl = d["pl"]
    crescimento = d["crescimento"]


    # Beta

    if not pd.isna(beta):

        if beta >= 1.6:
            pontos += 3

        elif beta >= 1.2:
            pontos += 2

        elif beta >= 0.9:
            pontos += 1


    # Dívida

    if not pd.isna(divida):

        if divida > 150:
            pontos += 3

        elif divida > 100:
            pontos += 2

        elif divida > 60:
            pontos += 1


    # P/L negativo

    if not pd.isna(pl):

        if pl < 0:
            pontos += 2


    # Crescimento negativo

    if not pd.isna(crescimento):

        if crescimento < -10:
            pontos += 2

        elif crescimento < 0:
            pontos += 1


    if pontos >= 6:
        return "ALTO"

    if pontos >= 3:
        return "MÉDIO"

    return "BAIXO"


# ================================================================
# 18. CONCLUSÃO
# ================================================================

def conclusao(nota, risco):

    if nota >= 8.5 and risco == "BAIXO":
        return "MUITO FAVORÁVEL"

    if nota >= 7.5 and risco != "ALTO":
        return "FAVORÁVEL"

    if nota >= 6:
        return "ATENÇÃO / ANALISAR"

    if nota >= 4:
        return "NEUTRO"

    return "DESFAVORÁVEL"


# ================================================================
# 19. ANÁLISE COMPLETA
# ================================================================

def analisar_ativo(ticker):

    ativo, info, hist = buscar_dados(ticker)

    if ativo is None:
        return None

    if not info:
        return None

    d = extrair_indicadores(
        ticker,
        info,
        hist
    )

    d["nota"] = calcular_nota_completa(d)

    d["risco"] = calcular_risco(d)

    d["conclusao"] = conclusao(
        d["nota"],
        d["risco"]
    )

    return d


# ================================================================
# 20. CARD HTML
# ================================================================

def card(titulo, valor, classe=""):

    return f"""
    <div class="ia-card">

        <div class="ia-label">
            {titulo}
        </div>

        <div class="ia-value {classe}">
            {valor}
        </div>

    </div>
    """


# ================================================================
# 21. CLASSE DA NOTA
# ================================================================

def classe_nota(nota):

    if nota >= 7.5:
        return "ia-good"

    if nota >= 5:
        return "ia-medium"

    return "ia-bad"


# ================================================================
# 22. CLASSE DO RISCO
# ================================================================

def classe_risco(risco):

    if risco == "BAIXO":
        return "ia-good"

    if risco == "MÉDIO":
        return "ia-medium"

    return "ia-bad"


# ================================================================
# 23. MOSTRAR FICHA COMPLETA
# ================================================================

def mostrar_ficha(ticker):

    ticker = ticker_limpo(ticker)

    with saida:

        clear_output(wait=True)

        print(
            f"🔎 Analisando {ticker_display(ticker)}..."
        )

        d = analisar_ativo(ticker)

        if d is None:

            display(HTML("""
            <div class="ia-box">

            <h2>❌ Ativo não encontrado</h2>

            <p>
            Não foi possível obter os dados desse ticker.
            </p>

            <p>
            Exemplos:
            PETR4 • VALE3 • ITUB4 • MXRF11 • BTLG11
            </p>

            </div>
            """))

            return


        nota = d["nota"]

        classe_n = classe_nota(nota)

        classe_r = classe_risco(d["risco"])


        # --------------------------------------------------------
        # FICHA
        # --------------------------------------------------------

        html = f"""

        <div class="ia-box">

        <h2>
        📋 {d["nome"]}
        </h2>

        <p>
        <b>Ticker:</b>
        {ticker_display(d["ticker"])}
        </p>

        <p>
        <b>Setor:</b>
        {d["setor"]}
        </p>

        <p>
        <b>Indústria:</b>
        {d["industria"]}
        </p>

        <hr>

        {card(
            "💰 Preço",
            moeda(d["preco"])
        )}

        {card(
            "💵 Dividend Yield",
            percentual(d["dividend_yield"])
        )}

        {card(
            "⭐ Nota",
            f'{nota}/10',
            classe_n
        )}

        {card(
            "⚠️ Risco",
            d["risco"],
            classe_r
        )}

        <br>

        {card(
            "P/L",
            numero_formatado(d["pl"])
        )}

        {card(
            "P/VP",
            numero_formatado(d["pvp"])
        )}

        {card(
            "ROE",
            percentual(d["roe"])
        )}

        {card(
            "Dívida/PL",
            numero_formatado(d["divida"])
        )}

        <br>

        {card(
            "Margem",
            percentual(d["margem"])
        )}

        {card(
            "Crescimento",
            percentual(d["crescimento"])
        )}

        {card(
            "Beta",
            numero_formatado(d["beta"])
        )}

        {card(
            "ROA",
            percentual(d["roa"])
        )}

        <hr>

        <h2>
        📌 CONCLUSÃO:
        <span class="{classe_n}">
        {d["conclusao"]}
        </span>
        </h2>

        </div>

        """


        display(HTML(html))


        # --------------------------------------------------------
        # GRÁFICO
        # --------------------------------------------------------

        try:

            ativo = obter_ativo(ticker)

            hist = ativo.history(
                period="1y",
                auto_adjust=False
            )

            if hist is not None and not hist.empty:

                fig = go.Figure()

                fig.add_trace(
                    go.Scatter(
                        x=hist.index,
                        y=hist["Close"],
                        mode="lines",
                        name=ticker_display(ticker)
                    )
                )

                fig.update_layout(
                    title=f"📈 Evolução - {ticker_display(ticker)} - 1 ano",
                    xaxis_title="Data",
                    yaxis_title="Preço",
                    height=450
                )

                fig.show()

        except Exception as erro:

            print(
                "⚠️ Gráfico indisponível:",
                erro
            )


# ================================================================
# 24. CRIAR RANKING
# ================================================================

def criar_ranking(lista):

    resultados = []

    for ticker in lista:

        try:

            d = analisar_ativo(ticker)

            if d is not None:

                resultados.append({

                    "Ticker":
                        ticker_display(d["ticker"]),

                    "Preço":
                        d["preco"],

                    "Dividend Yield":
                        d["dividend_yield"],

                    "P/L":
                        d["pl"],

                    "P/VP":
                        d["pvp"],

                    "ROE":
                        d["roe"],

                    "Dívida/PL":
                        d["divida"],

                    "Crescimento":
                        d["crescimento"],

                    "Nota":
                        d["nota"],

                    "Risco":
                        d["risco"],

                    "Conclusão":
                        d["conclusao"]
                })

        except Exception:
            continue


    if not resultados:
        return pd.DataFrame()


    df = pd.DataFrame(resultados)

    df = df.sort_values(
        "Nota",
        ascending=False,
        na_position="last"
    )

    return df.reset_index(drop=True)


# ================================================================
# 25. FORMATAR RANKING
# ================================================================

def formatar_ranking(df):

    return (
        df.style
        .format({

            "Preço":
                lambda x: moeda(x),

            "Dividend Yield":
                lambda x: percentual(x),

            "P/L":
                lambda x: numero_formatado(x),

            "P/VP":
                lambda x: numero_formatado(x),

            "ROE":
                lambda x: percentual(x),

            "Dívida/PL":
                lambda x: numero_formatado(x),

            "Crescimento":
                lambda x: percentual(x),

            "Nota":
                lambda x: f"{x:.1f}"

        })
    )


# ================================================================
# 26. VER AÇÕES
# ================================================================

def mostrar_acoes(_):

    global ranking_atual

    with saida:

        clear_output(wait=True)

        print("⏳ Analisando ações...")

        ranking_atual = criar_ranking(ACOES)

        if ranking_atual.empty:

            print("❌ Não foi possível criar o ranking.")

            return


        display(
            HTML("""
            <div class="ia-box">
            <h2>🏆 RANKING DE AÇÕES</h2>
            <p>
            Ordenado automaticamente pela nota do INVEST ANALYZER PRO.
            </p>
            </div>
            """)
        )

        display(
            formatar_ranking(
                ranking_atual
            )
        )


# ================================================================
# 27. VER FIIs
# ================================================================

def mostrar_fiis(_):

    global ranking_atual

    with saida:

        clear_output(wait=True)

        print("⏳ Analisando FIIs...")

        ranking_atual = criar_ranking(FIIS)

        if ranking_atual.empty:

            print("❌ Não foi possível criar o ranking.")

            return


        display(
            HTML("""
            <div class="ia-box">
            <h2>🏢 RANKING DE FIIs</h2>
            <p>
            Ranking baseado nos indicadores disponíveis.
            </p>
            </div>
            """)
        )

        display(
            formatar_ranking(
                ranking_atual
            )
        )


# ================================================================
# 28. OPORTUNIDADES
# ================================================================

def mostrar_oportunidades(_):

    global ranking_atual

    with saida:

        clear_output(wait=True)

        print("⏳ Procurando oportunidades...")

        lista = ACOES + FIIS

        df = criar_ranking(lista)

        if df.empty:

            print("❌ Nenhum dado encontrado.")

            return


        oportunidades = df[
            (df["Nota"] >= 7.5) &
            (df["Risco"] != "ALTO")
        ].copy()


        display(
            HTML("""
            <div class="ia-box">

            <h2>⭐ POSSÍVEIS OPORTUNIDADES</h2>

            <p>
            Ativos que atingiram os critérios automáticos
            de nota e risco do sistema.
            </p>

            </div>
            """)
        )


        if oportunidades.empty:

            display(
                HTML("""
                <div class="ia-box">

                <h3>🔎 Nenhum ativo atingiu os critérios.</h3>

                <p>
                Isso não significa que não existam oportunidades.
                Significa apenas que nenhum ativo da lista
                atingiu os filtros atuais.
                </p>

                </div>
                """)
            )

        else:

            ranking_atual = oportunidades

            display(
                formatar_ranking(
                    oportunidades
                )
            )


# ================================================================
# 29. TOP 5
# ================================================================

def mostrar_top5(_):

    global ranking_atual

    with saida:

        clear_output(wait=True)

        print("⏳ Calculando TOP 5...")

        df = criar_ranking(
            ACOES + FIIS
        )

        if df.empty:

            print("❌ Sem dados.")

            return


        ranking_atual = df.head(5).copy()


        html = """
        <div class="ia-box">

        <h2>🏆 TOP 5 INVEST ANALYZER PRO</h2>

        """

        for i, row in ranking_atual.iterrows():

            posicao = i + 1

            html += f"""

            <div class="ia-card">

            <div class="ia-label">
            {posicao}º LUGAR
            </div>

            <div class="ia-value">
            {row["Ticker"]}
            </div>

            <div>
            ⭐ Nota: {row["Nota"]:.1f}/10
            </div>

            <div>
            ⚠️ Risco: {row["Risco"]}
            </div>

            </div>

            """

        html += "</div>"

        display(
            HTML(html)
        )

        display(
            formatar_ranking(
                ranking_atual
            )
        )


# ================================================================
# 30. COMPARAR ATIVOS
# ================================================================

def comparar_ativos(ativos):

    lista = []

    for ticker in ativos:

        try:

            d = analisar_ativo(ticker)

            if d is not None:

                lista.append(d)

        except Exception:
            continue


    if not lista:

        return pd.DataFrame()


    comparacao = []


    for d in lista:

        comparacao.append({

            "Ticker":
                ticker_display(d["ticker"]),

            "Preço":
                d["preco"],

            "DY":
                d["dividend_yield"],

            "P/L":
                d["pl"],

            "P/VP":
                d["pvp"],

            "ROE":
                d["roe"],

            "Dívida/PL":
                d["divida"],

            "Crescimento":
                d["crescimento"],

            "Nota":
                d["nota"],

            "Risco":
                d["risco"]

        })


    return pd.DataFrame(comparacao)


# ================================================================
# 31. MOSTRAR COMPARAÇÃO
# ================================================================

def mostrar_comparacao(_):

    with saida:

        clear_output(wait=True)

        texto = campo_comparacao.value.strip()

        if not texto:

            print(
                "⚠️ Digite pelo menos dois tickers."
            )

            return


        tickers = [
            ticker_limpo(x)
            for x in texto.split(",")
            if x.strip()
        ]


        if len(tickers) < 2:

            print(
                "⚠️ Digite pelo menos dois ativos separados por vírgula."
            )

            return


        print("⏳ Comparando ativos...")

        df = comparar_ativos(tickers)


        if df.empty:

            print(
                "❌ Não foi possível comparar os ativos."
            )

            return


        display(
            HTML("""
            <div class="ia-box">

            <h2>⚖️ COMPARAÇÃO DE ATIVOS</h2>

            </div>
            """)
        )


        display(
            df.style
            .format({

                "Preço":
                    lambda x: moeda(x),

                "DY":
                    lambda x: percentual(x),

                "P/L":
                    lambda x: numero_formatado(x),

                "P/VP":
                    lambda x: numero_formatado(x),

                "ROE":
                    lambda x: percentual(x),

                "Dívida/PL":
                    lambda x: numero_formatado(x),

                "Crescimento":
                    lambda x: percentual(x),

                "Nota":
                    lambda x: f"{x:.1f}"

            })
        )


        # Melhor nota

        melhor = df.sort_values(
            "Nota",
            ascending=False
        ).iloc[0]


        display(
            HTML(f"""
            <div class="ia-box">

            <h3>
            🏆 Melhor nota da comparação:
            {melhor["Ticker"]}
            </h3>

            <p>
            ⭐ Nota:
            <b>{melhor["Nota"]:.1f}/10</b>
            </p>

            <p>
            ⚠️ Risco:
            <b>{melhor["Risco"]}</b>
            </p>

            </div>
            """)
        )


# ================================================================
# 32. ATUALIZAR
# ================================================================

def atualizar(_):

    with saida:

        clear_output(wait=True)

        CACHE.clear()

        display(
            HTML("""
            <div class="ia-box">

            <h2>🔄 Dados atualizados!</h2>

            <p>
            O cache foi limpo.
            Faça uma nova análise ou ranking.
            </p>

            </div>
            """)
        )


# ================================================================
# 33. EXPORTAR CSV
# ================================================================

def exportar_csv(_):

    with saida:

        clear_output(wait=True)

        if ranking_atual.empty:

            print(
                "⚠️ Primeiro gere um ranking."
            )

            return


        arquivo = "invest_analyzer_pro_7_ranking.csv"

        ranking_atual.to_csv(
            arquivo,
            index=False,
            encoding="utf-8-sig"
        )


        display(
            HTML(f"""
            <div class="ia-box">

            <h2>✅ CSV criado</h2>

            <p>
            Arquivo:
            <b>{arquivo}</b>
            </p>

            </div>
            """)
        )


# ================================================================
# 34. EXPORTAR EXCEL
# ================================================================

def exportar_excel(_):

    with saida:

        clear_output(wait=True)

        if ranking_atual.empty:

            print(
                "⚠️ Primeiro gere um ranking."
            )

            return


        arquivo = "invest_analyzer_pro_7_ranking.xlsx"

        ranking_atual.to_excel(
            arquivo,
            index=False
        )


        display(
            HTML(f"""
            <div class="ia-box">

            <h2>✅ Excel criado</h2>

            <p>
            Arquivo:
            <b>{arquivo}</b>
            </p>

            </div>
            """)
        )


# ================================================================
# 35. PESQUISA
# ================================================================

campo_ticker = widgets.Text(
    value="PETR4",
    placeholder="Ex.: PETR4",
    description="Ticker:",
    layout=widgets.Layout(
        width="340px"
    )
)


botao_analisar = widgets.Button(
    description="🔎 ANALISAR",
    button_style="primary",
    layout=widgets.Layout(
        width="130px"
    )
)


# ================================================================
# 36. COMPARAÇÃO
# ================================================================

campo_comparacao = widgets.Text(
    value="PETR4,VALE3,ITUB4",
    placeholder="PETR4,VALE3,ITUB4",
    description="Comparar:",
    layout=widgets.Layout(
        width="430px"
    )
)


botao_comparar = widgets.Button(
    description="⚖️ COMPARAR",
    button_style="primary",
    layout=widgets.Layout(
        width="140px"
    )
)


# ================================================================
# 37. BOTÕES
# ================================================================

botao_atualizar = widgets.Button(
    description="🔄 Atualizar",
    layout=widgets.Layout(
        width="125px"
    )
)


botao_acoes = widgets.Button(
    description="📈 Ver Ações",
    layout=widgets.Layout(
        width="130px"
    )
)


botao_fiis = widgets.Button(
    description="🏢 Ver FIIs",
    layout=widgets.Layout(
        width="130px"
    )
)


botao_oportunidades = widgets.Button(
    description="⭐ Oportunidades",
    layout=widgets.Layout(
        width="155px"
    )
)


botao_top5 = widgets.Button(
    description="🏆 TOP 5",
    layout=widgets.Layout(
        width="110px"
    )
)


botao_csv = widgets.Button(
    description="📄 CSV",
    layout=widgets.Layout(
        width="100px"
    )
)


botao_excel = widgets.Button(
    description="📊 Excel",
    layout=widgets.Layout(
        width="110px"
    )
)


# ================================================================
# 38. ÁREA DE SAÍDA
# ================================================================

saida = widgets.Output()


# ================================================================
# 39. EVENTOS
# ================================================================

def evento_analisar(_):

    mostrar_ficha(
        campo_ticker.value
    )


botao_analisar.on_click(
    evento_analisar
)


botao_atualizar.on_click(
    atualizar
)


botao_acoes.on_click(
    mostrar_acoes
)


botao_fiis.on_click(
    mostrar_fiis
)


botao_oportunidades.on_click(
    mostrar_oportunidades
)


botao_top5.on_click(
    mostrar_top5
)


botao_comparar.on_click(
    mostrar_comparacao
)


botao_csv.on_click(
    exportar_csv
)


botao_excel.on_click(
    exportar_excel
)


# ================================================================
# 40. DASHBOARD
# ================================================================

display(
    widgets.HBox([
        campo_ticker,
        botao_analisar
    ])
)


display(
    widgets.HBox([
        campo_comparacao,
        botao_comparar
    ])
)


display(
    widgets.HBox([
        botao_atualizar,
        botao_acoes,
        botao_fiis,
        botao_oportunidades
    ])
)


display(
    widgets.HBox([
        botao_top5,
        botao_csv,
        botao_excel
    ])
)


display(
    saida
)


# ================================================================
# 41. MENSAGEM INICIAL
# ================================================================

with saida:

    display(
        HTML("""
        <div class="ia-box">

        <h2>🚀 INVEST ANALYZER PRO 7.0 ONLINE</h2>

        <p>
        Seu painel está pronto.
        </p>

        <hr>

        <h3>🔎 Pesquisa individual</h3>

        <p>
        Digite um ticker:
        <b>PETR4</b>,
        <b>VALE3</b>,
        <b>ITUB4</b>,
        <b>MXRF11</b>,
        <b>BTLG11</b>
        </p>

        <h3>⚖️ Comparação</h3>

        <p>
        Digite:
        <b>PETR4,VALE3,ITUB4</b>
        </p>

        <h3>📊 O PRO 7.0 possui</h3>

        <ul>

        <li>🔎 Pesquisa por ticker</li>

        <li>📋 Ficha completa</li>

        <li>💰 Preço</li>

        <li>💵 Dividend Yield</li>

        <li>📊 P/L</li>

        <li>📊 P/VP</li>

        <li>📈 ROE</li>

        <li>💳 Dívida/PL</li>

        <li>📈 Crescimento</li>

        <li>📊 Margem</li>

        <li>📉 Beta</li>

        <li>⭐ Nota automática de 0 a 10</li>

        <li>⚠️ Classificação de risco</li>

        <li>📌 Conclusão automática</li>

        <li>📈 Gráfico de 1 ano</li>

        <li>🏆 Ranking de ações</li>

        <li>🏢 Ranking de FIIs</li>

        <li>⭐ Possíveis oportunidades</li>

        <li>🏆 TOP 5</li>

        <li>⚖️ Comparação entre ativos</li>

        <li>📄 Exportação CSV</li>

        <li>📊 Exportação Excel</li>

        <li>🔄 Atualização dos dados</li>

        </ul>

        <hr>

        <p>
        ⚠️ <b>Importante:</b>
        a nota e os sinais são critérios automáticos
        para auxiliar na análise. Não constituem recomendação
        personalizada nem garantia de rentabilidade.
        </p>

        </div>
        """)
    )


print("=" * 60)
print("🚀 INVEST ANALYZER PRO 7.0")
print("✅ SISTEMA CARREGADO COM SUCESSO")
print("✅ DASHBOARD ONLINE")
print("✅ PESQUISA POR TICKER")
print("✅ RANKING")
print("✅ COMPARAÇÃO")
print("✅ ANÁLISE DE RISCO")
print("✅ NOTA AUTOMÁTICA")
print("=" * 60)
