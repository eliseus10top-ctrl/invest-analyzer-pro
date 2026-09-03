# ================================================================
# 🚀 INVEST ANALYZER 5.0 — CARTEIRA REAL INTELIGENTE
# ================================================================
#
# ✔ Cadastro da carteira real
# ✔ Quantidade de ativos
# ✔ Preço médio
# ✔ Preço atual via Yahoo Finance
# ✔ Patriimônio total
# ✔ Lucro/prejuízo estimado
# ✔ Dividend Yield
# ✔ Score 0–100
# ✔ Risco
# ✔ Distribuição atual
# ✔ Distribuição ideal
# ✔ Rebalanceamento
# ✔ Próximo aporte inteligente
# ✔ Ranking
# ✔ Pesquisa por ticker
# ✔ Simulação
# ✔ Gráficos
# ✔ Exportação CSV
#
# ================================================================

!pip -q install -U yfinance pandas numpy matplotlib ipywidgets

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as widgets

from IPython.display import display, HTML, clear_output
import warnings
import os
import math

warnings.filterwarnings("ignore")

# ================================================================
# GOOGLE COLAB
# ================================================================

try:
    from google.colab import output
    output.enable_custom_widget_manager()
except:
    pass

# ================================================================
# CONFIGURAÇÕES
# ================================================================

CACHE = {}

CARTEIRA = pd.DataFrame(
    columns=[
        "Ticker",
        "Tipo",
        "Quantidade",
        "Preço Médio"
    ]
)

ULTIMO_RANKING = pd.DataFrame()
ULTIMA_ANALISE = None
ULTIMA_SUGESTAO = pd.DataFrame()

# ================================================================
# LISTAS
# ================================================================

ACOES = [
    "PETR4","VALE3","ITUB4","BBAS3","BBDC4","ABEV3",
    "WEGE3","PRIO3","SUZB3","JBSS3","ELET3","ELET6",
    "RENT3","RADL3","EQTL3","VIVT3","CPLE6","CMIG4",
    "TIMS3","SANB11","BBSE3","TAEE11","EGIE3","FLRY3",
    "GGBR4","USIM5","EMBR3","LREN3","CSAN3","B3SA3"
]

FIIS = [
    "MXRF11","BTLG11","HGLG11","KNRI11","XPML11",
    "VISC11","XPLG11","HGRU11","TRXF11","CPTS11",
    "KNCR11","RECR11","VGIR11","RBRF11","BCFF11",
    "MALL11","HSML11","HGRE11","PVBI11","JSRE11"
]

TODOS = ACOES + FIIS

# ================================================================
# FUNÇÕES BÁSICAS
# ================================================================

def norm(ticker):

    return str(ticker).upper().strip().replace(".SA","")


def identificar_tipo(ticker):

    ticker = norm(ticker)

    if ticker in FIIS:
        return "FII"

    return "AÇÃO"


def numero(x):

    try:

        if x is None:
            return np.nan

        return float(x)

    except:

        return np.nan


def dinheiro(x):

    if pd.isna(x):
        return "N/D"

    return (
        f"R$ {x:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X",".")
    )


def percentual(x):

    if pd.isna(x):
        return "N/D"

    return f"{x:.2f}%".replace(".",",")


def decimal(x):

    if pd.isna(x):
        return "N/D"

    return f"{x:.2f}".replace(".",",")


def obter_info(info,*chaves):

    for chave in chaves:

        try:

            valor = info.get(chave,np.nan)

            if valor is not None and not pd.isna(valor):

                return valor

        except:

            pass

    return np.nan


# ================================================================
# SCORE
# ================================================================

def score_linear(valor,minimo,maximo):

    if pd.isna(valor):
        return np.nan

    return max(
        0,
        min(
            100,
            (valor-minimo) /
            (maximo-minimo) *
            100
        )
    )


def classificacao(score):

    if pd.isna(score):
        return "⚪ SEM DADOS"

    if score >= 85:
        return "🟢 EXCELENTE"

    if score >= 75:
        return "🟢 MUITO BOM"

    if score >= 65:
        return "🟡 BOM"

    if score >= 50:
        return "🟠 REGULAR"

    return "🔴 FRACO"


def risco_por_score(score):

    if pd.isna(score):
        return "N/D"

    if score >= 80:
        return "BAIXO"

    if score >= 65:
        return "MÉDIO"

    return "ALTO"


# ================================================================
# CRESCIMENTO
# ================================================================

def crescimento(fin, nome):

    try:

        if fin is None or fin.empty:
            return np.nan

        linha = None

        for indice in fin.index:

            if nome.lower() in str(indice).lower():

                linha = fin.loc[indice]

                break

        if linha is None:
            return np.nan

        valores = pd.to_numeric(
            linha,
            errors="coerce"
        ).dropna()

        if len(valores) < 2:
            return np.nan

        valores = valores.sort_index()

        inicial = valores.iloc[0]
        final = valores.iloc[-1]

        if inicial <= 0 or final <= 0:
            return np.nan

        anos = len(valores)-1

        return (
            (final/inicial)**(1/anos)-1
        )*100

    except:

        return np.nan


# ================================================================
# DIVIDENDOS
# ================================================================

def analisar_dividendos(ativo):

    try:

        div = ativo.dividends

        if div is None or len(div)==0:

            return np.nan,0

        div = div.dropna()

        if len(div)==0:

            return np.nan,0

        ano_atual = pd.Timestamp.today().year

        ultimos = div[
            div.index.year >= ano_atual-4
        ]

        total = ultimos.sum()

        anos = len(
            ultimos.groupby(
                ultimos.index.year
            ).sum()
        )

        return total,anos

    except:

        return np.nan,0


# ================================================================
# ANÁLISE FUNDAMENTAL
# ================================================================

def analisar_ativo(ticker,forcar=False):

    ticker = norm(ticker)

    if not ticker:
        return None

    if ticker in CACHE and not forcar:

        return CACHE[ticker].copy()

    tipo = identificar_tipo(ticker)

    try:

        ativo = yf.Ticker(
            ticker+".SA"
        )

        # --------------------------------------------------------
        # INFO
        # --------------------------------------------------------

        try:

            info = ativo.info

        except:

            info = {}

        preco = obter_info(
            info,
            "currentPrice",
            "regularMarketPrice",
            "previousClose"
        )

        anterior = obter_info(
            info,
            "previousClose"
        )

        if (
            not pd.isna(preco)
            and not pd.isna(anterior)
            and anterior != 0
        ):

            variacao = (
                preco/anterior-1
            )*100

        else:

            variacao=np.nan

        dy = obter_info(
            info,
            "dividendYield"
        )

        if (
            not pd.isna(dy)
            and abs(dy)<1
        ):

            dy*=100

        pl = obter_info(
            info,
            "trailingPE",
            "forwardPE"
        )

        pvp = obter_info(
            info,
            "priceToBook"
        )

        roe = obter_info(
            info,
            "returnOnEquity"
        )

        if (
            not pd.isna(roe)
            and abs(roe)<2
        ):

            roe*=100

        margem = obter_info(
            info,
            "profitMargins"
        )

        if (
            not pd.isna(margem)
            and abs(margem)<2
        ):

            margem*=100

        divida = obter_info(
            info,
            "debtToEquity"
        )

        # --------------------------------------------------------
        # HISTÓRICO
        # --------------------------------------------------------

        try:

            historico = ativo.history(
                period="5y",
                auto_adjust=False
            )

        except:

            historico=pd.DataFrame()

        if (
            not historico.empty
            and "Volume" in historico.columns
        ):

            liquidez = (
                historico[
                    "Volume"
                ]
                .tail(60)
                .mean()
            )

        else:

            liquidez=np.nan

        # --------------------------------------------------------
        # FINANCEIROS
        # --------------------------------------------------------

        try:

            financeiros = ativo.financials

        except:

            financeiros=pd.DataFrame()

        crescimento_lucro = crescimento(
            financeiros,
            "Net Income"
        )

        crescimento_receita = crescimento(
            financeiros,
            "Total Revenue"
        )

        # --------------------------------------------------------
        # DIVIDENDOS
        # --------------------------------------------------------

        total_dividendos,anos_dividendos = \
            analisar_dividendos(ativo)

        # ========================================================
        # SCORE AÇÕES
        # ========================================================

        if tipo=="AÇÃO":

            # P/L
            if pd.isna(pl):

                s_pl=np.nan

            elif 5<=pl<=12:

                s_pl=100

            elif pl<5:

                s_pl=80

            elif pl<=18:

                s_pl=70

            elif pl<=25:

                s_pl=50

            else:

                s_pl=25

            # P/VP
            if pd.isna(pvp):

                s_pvp=np.nan

            elif .8<=pvp<=1.5:

                s_pvp=100

            elif pvp<.8:

                s_pvp=85

            elif pvp<=2:

                s_pvp=75

            elif pvp<=3:

                s_pvp=50

            else:

                s_pvp=25

            # ROE
            s_roe = (
                score_linear(
                    roe,0,30
                )
                if not pd.isna(roe)
                else np.nan
            )

            # DY
            s_dy = (
                score_linear(
                    dy,0,15
                )
                if not pd.isna(dy)
                else np.nan
            )

            # Lucro
            s_lucro = (
                score_linear(
                    crescimento_lucro,
                    -10,
                    30
                )
                if not pd.isna(
                    crescimento_lucro
                )
                else np.nan
            )

            # Receita
            s_receita = (
                score_linear(
                    crescimento_receita,
                    -10,
                    25
                )
                if not pd.isna(
                    crescimento_receita
                )
                else np.nan
            )

            # Margem
            s_margem = (
                score_linear(
                    margem,
                    0,
                    30
                )
                if not pd.isna(margem)
                else np.nan
            )

            # Dividendos
            s_dividendos=min(
                100,
                anos_dividendos*20
            )

            # Liquidez
            if pd.isna(liquidez):

                s_liquidez=np.nan

            elif liquidez>=10000000:

                s_liquidez=100

            elif liquidez>=5000000:

                s_liquidez=90

            elif liquidez>=1000000:

                s_liquidez=75

            elif liquidez>=300000:

                s_liquidez=55

            else:

                s_liquidez=30

            consistencia=0

            if (
                not pd.isna(crescimento_lucro)
                and crescimento_lucro>0
            ):

                consistencia+=25

            if (
                not pd.isna(crescimento_receita)
                and crescimento_receita>0
            ):

                consistencia+=25

            if (
                not pd.isna(roe)
                and roe>10
            ):

                consistencia+=25

            if (
                not pd.isna(margem)
                and margem>0
            ):

                consistencia+=25

            pesos=[

                (s_pl,10),
                (s_pvp,8),
                (s_roe,10),
                (s_dy,10),
                (s_lucro,15),
                (s_receita,10),
                (s_margem,10),
                (s_dividendos,10),
                (s_liquidez,5),
                (consistencia,12)

            ]

        # ========================================================
        # SCORE FII
        # ========================================================

        else:

            s_dy = (
                score_linear(
                    dy,
                    4,
                    14
                )
                if not pd.isna(dy)
                else np.nan
            )

            if pd.isna(pvp):

                s_pvp=np.nan

            elif .8<=pvp<=1.05:

                s_pvp=100

            elif pvp<.8:

                s_pvp=90

            elif pvp<=1.15:

                s_pvp=80

            elif pvp<=1.30:

                s_pvp=55

            else:

                s_pvp=25

            if pd.isna(liquidez):

                s_liquidez=np.nan

            elif liquidez>=5000000:

                s_liquidez=100

            elif liquidez>=1000000:

                s_liquidez=90

            elif liquidez>=500000:

                s_liquidez=75

            elif liquidez>=100000:

                s_liquidez=55

            else:

                s_liquidez=25

            s_dividendos=min(
                100,
                anos_dividendos*20
            )

            pesos=[

                (s_dy,30),
                (s_pvp,20),
                (s_dividendos,20),
                (s_liquidez,15),
                (s_dividendos,15)

            ]

        # ========================================================
        # SCORE FINAL
        # ========================================================

        soma=0
        peso_total=0

        for nota,peso in pesos:

            if not pd.isna(nota):

                soma+=nota*peso
                peso_total+=peso

        score = (
            soma/peso_total
            if peso_total>0
            else np.nan
        )

        resultado={

            "Ticker":ticker,
            "Tipo":tipo,
            "Preço":preco,
            "Variação %":variacao,
            "DY %":dy,
            "P/L":pl,
            "P/VP":pvp,
            "ROE %":roe,
            "Margem %":margem,
            "Dívida/PL":divida,
            "Crescimento Lucro %":
                crescimento_lucro,
            "Crescimento Receita %":
                crescimento_receita,
            "Dividendos 5 anos":
                total_dividendos,
            "Anos dividendos":
                anos_dividendos,
            "Liquidez":
                liquidez,
            "Score":
                score,
            "Risco":
                risco_por_score(score),
            "Classificação":
                classificacao(score)
        }

        CACHE[ticker]=pd.Series(
            resultado
        )

        return CACHE[ticker].copy()

    except Exception as erro:

        return pd.Series({

            "Ticker":ticker,
            "Tipo":tipo,
            "Preço":np.nan,
            "Variação %":np.nan,
            "DY %":np.nan,
            "P/L":np.nan,
            "P/VP":np.nan,
            "ROE %":np.nan,
            "Margem %":np.nan,
            "Dívida/PL":np.nan,
            "Crescimento Lucro %":np.nan,
            "Crescimento Receita %":np.nan,
            "Dividendos 5 anos":np.nan,
            "Anos dividendos":0,
            "Liquidez":np.nan,
            "Score":np.nan,
            "Risco":"N/D",
            "Classificação":"⚪ ERRO"
        })


# ================================================================
# ADICIONAR ATIVO
# ================================================================

def adicionar_ativo():

    global CARTEIRA

    ticker=norm(
        entrada_ticker.value
    )

    quantidade=float(
        entrada_quantidade.value
    )

    preco_medio=float(
        entrada_preco_medio.value
    )

    if not ticker:

        with saida_carteira:

            print(
                "⚠️ Digite um ticker."
            )

        return

    if quantidade<=0:

        with saida_carteira:

            print(
                "⚠️ A quantidade deve ser maior que zero."
            )

        return

    if preco_medio<=0:

        with saida_carteira:

            print(
                "⚠️ O preço médio deve ser maior que zero."
            )

        return

    nova=pd.DataFrame([{

        "Ticker":ticker,
        "Tipo":identificar_tipo(ticker),
        "Quantidade":quantidade,
        "Preço Médio":preco_medio

    }])

    # Se já existe, soma posição
    if ticker in CARTEIRA["Ticker"].values:

        indice=CARTEIRA[
            CARTEIRA["Ticker"]==ticker
        ].index[0]

        qtd_antiga=CARTEIRA.loc[
            indice,
            "Quantidade"
        ]

        pm_antigo=CARTEIRA.loc[
            indice,
            "Preço Médio"
        ]

        nova_qtd=qtd_antiga+quantidade

        novo_pm=(

            (
                qtd_antiga*pm_antigo
                +
                quantidade*preco_medio
            )
            /
            nova_qtd

        )

        CARTEIRA.loc[
            indice,
            "Quantidade"
        ]=nova_qtd

        CARTEIRA.loc[
            indice,
            "Preço Médio"
        ]=novo_pm

    else:

        CARTEIRA=pd.concat(
            [
                CARTEIRA,
                nova
            ],
            ignore_index=True
        )

    mostrar_carteira()


# ================================================================
# REMOVER ATIVO
# ================================================================

def remover_ativo():

    global CARTEIRA

    ticker=norm(
        entrada_remover.value
    )

    if ticker in CARTEIRA["Ticker"].values:

        CARTEIRA=CARTEIRA[
            CARTEIRA["Ticker"]!=ticker
        ].reset_index(drop=True)

        mostrar_carteira()

    else:

        with saida_carteira:

            clear_output(wait=True)

            print(
                "⚠️ Esse ativo não está na carteira."
            )


# ================================================================
# MOSTRAR CARTEIRA
# ================================================================

def mostrar_carteira():

    with saida_carteira:

        clear_output(wait=True)

        if CARTEIRA.empty:

            print(
                "📭 Sua carteira está vazia."
            )

            print(
                "Adicione seu primeiro ativo acima."
            )

            return

        dados=[]

        patrimonio=0
        custo_total=0

        for _,linha in CARTEIRA.iterrows():

            ticker=linha["Ticker"]

            quantidade=linha["Quantidade"]

            pm=linha["Preço Médio"]

            d=analisar_ativo(ticker)

            preco=d["Preço"]

            if pd.isna(preco):

                valor=np.nan
                custo=np.nan
                lucro=np.nan
                rent=np.nan

            else:

                valor=quantidade*preco

                custo=quantidade*pm

                lucro=valor-custo

                rent=(
                    lucro/custo*100
                    if custo!=0
                    else np.nan
                )

                patrimonio+=valor
                custo_total+=custo

            dados.append({

                "Ticker":ticker,
                "Tipo":linha["Tipo"],
                "Qtd":quantidade,
                "Preço Médio":pm,
                "Preço Atual":preco,
                "Valor Atual":valor,
                "Custo":custo,
                "Lucro/Prejuízo":lucro,
                "Rentabilidade %":rent,
                "DY %":d["DY %"],
                "Score":d["Score"],
                "Risco":d["Risco"]

            })

        df=pd.DataFrame(dados)

        valor_validos=df[
            "Valor Atual"
        ].notna()

        patrimonio=df[
            "Valor Atual"
        ].sum()

        custo_total=df[
            "Custo"
        ].sum()

        lucro_total=(
            patrimonio-custo_total
        )

        rent_total=(
            lucro_total/
            custo_total*100
            if custo_total!=0
            else np.nan
        )

        # Pesos
        if patrimonio>0:

            df["Peso %"]=(
                df["Valor Atual"]/
                patrimonio*100
            )

        else:

            df["Peso %"]=np.nan

        display(
            HTML(f"""

            <div style="
            padding:18px;
            border-radius:15px;
            background:#f3f4f6;">

            <h2>💼 Minha Carteira</h2>

            <p>
            💰 Patrimônio:
            <b>{dinheiro(patrimonio)}</b>
            </p>

            <p>
            💵 Custo total:
            <b>{dinheiro(custo_total)}</b>
            </p>

            <p>
            📈 Lucro/Prejuízo:
            <b>{dinheiro(lucro_total)}</b>
            </p>

            <p>
            📊 Rentabilidade:
            <b>{percentual(rent_total)}</b>
            </p>

            </div>

            """)
        )

        display(
            df.style.format({

                "Qtd":
                    lambda x:
                    f"{x:.2f}",

                "Preço Médio":
                    lambda x:
                    dinheiro(x),

                "Preço Atual":
                    lambda x:
                    dinheiro(x),

                "Valor Atual":
                    lambda x:
                    dinheiro(x),

                "Custo":
                    lambda x:
                    dinheiro(x),

                "Lucro/Prejuízo":
                    lambda x:
                    dinheiro(x),

                "Rentabilidade %":
                    lambda x:
                    percentual(x),

                "DY %":
                    lambda x:
                    percentual(x),

                "Score":
                    lambda x:
                    "N/D"
                    if pd.isna(x)
                    else f"{x:.1f}",

                "Peso %":
                    lambda x:
                    percentual(x)

            }).hide(axis="index")
        )

        # ========================================================
        # GRÁFICO
        # ========================================================

        if patrimonio>0:

            plt.figure(
                figsize=(11,5)
            )

            plt.bar(
                df["Ticker"],
                df["Peso %"]
            )

            plt.title(
                "📊 Distribuição atual da carteira"
            )

            plt.xlabel("Ativo")
            plt.ylabel("Peso (%)")

            plt.xticks(
                rotation=45
            )

            plt.grid(
                axis="y",
                alpha=.25
            )

            plt.tight_layout()

            plt.show()


# ================================================================
# DEFINIR METAS
# ================================================================

def metas_perfil(perfil):

    if perfil=="CONSERVADOR":

        return {

            "RENDA FIXA":60,
            "AÇÕES":15,
            "FIIs":25

        }

    if perfil=="MODERADO":

        return {

            "RENDA FIXA":40,
            "AÇÕES":30,
            "FIIs":30

        }

    return {

        "RENDA FIXA":20,
        "AÇÕES":50,
        "FIIs":30

    }


# ================================================================
# REBALANCEAMENTO
# ================================================================

def calcular_rebalanceamento():

    global ULTIMA_SUGESTAO

    with saida_rebalanceamento:

        clear_output(wait=True)

        aporte=float(
            aporte_rebalanceamento.value
        )

        perfil=perfil_rebalanceamento.value

        metas=metas_perfil(
            perfil
        )

        # --------------------------------------------------------
        # CARTEIRA VAZIA
        # --------------------------------------------------------

        if CARTEIRA.empty:

            print(
                "📭 Cadastre ativos primeiro."
            )

            return

        # --------------------------------------------------------
        # PREÇOS
        # --------------------------------------------------------

        dados=[]

        for _,linha in CARTEIRA.iterrows():

            ticker=linha["Ticker"]

            d=analisar_ativo(ticker)

            preco=d["Preço"]

            if pd.isna(preco):
                continue

            valor=(
                linha["Quantidade"]*
                preco
            )

            dados.append({

                "Ticker":ticker,
                "Tipo":linha["Tipo"],
                "Valor":valor,
                "Score":d["Score"],
                "DY":d["DY %"]

            })

        df=pd.DataFrame(dados)

        if df.empty:

            print(
                "❌ Não foi possível atualizar os preços."
            )

            return

        patrimonio=df[
            "Valor"
        ].sum()

        # --------------------------------------------------------
        # PESO ATUAL
        # --------------------------------------------------------

        df["Peso Atual %"]=(
            df["Valor"]/
            patrimonio*100
        )

        # --------------------------------------------------------
        # META DA CLASSE
        # --------------------------------------------------------

        df["Meta Classe %"]=df[
            "Tipo"
        ].map({

            "AÇÃO":metas["AÇÕES"],
            "FII":metas["FIIs"]

        })

        # --------------------------------------------------------
        # DISTRIBUIÇÃO DA META ENTRE ATIVOS
        # --------------------------------------------------------

        # Quanto cada ativo representa dentro da classe

        for tipo in ["AÇÃO","FII"]:

            indices=df[
                df["Tipo"]==tipo
            ].index

            if len(indices)==0:
                continue

            scores=df.loc[
                indices,
                "Score"
            ].fillna(50)

            scores=scores.clip(
                lower=1
            )

            pesos=scores/scores.sum()

            df.loc[
                indices,
                "Peso Meta %"
            ]=(
                pesos*
                metas[
                    "AÇÕES"
                    if tipo=="AÇÃO"
                    else "FIIs"
                ]
            )

        # --------------------------------------------------------
        # RENDA FIXA
        # --------------------------------------------------------

        renda_fixa_meta=metas[
            "RENDA FIXA"
        ]

        # --------------------------------------------------------
        # NECESSIDADE
        # --------------------------------------------------------

        df["Diferença %"]=(
            df["Peso Meta %"]-
            df["Peso Atual %"]
        )

        df["Necessidade R$"]=(
            df["Diferença %"]/
            100*
            patrimonio
        )

        # --------------------------------------------------------
        # NOVO APORTE
        # --------------------------------------------------------

        positivas=df[
            df["Necessidade R$"]>0
        ].copy()

        if positivas.empty:

            print(
                "✅ Sua carteira está próxima das metas."
            )

            print(
                "O próximo aporte pode ser direcionado "
                "à classe mais abaixo da meta."
            )

            return

        necessidade_total=positivas[
            "Necessidade R$"
        ].sum()

        positivas["Aporte Sugerido"]=(
            positivas["Necessidade R$"]/
            necessidade_total*
            aporte
        )

        # Não ultrapassar necessidade
        positivas["Aporte Sugerido"]=np.minimum(
            positivas["Aporte Sugerido"],
            positivas["Necessidade R$"]
        )

        positivas=positivas.sort_values(
            "Aporte Sugerido",
            ascending=False
        )

        # --------------------------------------------------------
        # RENDA FIXA
        # --------------------------------------------------------

        peso_rf_atual=0

        valor_nao_classificado=0

        peso_classes=df.groupby(
            "Tipo"
        )["Valor"].sum()

        if patrimonio>0:

            peso_acoes=(
                peso_classes.get(
                    "AÇÃO",0
                )/
                patrimonio*100
            )

            peso_fiis=(
                peso_classes.get(
                    "FII",0
                )/
                patrimonio*100
            )

        else:

            peso_acoes=0
            peso_fiis=0

        # Como o sistema não tem cadastro de renda fixa,
        # calcula o quanto deveria existir na meta.

        necessidade_rf=max(
            0,
            (
                renda_fixa_meta-
                (100-peso_acoes-peso_fiis)
            )
        )

        display(
            HTML(f"""

            <div style="
            padding:18px;
            border-radius:15px;
            background:#f3f4f6;">

            <h2>⚖️ REBALANCEAMENTO</h2>

            <p>
            Perfil:
            <b>{perfil}</b>
            </p>

            <p>
            Patrimônio analisado:
            <b>{dinheiro(patrimonio)}</b>
            </p>

            <p>
            Próximo aporte:
            <b>{dinheiro(aporte)}</b>
            </p>

            </div>

            """)
        )

        tabela=positivas[[

            "Ticker",
            "Tipo",
            "Peso Atual %",
            "Peso Meta %",
            "Diferença %",
            "Score",
            "DY",
            "Aporte Sugerido"

        ]].copy()

        tabela.rename(
            columns={
                "DY":"DY %"
            },
            inplace=True
        )

        display(
            tabela.style.format({

                "Peso Atual %":
                    lambda x:
                    percentual(x),

                "Peso Meta %":
                    lambda x:
                    percentual(x),

                "Diferença %":
                    lambda x:
                    percentual(x),

                "Score":
                    lambda x:
                    "N/D"
                    if pd.isna(x)
                    else f"{x:.1f}",

                "DY %":
                    lambda x:
                    percentual(x),

                "Aporte Sugerido":
                    lambda x:
                    dinheiro(x)

            }).hide(axis="index")
        )

        # --------------------------------------------------------
        # GRÁFICO
        # --------------------------------------------------------

        plt.figure(
            figsize=(11,5)
        )

        x=np.arange(
            len(tabela)
        )

        largura=.35

        plt.bar(
            x-largura/2,
            tabela["Peso Atual %"],
            largura,
            label="Atual"
        )

        plt.bar(
            x+largura/2,
            tabela["Peso Meta %"],
            largura,
            label="Meta"
        )

        plt.xticks(
            x,
            tabela["Ticker"],
            rotation=45
        )

        plt.ylabel(
            "Peso (%)"
        )

        plt.title(
            "⚖️ Peso atual × peso desejado"
        )

        plt.legend()

        plt.grid(
            axis="y",
            alpha=.25
        )

        plt.tight_layout()

        plt.show()

        print(
            "\n💡 Sugestão: priorize os ativos que estão "
            "mais abaixo da meta, sempre considerando "
            "se os fundamentos continuam adequados."
        )

        ULTIMA_SUGESTAO=positivas.copy()


# ================================================================
# PESQUISA POR TICKER
# ================================================================

def pesquisar_ticker():

    global ULTIMA_ANALISE

    with saida_pesquisa:

        clear_output(wait=True)

        ticker=norm(
            pesquisa_ticker.value
        )

        if not ticker:

            print(
                "⚠️ Digite um ticker."
            )

            return

        print(
            f"⏳ Analisando {ticker}..."
        )

        d=analisar_ativo(
            ticker,
            forcar=True
        )

        ULTIMA_ANALISE=d.copy()

        if d is None:

            return

        display(
            HTML(f"""

            <div style="
            padding:20px;
            border-radius:18px;
            background:#f3f4f6;">

            <h1>📊 {d['Ticker']}</h1>

            <h2>
            💰 {dinheiro(d['Preço'])}
            </h2>

            <p>
            📈 Variação:
            <b>{percentual(d['Variação %'])}</b>
            </p>

            <p>
            💵 Dividend Yield:
            <b>{percentual(d['DY %'])}</b>
            </p>

            <p>
            ⭐ Score:
            <b>{decimal(d['Score'])}/100</b>
            </p>

            <p>
            🛡️ Risco:
            <b>{d['Risco']}</b>
            </p>

            <h2>
            {d['Classificação']}
            </h2>

            </div>

            """)
        )

        indicadores=pd.DataFrame({

            "Indicador":[

                "Preço",
                "DY",
                "P/L",
                "P/VP",
                "ROE",
                "Margem",
                "Dívida/PL",
                "Crescimento Lucro",
                "Crescimento Receita",
                "Score",
                "Risco"

            ],

            "Valor":[

                dinheiro(d["Preço"]),
                percentual(d["DY %"]),
                decimal(d["P/L"]),
                decimal(d["P/VP"]),
                percentual(d["ROE %"]),
                percentual(d["Margem %"]),
                decimal(d["Dívida/PL"]),
                percentual(d["Crescimento Lucro %"]),
                percentual(d["Crescimento Receita %"]),
                decimal(d["Score"]),
                d["Risco"]

            ]

        })

        display(
            indicadores
        )

        # ========================================================
        # GRÁFICO
        # ========================================================

        try:

            ativo=yf.Ticker(
                ticker+".SA"
            )

            hist=ativo.history(
                period="5y",
                auto_adjust=False
            )

            if not hist.empty:

                plt.figure(
                    figsize=(11,5)
                )

                plt.plot(
                    hist.index,
                    hist["Close"]
                )

                plt.title(
                    f"📈 {ticker} — Histórico de 5 anos"
                )

                plt.xlabel(
                    "Data"
                )

                plt.ylabel(
                    "Preço"
                )

                plt.grid(
                    alpha=.25
                )

                plt.tight_layout()

                plt.show()

        except:

            pass

        # ========================================================
        # CONCLUSÃO
        # ========================================================

        if not pd.isna(d["Score"]):

            if d["Score"]>=75:

                conclusao=(
                    "🟢 ATIVO COM BONS INDICADORES"
                )

            elif d["Score"]>=60:

                conclusao=(
                    "🟡 ATIVO PARA AVALIAÇÃO"
                )

            else:

                conclusao=(
                    "🔴 EXIGE MAIOR CAUTELA"
                )

            display(
                HTML(f"""

                <div style="
                padding:15px;
                border-radius:12px;
                background:#eeeeee;">

                <h3>{conclusao}</h3>

                <p>
                Essa classificação é baseada nos indicadores
                disponíveis e não representa garantia de
                desempenho futuro.
                </p>

                </div>

                """)
            )


# ================================================================
# RANKING
# ================================================================

def gerar_ranking():

    global ULTIMO_RANKING

    with saida_ranking:

        clear_output(wait=True)

        mercado=mercado_ranking.value

        if mercado=="AÇÕES":

            lista=ACOES

        elif mercado=="FIIs":

            lista=FIIS

        else:

            lista=TODOS

        dados=[]

        print(
            "⏳ Gerando ranking..."
        )

        for i,ticker in enumerate(lista):

            print(
                f"\rAnalisando "
                f"{ticker} "
                f"({i+1}/{len(lista)})",
                end=""
            )

            d=analisar_ativo(ticker)

            if d is not None:

                dados.append(
                    d.to_dict()
                )

        print()

        if not dados:

            print(
                "❌ Não foi possível gerar o ranking."
            )

            return

        df=pd.DataFrame(
            dados
        )

        df=df[
            df["Score"].notna()
        ]

        df=df.sort_values(
            [
                "Score",
                "DY %"
            ],
            ascending=False
        )

        ULTIMO_RANKING=df.copy()

        quantidade=int(
            quantidade_ranking.value
        )

        top=df.head(
            quantidade
        )

        tabela=top[[

            "Ticker",
            "Tipo",
            "Preço",
            "DY %",
            "P/L",
            "P/VP",
            "ROE %",
            "Score",
            "Risco",
            "Classificação"

        ]].copy()

        display(
            tabela.style.format({

                "Preço":
                    lambda x:
                    dinheiro(x),

                "DY %":
                    lambda x:
                    percentual(x),

                "P/L":
                    lambda x:
                    decimal(x),

                "P/VP":
                    lambda x:
                    decimal(x),

                "ROE %":
                    lambda x:
                    percentual(x),

                "Score":
                    lambda x:
                    f"{x:.1f}"

            }).hide(axis="index")
        )

        # ========================================================
        # GRÁFICO
        # ========================================================

        plt.figure(
            figsize=(11,5)
        )

        plt.bar(
            top["Ticker"],
            top["Score"]
        )

        plt.title(
            "🏆 Ranking por Score"
        )

        plt.ylabel(
            "Score"
        )

        plt.xlabel(
            "Ativo"
        )

        plt.ylim(
            0,
            100
        )

        plt.xticks(
            rotation=45
        )

        plt.grid(
            axis="y",
            alpha=.25
        )

        plt.tight_layout()

        plt.show()


# ================================================================
# SIMULAÇÃO DE PATRIMÔNIO
# ================================================================

def simular_patrimonio():

    with saida_simulacao:

        clear_output(wait=True)

        inicial=float(
            simulacao_inicial.value
        )

        aporte=float(
            simulacao_aporte.value
        )

        anos=int(
            simulacao_anos.value
        )

        taxa=float(
            simulacao_taxa.value
        )/100

        dy=float(
            simulacao_dy.value
        )/100

        meses=anos*12

        taxa_mensal=(
            (1+taxa)**(1/12)-1
        )

        patrimonio=inicial

        total_aportado=inicial

        resultados=[]

        for mes in range(
            1,
            meses+1
        ):

            patrimonio=(
                patrimonio*
                (1+taxa_mensal)
                +
                aporte
            )

            total_aportado+=aporte

            if mes%12==0:

                ano=mes//12

                dividendos_ano=(
                    patrimonio*dy
                )

                resultados.append({

                    "Ano":ano,

                    "Patrimônio":
                        patrimonio,

                    "Total aportado":
                        total_aportado,

                    "Rendimento":
                        patrimonio-total_aportado,

                    "Dividendos anuais estimados":
                        dividendos_ano,

                    "Dividendos mensais estimados":
                        dividendos_ano/12

                })

        df=pd.DataFrame(
            resultados
        )

        display(
            df.style.format({

                "Patrimônio":
                    lambda x:
                    dinheiro(x),

                "Total aportado":
                    lambda x:
                    dinheiro(x),

                "Rendimento":
                    lambda x:
                    dinheiro(x),

                "Dividendos anuais estimados":
                    lambda x:
                    dinheiro(x),

                "Dividendos mensais estimados":
                    lambda x:
                    dinheiro(x)

            }).hide(axis="index")
        )

        # ========================================================
        # GRÁFICO
        # ========================================================

        plt.figure(
            figsize=(11,5)
        )

        plt.plot(
            df["Ano"],
            df["Patrimônio"],
            marker="o"
        )

        plt.title(
            "📈 Evolução estimada do patrimônio"
        )

        plt.xlabel(
            "Ano"
        )

        plt.ylabel(
            "Patrimônio"
        )

        plt.grid(
            alpha=.25
        )

        plt.tight_layout()

        plt.show()

        final=patrimonio

        lucro=(
            final-total_aportado
        )

        renda_mensal=(
            final*dy/12
        )

        display(
            HTML(f"""

            <div style="
            padding:20px;
            border-radius:15px;
            background:#f3f4f6;">

            <h2>🎯 RESULTADO FINAL</h2>

            <p>
            Patrimônio:
            <b>{dinheiro(final)}</b>
            </p>

            <p>
            Total aportado:
            <b>{dinheiro(total_aportado)}</b>
            </p>

            <p>
            Rendimentos:
            <b>{dinheiro(lucro)}</b>
            </p>

            <p>
            Dividendos mensais estimados:
            <b>{dinheiro(renda_mensal)}</b>
            </p>

            </div>

            """)
        )

        print(
            "\n⚠️ A rentabilidade e os dividendos usados "
            "na simulação são hipóteses editáveis."
        )


# ================================================================
# EXPORTAR CARTEIRA
# ================================================================

def exportar_carteira():

    if CARTEIRA.empty:

        print(
            "⚠️ Carteira vazia."
        )

        return

    caminho=(
        "/content/"
        "minha_carteira_5_0.csv"
    )

    CARTEIRA.to_csv(
        caminho,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        "✅ Arquivo criado:"
    )

    print(caminho)

    try:

        from google.colab import files

        files.download(
            caminho
        )

    except:

        pass


# ================================================================
# EXPORTAR SUGESTÃO
# ================================================================

def exportar_sugestao():

    if ULTIMA_SUGESTAO.empty:

        print(
            "⚠️ Calcule o rebalanceamento primeiro."
        )

        return

    caminho=(
        "/content/"
        "proximo_aporte_5_0.csv"
    )

    ULTIMA_SUGESTAO.to_csv(
        caminho,
        index=False,
        encoding="utf-8-sig"
    )

    try:

        from google.colab import files

        files.download(
            caminho
        )

    except:

        pass

    print(
        "✅ Sugestão exportada."
    )


# ================================================================
# EXPORTAR RANKING
# ================================================================

def exportar_ranking():

    if ULTIMO_RANKING.empty:

        print(
            "⚠️ Gere o ranking primeiro."
        )

        return

    caminho=(
        "/content/"
        "ranking_5_0.csv"
    )

    ULTIMO_RANKING.to_csv(
        caminho,
        index=False,
        encoding="utf-8-sig"
    )

    try:

        from google.colab import files

        files.download(
            caminho
        )

    except:

        pass

    print(
        "✅ Ranking exportado."
    )


# ================================================================
# INTERFACE
# ================================================================

titulo=widgets.HTML("""

<div style="
background:#111827;
color:white;
padding:25px;
border-radius:18px;
margin-bottom:15px;">

<h1>🚀 INVEST ANALYZER 5.0</h1>

<h3>
Carteira Real Inteligente
</h3>

<p>
Análise • Score • Rebalanceamento • Aportes • Simulação
</p>

</div>

""")


# ================================================================
# ABA MINHA CARTEIRA
# ================================================================

entrada_ticker=widgets.Text(

    value="PETR4",

    description="Ticker:"

)

entrada_quantidade=widgets.FloatText(

    value=10,

    description="Quantidade:"

)

entrada_preco_medio=widgets.FloatText(

    value=30,

    description="Preço médio:"

)

botao_adicionar=widgets.Button(

    description="➕ Adicionar",

    button_style="primary"

)

entrada_remover=widgets.Text(

    description="Remover:"

)

botao_remover=widgets.Button(

    description="🗑️ Remover",

    button_style="danger"

)

botao_atualizar=widgets.Button(

    description="🔄 Atualizar preços",

    button_style="warning"

)

botao_exportar=widgets.Button(

    description="📥 Exportar CSV",

    button_style="success"

)

saida_carteira=widgets.Output()


botao_adicionar.on_click(
    lambda b:
    adicionar_ativo()
)

botao_remover.on_click(
    lambda b:
    remover_ativo()
)

botao_atualizar.on_click(
    lambda b:
    mostrar_carteira()
)

botao_exportar.on_click(
    lambda b:
    exportar_carteira()
)


aba_carteira=widgets.VBox([

    widgets.HTML(
        "<h2>💼 Minha Carteira Real</h2>"
    ),

    widgets.HBox([
        entrada_ticker,
        entrada_quantidade,
        entrada_preco_medio
    ]),

    widgets.HBox([
        botao_adicionar,
        entrada_remover,
        botao_remover,
        botao_atualizar,
        botao_exportar
    ]),

    saida_carteira

])


# ================================================================
# ABA REBALANCEAMENTO
# ================================================================

perfil_rebalanceamento=widgets.Dropdown(

    options=[
        "CONSERVADOR",
        "MODERADO",
        "ARROJADO"
    ],

    value="MODERADO",

    description="Perfil:"

)

aporte_rebalanceamento=widgets.FloatText(

    value=500,

    description="Próximo aporte:"

)

botao_rebalancear=widgets.Button(

    description="⚖️ Calcular aporte",

    button_style="primary"

)

botao_exportar_sugestao=widgets.Button(

    description="📥 Exportar",

    button_style="success"

)

saida_rebalanceamento=widgets.Output()


botao_rebalancear.on_click(
    lambda b:
    calcular_rebalanceamento()
)

botao_exportar_sugestao.on_click(
    lambda b:
    exportar_sugestao()
)


aba_rebalanceamento=widgets.VBox([

    widgets.HTML(
        "<h2>⚖️ Próximo aporte inteligente</h2>"
    ),

    widgets.HBox([
        perfil_rebalanceamento,
        aporte_rebalanceamento
    ]),

    widgets.HBox([
        botao_rebalancear,
        botao_exportar_sugestao
    ]),

    saida_rebalanceamento

])


# ================================================================
# ABA PESQUISA
# ================================================================

pesquisa_ticker=widgets.Text(

    value="PETR4",

    description="Ticker:"

)

botao_pesquisar=widgets.Button(

    description="🔎 Pesquisar",

    button_style="primary"

)

saida_pesquisa=widgets.Output()


botao_pesquisar.on_click(
    lambda b:
    pesquisar_ticker()
)


aba_pesquisa=widgets.VBox([

    widgets.HTML(
        "<h2>🔎 Ficha completa do ativo</h2>"
    ),

    widgets.HBox([
        pesquisa_ticker,
        botao_pesquisar
    ]),

    saida_pesquisa

])


# ================================================================
# ABA RANKING
# ================================================================

mercado_ranking=widgets.Dropdown(

    options=[
        "TODOS",
        "AÇÕES",
        "FIIs"
    ],

    value="TODOS",

    description="Mercado:"

)

quantidade_ranking=widgets.IntSlider(

    value=10,

    min=5,

    max=30,

    step=5,

    description="Top:"

)

botao_gerar_ranking=widgets.Button(

    description="🏆 Gerar ranking",

    button_style="primary"

)

botao_exportar_rank=widgets.Button(

    description="📥 Exportar CSV",

    button_style="success"

)

saida_ranking=widgets.Output()


botao_gerar_ranking.on_click(
    lambda b:
    gerar_ranking()
)

botao_exportar_rank.on_click(
    lambda b:
    exportar_ranking()
)


aba_ranking=widgets.VBox([

    widgets.HTML(
        "<h2>🏆 Ranking de ativos</h2>"
    ),

    widgets.HBox([
        mercado_ranking,
        quantidade_ranking
    ]),

    widgets.HBox([
        botao_gerar_ranking,
        botao_exportar_rank
    ]),

    saida_ranking

])


# ================================================================
# ABA SIMULAÇÃO
# ================================================================

simulacao_inicial=widgets.FloatText(

    value=0,

    description="Inicial:"

)

simulacao_aporte=widgets.FloatText(

    value=500,

    description="Aporte/mês:"

)

simulacao_anos=widgets.IntSlider(

    value=20,

    min=1,

    max=30,

    step=1,

    description="Anos:"

)

simulacao_taxa=widgets.FloatSlider(

    value=10,

    min=1,

    max=20,

    step=.5,

    description="Taxa anual:"

)

simulacao_dy=widgets.FloatSlider(

    value=7,

    min=0,

    max=15,

    step=.5,

    description="DY:"

)

botao_simular=widgets.Button(

    description="📈 Simular",

    button_style="primary"

)

saida_simulacao=widgets.Output()


botao_simular.on_click(
    lambda b:
    simular_patrimonio()
)


aba_simulacao=widgets.VBox([

    widgets.HTML(
        "<h2>📈 Simulador de patrimônio</h2>"
    ),

    widgets.HBox([
        simulacao_inicial,
        simulacao_aporte
    ]),

    widgets.HBox([
        simulacao_anos,
        simulacao_taxa,
        simulacao_dy
    ]),

    botao_simular,

    saida_simulacao

])


# ================================================================
# ABA METODOLOGIA
# ================================================================

aba_metodologia=widgets.HTML("""

<h2>🧠 Como funciona o sistema</h2>

<h3>⭐ Score</h3>

<p>
O Score varia de <b>0 a 100</b> e utiliza indicadores
fundamentalistas disponíveis.
</p>

<h3>⚖️ Perfis</h3>

<p>
<b>Conservador</b><br>
60% Renda Fixa • 25% FIIs • 15% Ações
</p>

<p>
<b>Moderado</b><br>
40% Renda Fixa • 30% FIIs • 30% Ações
</p>

<p>
<b>Arrojado</b><br>
20% Renda Fixa • 30% FIIs • 50% Ações
</p>

<h3>💰 Próximo aporte</h3>

<p>
O sistema verifica a diferença entre o peso atual
e o peso desejado e prioriza os ativos que estão
mais abaixo da meta.
</p>

<h3>📈 Simulação</h3>

<p>
A simulação usa uma taxa anual definida por você.
Ela é uma hipótese matemática, não uma previsão.
</p>

<hr>

<h3>⚠️ IMPORTANTE</h3>

<p>
Este sistema não garante lucro nem prevê o futuro.
Preços, dividendos, lucros e indicadores podem mudar.
</p>

<p>
Antes de investir, avalie os ativos e seus riscos.
</p>

""")


# ================================================================
# ABAS
# ================================================================

abas=widgets.Tab(

    children=[

        aba_carteira,
        aba_rebalanceamento,
        aba_pesquisa,
        aba_ranking,
        aba_simulacao,
        aba_metodologia

    ]

)

abas.set_title(
    0,
    "💼 Carteira"
)

abas.set_title(
    1,
    "⚖️ Aporte"
)

abas.set_title(
    2,
    "🔎 Ativo"
)

abas.set_title(
    3,
    "🏆 Ranking"
)

abas.set_title(
    4,
    "📈 Simulação"
)

abas.set_title(
    5,
    "🧠 Metodologia"
)


# ================================================================
# INICIAR
# ================================================================

display(
    titulo,
    abas
)

print(
    "✅ INVEST ANALYZER 5.0 iniciado!"
)

print(
    "Comece pela aba 💼 Carteira."
)

# ================================================================
# PESQUISA INICIAL
# ================================================================

pesquisar_ticker()
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=10000)

