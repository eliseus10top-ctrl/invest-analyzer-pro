
import io
import math
import os
import time
import warnings
from datetime import datetime

from flask import Flask, jsonify, render_template_string, request, send_file
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

warnings.filterwarnings("ignore")

app = Flask(__name__)
VERSAO = "5.0"
CACHE = {}
CACHE_TIME = {}
CACHE_SEARCH = {}
CACHE_SEARCH_TIME = {}
CACHE_TTL = 300

ACOES_PADRAO = [
    "PETR4","VALE3","ITUB4","BBAS3","BBDC4","ABEV3","WEGE3",
    "PRIO3","SUZB3","ELET3","RENT3","JBSS3","GGBR4","CSNA3",
    "BBSE3","EGIE3","TAEE11","CMIG4","CPLE6","VIVT3"
]
FIIS_PADRAO = [
    "MXRF11","HGLG11","KNRI11","BTLG11","TRXF11","XPML11","VISC11",
    "XPLG11","CPTS11","RBRF11","BCFF11","HGRU11","PVBI11","VILG11",
    "MALL11","IRDM11","KNCR11","HGRE11","RECT11","ALZR11"
]


def numero(valor, padrao=np.nan):
    try:
        if valor is None:
            return padrao
        if isinstance(valor, str):
            valor = valor.strip().replace("%", "").replace(",", ".")
        valor = float(valor)
        return valor if np.isfinite(valor) else padrao
    except Exception:
        return padrao


def fmt_num(valor, casas=2):
    if valor is None:
        return "N/D"
    try:
        if pd.isna(valor):
            return "N/D"
        return f"{float(valor):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "N/D"


def fmt_money(valor):
    return "N/D" if not valido(valor) else f"R$ {fmt_num(valor)}"


def fmt_percent(valor):
    return "N/D" if not valido(valor) else f"{float(valor):.2f}%".replace(".", ",")


def valido(valor):
    try:
        return valor is not None and not pd.isna(valor)
    except Exception:
        return False


def normalizar_ticker(ticker):
    ticker = str(ticker or "").strip().upper().replace(" ", "")
    if not ticker:
        return ""
    if ticker.endswith(".SA") or ticker.endswith("-USD") or "." in ticker:
        return ticker
    return ticker + ".SA"


def ticker_sem_sa(ticker):
    return str(ticker or "").upper().replace(".SA", "")


def possiveis_simbolos(consulta):
    consulta = str(consulta or "").strip().upper().replace(" ", "")
    if not consulta:
        return []
    lista = [consulta] if consulta.endswith(".SA") else [consulta + ".SA", consulta]
    if "-" not in consulta:
        lista.append(consulta + "-USD")
    return list(dict.fromkeys(lista))


def obter_dados(ticker, periodo="1y"):
    ticker_yf = normalizar_ticker(ticker)
    if not ticker_yf:
        return None

    chave = (ticker_yf, periodo)
    agora = time.time()
    if chave in CACHE and agora - CACHE_TIME.get(chave, 0) < CACHE_TTL:
        return CACHE[chave]

    try:
        ativo = yf.Ticker(ticker_yf)
        historico = ativo.history(period=periodo, interval="1d", auto_adjust=False)
        if historico is None or historico.empty:
            return None

        try:
            info = ativo.info or {}
        except Exception:
            info = {}

        try:
            dividendos = ativo.dividends
        except Exception:
            dividendos = pd.Series(dtype=float)

        dados = {
            "ativo": ativo,
            "info": info if isinstance(info, dict) else {},
            "historico": historico,
            "dividendos": dividendos if dividendos is not None else pd.Series(dtype=float)
        }
        CACHE[chave] = dados
        CACHE_TIME[chave] = agora
        return dados
    except Exception:
        return None


def pesquisar_ativo(consulta, limite=10):
    consulta = str(consulta or "").strip()
    if not consulta:
        return []

    chave = consulta.upper()
    agora = time.time()
    if chave in CACHE_SEARCH and agora - CACHE_SEARCH_TIME.get(chave, 0) < CACHE_TTL:
        return CACHE_SEARCH[chave]

    resultados = []
    try:
        busca = yf.Search(consulta, max_results=limite)
        for item in (getattr(busca, "quotes", []) or []):
            if isinstance(item, dict) and item.get("symbol"):
                resultados.append({
                    "Ticker": item["symbol"],
                    "Nome": item.get("longname") or item.get("shortname") or "",
                    "Tipo": item.get("quoteType") or "",
                    "Bolsa": item.get("exchange") or ""
                })
    except Exception:
        pass

    if not resultados:
        for simbolo in possiveis_simbolos(consulta):
            dados = obter_dados(simbolo, "5d")
            if dados is not None:
                info = dados["info"]
                resultados.append({
                    "Ticker": simbolo,
                    "Nome": info.get("longName") or info.get("shortName") or simbolo,
                    "Tipo": info.get("quoteType") or "",
                    "Bolsa": info.get("exchange") or ""
                })
                break

    finais = []
    vistos = set()
    for item in resultados:
        if item["Ticker"] not in vistos:
            vistos.add(item["Ticker"])
            finais.append(item)

    CACHE_SEARCH[chave] = finais
    CACHE_SEARCH_TIME[chave] = agora
    return finais


def encontrar_ticker(consulta):
    consulta = str(consulta or "").strip()
    if not consulta:
        return None

    for simbolo in possiveis_simbolos(consulta):
        dados = obter_dados(simbolo, "5d")
        if dados is not None and not dados["historico"].empty:
            return simbolo

    resultados = pesquisar_ativo(consulta)
    return resultados[0]["Ticker"] if resultados else None


def primeiro_valor(info, nomes):
    if not isinstance(info, dict):
        return np.nan
    for nome in nomes:
        valor = numero(info.get(nome))
        if valido(valor):
            return valor
    return np.nan


def calcular_rsi(precos, periodo=14):
    if precos is None or len(precos) < periodo + 1:
        return np.nan
    delta = precos.diff()
    ganhos = delta.clip(lower=0)
    perdas = -delta.clip(upper=0)
    media_ganho = ganhos.rolling(periodo).mean()
    media_perda = perdas.rolling(periodo).mean()
    if media_perda.iloc[-1] == 0:
        return 100.0
    rs = media_ganho / media_perda
    return float((100 - (100 / (1 + rs))).iloc[-1])


def calcular_drawdown(precos):
    if precos is None or len(precos) == 0:
        return np.nan
    maximo = precos.cummax()
    return float(((precos / maximo) - 1).min() * 100)


def identificar_tipo(info, ticker):
    tipo = str(info.get("quoteType", "")).upper()
    ticker = str(ticker).upper()
    if "CRYPTO" in tipo or ticker.endswith("-USD"):
        return "Criptomoeda"
    if tipo == "ETF":
        return "ETF"
    if tipo == "MUTUALFUND":
        return "Fundo"
    if ticker.endswith(".SA") and len(ticker_sem_sa(ticker)) == 6 and ticker_sem_sa(ticker)[-2:].isdigit():
        return "Possível FII/ETF"
    if tipo in ("EQUITY", "STOCK"):
        return "Ação"
    if "INDEX" in tipo:
        return "Índice"
    return "Outro"


def analisar_ativo(consulta):
    ticker = encontrar_ticker(consulta)
    if not ticker:
        return None

    dados = obter_dados(ticker, "5y") or obter_dados(ticker, "1y")
    if dados is None:
        return None

    info = dados["info"]
    historico = dados["historico"].dropna(subset=["Close"]).copy()
    if historico.empty:
        return None

    precos = historico["Close"].astype(float)
    preco = float(precos.iloc[-1])
    tipo = identificar_tipo(info, ticker)

    def retorno_dias(dias):
        if len(precos) < 2:
            return np.nan
        inicio = precos.iloc[0] if len(precos) <= dias else precos.iloc[-dias]
        return np.nan if inicio == 0 else (precos.iloc[-1] / inicio - 1) * 100

    dividendos = dados["dividendos"]
    dy = primeiro_valor(info, ["dividendYield"])
    if valido(dy) and abs(dy) <= 2:
        dy *= 100

    dividendos_12m = 0.0
    qtd_dividendos = 0
    try:
        if dividendos is not None and not dividendos.empty:
            data_final = dividendos.index.max()
            recentes = dividendos[dividendos.index >= data_final - pd.Timedelta(days=365)]
            dividendos_12m = float(recentes.sum())
            qtd_dividendos = int(len(recentes))
            if not valido(dy) and preco > 0 and dividendos_12m > 0:
                dy = dividendos_12m / preco * 100
    except Exception:
        pass

    def percentual_info(chaves):
        x = primeiro_valor(info, chaves)
        if valido(x) and abs(x) <= 2:
            x *= 100
        return x

    precos_1a = precos.tail(252)
    maxima = float(precos_1a.max())
    minima = float(precos_1a.min())
    retornos = precos.pct_change().dropna()

    d = {
        "Ticker": ticker,
        "Nome": info.get("longName") or info.get("shortName") or ticker,
        "Tipo": tipo,
        "Preço": preco,
        "Variação diária (%)": ((precos.iloc[-1] / precos.iloc[-2]) - 1) * 100 if len(precos) >= 2 else np.nan,
        "Retorno 1M (%)": retorno_dias(21),
        "Retorno 3M (%)": retorno_dias(63),
        "Retorno 6M (%)": retorno_dias(126),
        "Retorno 1A (%)": retorno_dias(252),
        "Retorno 3A (%)": retorno_dias(756),
        "Retorno 5A (%)": retorno_dias(1260),
        "Máxima 52S": maxima,
        "Mínima 52S": minima,
        "Distância da máxima (%)": (preco / maxima - 1) * 100 if maxima else np.nan,
        "Distância da mínima (%)": (preco / minima - 1) * 100 if minima else np.nan,
        "Volatilidade anual (%)": retornos.std() * math.sqrt(252) * 100 if len(retornos) > 20 else np.nan,
        "Drawdown máximo (%)": calcular_drawdown(precos),
        "P/L": primeiro_valor(info, ["trailingPE", "forwardPE"]),
        "P/VP": primeiro_valor(info, ["priceToBook"]),
        "EV/EBITDA": primeiro_valor(info, ["enterpriseToEbitda"]),
        "ROE (%)": percentual_info(["returnOnEquity"]),
        "ROA (%)": percentual_info(["returnOnAssets"]),
        "Margem líquida (%)": percentual_info(["profitMargins"]),
        "Margem operacional (%)": percentual_info(["operatingMargins"]),
        "Crescimento receita (%)": percentual_info(["revenueGrowth"]),
        "Crescimento lucro (%)": percentual_info(["earningsGrowth"]),
        "Dívida/Patrimônio": primeiro_valor(info, ["debtToEquity"]),
        "Liquidez corrente": primeiro_valor(info, ["currentRatio"]),
        "Beta": primeiro_valor(info, ["beta", "beta3Year"]),
        "Dividend Yield (%)": dy,
        "Dividendos 12M": dividendos_12m,
        "Quantidade dividendos 12M": qtd_dividendos,
        "Dividendos anuais informados": primeiro_valor(info, ["dividendRate"]),
        "Valor de mercado": primeiro_valor(info, ["marketCap"]),
        "Enterprise Value": primeiro_valor(info, ["enterpriseValue"]),
        "Volume": primeiro_valor(info, ["volume"]),
        "Volume médio": primeiro_valor(info, ["averageVolume", "averageVolume10days"]),
        "RSI": calcular_rsi(precos),
        "MM20": precos.rolling(20).mean().iloc[-1] if len(precos) >= 20 else np.nan,
        "MM50": precos.rolling(50).mean().iloc[-1] if len(precos) >= 50 else np.nan,
        "MM200": precos.rolling(200).mean().iloc[-1] if len(precos) >= 200 else np.nan,
        "_historico": historico,
        "_dividendos": dividendos,
    }
    return avaliar_ativo(d)


def nota_desempenho(d):
    notas = []
    for x in [d.get("Retorno 1A (%)"), d.get("Retorno 3A (%)"), d.get("Retorno 5A (%)")]:
        if valido(x):
            notas.append(10 if x >= 30 else 9 if x >= 20 else 8 if x >= 10 else 7 if x >= 5 else 6 if x >= 0 else 4 if x >= -10 else 2)
    return round(sum(notas) / len(notas), 2) if notas else 5.0


def nota_dividendos(d):
    tipo = str(d.get("Tipo", "")).lower()
    dy = d.get("Dividend Yield (%)")
    if "cripto" in tipo or "índice" in tipo:
        return 5.0
    if not valido(dy):
        return 6.0 if d.get("Dividendos 12M", 0) > 0 else 5.0
    return 10 if dy >= 10 else 9 if dy >= 8 else 8 if dy >= 6 else 7 if dy >= 4 else 6 if dy >= 2 else 4 if dy > 0 else 2


def nota_fundamentos(d):
    if "cripto" in str(d.get("Tipo", "")).lower():
        return 5.0
    notas = []
    x = d.get("ROE (%)")
    if valido(x): notas.append(10 if x >= 25 else 9 if x >= 20 else 8 if x >= 15 else 7 if x >= 10 else 5 if x >= 5 else 3)
    x = d.get("Margem líquida (%)")
    if valido(x): notas.append(10 if x >= 25 else 9 if x >= 15 else 8 if x >= 10 else 6 if x >= 5 else 4 if x >= 0 else 2)
    x = d.get("Crescimento lucro (%)")
    if valido(x): notas.append(10 if x >= 20 else 9 if x >= 10 else 8 if x >= 5 else 6 if x >= 0 else 4 if x >= -10 else 2)
    x = d.get("Liquidez corrente")
    if valido(x): notas.append(9 if x >= 2 else 8 if x >= 1.5 else 7 if x >= 1 else 5 if x >= .8 else 3)
    return round(sum(notas) / len(notas), 2) if notas else 5.0


def nota_valuation(d):
    if "cripto" in str(d.get("Tipo", "")).lower():
        return 5.0
    notas = []
    x = d.get("P/L")
    if valido(x) and x > 0: notas.append(10 if x <= 8 else 9 if x <= 12 else 8 if x <= 16 else 6 if x <= 20 else 4 if x <= 30 else 2)
    x = d.get("P/VP")
    if valido(x) and x > 0: notas.append(10 if x <= 1 else 9 if x <= 1.5 else 8 if x <= 2 else 6 if x <= 3 else 4 if x <= 5 else 2)
    x = d.get("EV/EBITDA")
    if valido(x) and x > 0: notas.append(10 if x <= 6 else 8 if x <= 10 else 6 if x <= 15 else 4 if x <= 20 else 2)
    return round(sum(notas) / len(notas), 2) if notas else 5.0


def nota_risco(d):
    notas = []
    x = d.get("Volatilidade anual (%)")
    if valido(x): notas.append(10 if x <= 15 else 8 if x <= 25 else 6 if x <= 35 else 4 if x <= 50 else 2)
    x = d.get("Drawdown máximo (%)")
    if valido(x):
        x = abs(x)
        notas.append(10 if x <= 15 else 8 if x <= 25 else 6 if x <= 40 else 4 if x <= 55 else 2)
    x = d.get("Dívida/Patrimônio")
    if valido(x): notas.append(10 if x <= 30 else 8 if x <= 60 else 6 if x <= 100 else 4 if x <= 150 else 2)
    x = d.get("Beta")
    if valido(x):
        x = abs(x)
        notas.append(10 if x <= .8 else 8 if x <= 1.1 else 6 if x <= 1.4 else 4 if x <= 1.8 else 2)
    return round(sum(notas) / len(notas), 2) if notas else 5.0


def nota_tecnica(d):
    notas = []
    preco = d.get("Preço")
    for chave, bom, ruim in [("MM20",8,4),("MM50",9,4),("MM200",10,3)]:
        media = d.get(chave)
        if valido(preco) and valido(media):
            notas.append(bom if preco > media else ruim)
    rsi = d.get("RSI")
    if valido(rsi):
        notas.append(9 if 40 <= rsi <= 60 else 8 if 30 <= rsi < 40 else 7 if 60 < rsi <= 70 else 6 if rsi < 30 else 4)
    return round(sum(notas) / len(notas), 2) if notas else 5.0


def classificar_risco(nota):
    return "🟢 Baixo" if nota >= 8.5 else "🟢 Moderado" if nota >= 7 else "🟡 Médio" if nota >= 5.5 else "🟠 Alto" if nota >= 4 else "🔴 Muito alto"


def gerar_conclusao(nota):
    return "🟢 FAVORÁVEL" if nota >= 8.5 else "🟢 FAVORÁVEL COM ATENÇÃO" if nota >= 7 else "🟡 NEUTRA" if nota >= 5.5 else "🟠 DESFAVORÁVEL" if nota >= 4 else "🔴 MUITO DESFAVORÁVEL"


def gerar_alertas(d):
    a = []
    if valido(d.get("Variação diária (%)")) and d["Variação diária (%)"] <= -5:
        a.append(f"⚠️ Queda diária forte: {fmt_percent(d['Variação diária (%)'])}")
    if valido(d.get("Distância da máxima (%)")) and d["Distância da máxima (%)"] <= -30:
        a.append(f"⚠️ {abs(d['Distância da máxima (%)']):.1f}% abaixo da máxima de 52 semanas.")
    if valido(d.get("Volatilidade anual (%)")) and d["Volatilidade anual (%)"] >= 40:
        a.append(f"⚠️ Volatilidade elevada: {fmt_percent(d['Volatilidade anual (%)'])} ao ano.")
    if valido(d.get("Drawdown máximo (%)")) and d["Drawdown máximo (%)"] <= -50:
        a.append(f"⚠️ Drawdown máximo elevado: {fmt_percent(d['Drawdown máximo (%)'])}.")
    if valido(d.get("Dívida/Patrimônio")) and d["Dívida/Patrimônio"] >= 150:
        a.append(f"⚠️ Dívida/Patrimônio elevada: {fmt_num(d['Dívida/Patrimônio'])}%.")
    if valido(d.get("P/L")) and d["P/L"] >= 30:
        a.append(f"⚠️ P/L elevado: {fmt_num(d['P/L'])}.")
    if valido(d.get("RSI")):
        if d["RSI"] >= 70: a.append(f"⚠️ RSI em possível sobrecompra: {fmt_num(d['RSI'],1)}")
        elif d["RSI"] <= 30: a.append(f"ℹ️ RSI em possível sobrevenda: {fmt_num(d['RSI'],1)}")
    return a or ["✅ Nenhum alerta relevante identificado."]


def gerar_positivos(d):
    p = []
    if valido(d.get("Retorno 1A (%)")) and d["Retorno 1A (%)"] >= 10: p.append(f"📈 Retorno de 1 ano positivo: {fmt_percent(d['Retorno 1A (%)'])}.")
    if valido(d.get("ROE (%)")) and d["ROE (%)"] >= 15: p.append(f"💪 ROE elevado: {fmt_percent(d['ROE (%)'])}.")
    if valido(d.get("Dividend Yield (%)")) and d["Dividend Yield (%)"] >= 6: p.append(f"💰 Dividend Yield atrativo: {fmt_percent(d['Dividend Yield (%)'])}.")
    if valido(d.get("Volatilidade anual (%)")) and d["Volatilidade anual (%)"] <= 25: p.append(f"🛡️ Volatilidade relativamente baixa: {fmt_percent(d['Volatilidade anual (%)'])}.")
    if valido(d.get("P/L")) and 0 < d["P/L"] <= 12: p.append(f"💵 P/L relativamente baixo: {fmt_num(d['P/L'])}.")
    if valido(d.get("Preço")) and valido(d.get("MM200")) and d["Preço"] > d["MM200"]: p.append("📊 Preço acima da média móvel de 200 dias.")
    return p or ["ℹ️ Não foram identificados pontos positivos fortes pelos critérios atuais."]


def avaliar_ativo(d):
    desempenho = nota_desempenho(d)
    dividendos = nota_dividendos(d)
    fundamentos = nota_fundamentos(d)
    valuation = nota_valuation(d)
    risco = nota_risco(d)
    tecnica = nota_tecnica(d)
    final = round(
        desempenho*.25 + dividendos*.15 + fundamentos*.20 +
        valuation*.15 + risco*.15 + tecnica*.10, 2
    )
    d = dict(d)
    d.update({
        "Nota desempenho": desempenho,
        "Nota dividendos": dividendos,
        "Nota fundamentos": fundamentos,
        "Nota valuation": valuation,
        "Nota risco": risco,
        "Nota técnica": tecnica,
        "NOTA FINAL": max(0, min(10, final)),
        "RISCO": classificar_risco(risco),
        "CONCLUSÃO": gerar_conclusao(final),
        "ALERTAS": gerar_alertas(d),
        "PONTOS POSITIVOS": gerar_positivos(d)
    })
    return d


def analisar_lista(lista):
    resultados = []
    for ticker in lista:
        try:
            d = analisar_ativo(ticker)
            if d:
                resultados.append({
                    "Ticker": ticker_sem_sa(d["Ticker"]),
                    "Nome": d["Nome"],
                    "Preço": d["Preço"],
                    "DY (%)": d["Dividend Yield (%)"],
                    "P/L": d["P/L"],
                    "P/VP": d["P/VP"],
                    "ROE (%)": d["ROE (%)"],
                    "Var. 1A (%)": d["Retorno 1A (%)"],
                    "Nota": d["NOTA FINAL"],
                    "Risco": d["RISCO"],
                    "Conclusão": d["CONCLUSÃO"]
                })
        except Exception:
            continue
    df = pd.DataFrame(resultados)
    return df.sort_values("Nota", ascending=False, na_position="last").reset_index(drop=True) if not df.empty else df


def grafico_preco(d):
    hist = d["_historico"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index.astype(str), y=hist["Close"], mode="lines", name="Preço"))
    fig.update_layout(title=f"📈 {ticker_sem_sa(d['Ticker'])} — Histórico", height=430)
    return fig.to_dict()


def grafico_dividendos(d):
    serie = d["_dividendos"]
    fig = go.Figure()
    if serie is None or serie.empty:
        fig.update_layout(title="Dividendos não encontrados", height=430)
        return fig.to_dict()
    serie = serie.tail(24)
    fig.add_trace(go.Bar(x=serie.index.astype(str), y=serie.values, name="Dividendos"))
    fig.update_layout(title=f"💰 Dividendos — {ticker_sem_sa(d['Ticker'])}", height=430)
    return fig.to_dict()


def limpar_para_json(d):
    saida = {}
    for k, v in d.items():
        if k.startswith("_"):
            continue
        if isinstance(v, (np.floating, np.integer)):
            saida[k] = None if pd.isna(v) else float(v)
        elif isinstance(v, float) and math.isnan(v):
            saida[k] = None
        else:
            saida[k] = v
    return saida


HTML = r'''
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>INVEST ANALYZER 5.0</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;background:#0f1117;color:#f4f4f4}
.container{max-width:1400px;margin:auto;padding:20px}.hero{text-align:center;padding:15px}
h1{margin:0;font-size:34px}.sub{color:#aeb6c3;margin-top:8px}
.search{display:flex;gap:10px;margin:20px 0}.search input{flex:1;padding:15px;border-radius:10px;border:1px solid #303744;background:#181c25;color:white;font-size:16px}
button{padding:13px 16px;border:0;border-radius:10px;background:#2f81f7;color:white;font-weight:bold;cursor:pointer}
button.secondary{background:#252b36}.buttons{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:15px}
.panel{background:#181c25;border:1px solid #2c3340;border-radius:14px;padding:18px;margin-top:15px}
.cardgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:15px 0}
.card{background:#11151d;border:1px solid #303744;border-radius:11px;padding:13px}.label{font-size:12px;color:#9ba5b4}.value{font-size:20px;font-weight:bold;margin-top:6px}
.good{color:#5ee58a}.warn{color:#ffd166}.bad{color:#ff6b6b}.small{color:#9ba5b4;font-size:13px}
table{width:100%;border-collapse:collapse}th,td{padding:9px;border-bottom:1px solid #303744;text-align:left}th{color:#b8c1cf}
.alert{padding:6px 0}@media(max-width:700px){.search{flex-direction:column}.container{padding:10px}h1{font-size:27px}}
</style>
</head>
<body>
<div class="container">
<div class="hero"><h1>📊 INVEST ANALYZER 5.0</h1><div class="sub">Ações • FIIs • Indicadores • Nota • Risco • Gráficos • Ranking</div></div>
<div class="search"><input id="ticker" value="PETR4" placeholder="PETR4, VALE3, MXRF11, BTLG11, Bitcoin, AAPL..."><button onclick="analisar()">📊 Analisar ativo</button></div>
<div class="buttons">
<button class="secondary" onclick="mercado('acoes')">📈 Ver ações</button>
<button class="secondary" onclick="mercado('fiis')">🏢 Ver FIIs</button>
<button class="secondary" onclick="mercado('oportunidades')">🔥 Oportunidades</button>
<button class="secondary" onclick="mercado('ranking')">🏆 Ranking</button>
<button class="secondary" onclick="atualizar()">🔄 Atualizar</button>
<button class="secondary" onclick="location.href='/exportar-excel'">📊 Exportar Excel</button>
</div>
<div id="status" class="small">Digite um ticker e clique em analisar.</div>
<div id="resultado"></div><div id="mercado" class="panel" style="display:none"></div>
<div class="panel small">⚠️ A Nota, Risco e Conclusão são cálculos automáticos baseados em dados públicos. Não constituem recomendação personalizada de compra ou venda.</div>
</div>
<script>
function money(v){return v==null||isNaN(v)?'N/D':'R$ '+Number(v).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})}
function num(v){return v==null||isNaN(v)?'N/D':Number(v).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})}
function pct(v){return v==null||isNaN(v)?'N/D':Number(v).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+'%'}
function card(a,b,c=''){return `<div class="card"><div class="label">${a}</div><div class="value ${c}">${b}</div></div>`}
async function analisar(){
 const t=document.getElementById('ticker').value.trim();if(!t)return;
 document.getElementById('status').innerText='⏳ Buscando dados...';
 try{
  const r=await fetch('/api/analisar?ticker='+encodeURIComponent(t));const j=await r.json();
  if(!r.ok){document.getElementById('resultado').innerHTML=`<div class="panel">❌ ${j.erro}</div>`;return}
  const d=j.dados,n=d['NOTA FINAL'];
  let html=`<div class="panel"><h2>${d.Nome}</h2><div class="small">Ticker: ${d.Ticker} • Tipo: ${d.Tipo}</div>
  <div class="cardgrid">${card('💰 Preço',money(d['Preço']))}${card('💵 Dividend Yield',pct(d['Dividend Yield (%)']))}
  ${card('⭐ Nota',num(n)+'/10',n>=7?'good':n>=5.5?'warn':'bad')}
  ${card('🛡️ Risco',d.RISCO,d.RISCO.includes('Baixo')||d.RISCO.includes('Moderado')?'good':d.RISCO.includes('Médio')?'warn':'bad')}
  ${card('P/L',num(d['P/L']))}${card('P/VP',num(d['P/VP']))}${card('ROE',pct(d['ROE (%)']))}${card('Dívida/PL',num(d['Dívida/Patrimônio']))}
  ${card('Variação 1A',pct(d['Retorno 1A (%)']))}${card('Volatilidade',pct(d['Volatilidade anual (%)']))}${card('RSI',num(d.RSI))}${card('Beta',num(d.Beta))}</div>
  <h3>🎯 Conclusão: ${d['CONCLUSÃO']}</h3><h3>🚨 Alertas</h3>${d.ALERTAS.map(x=>`<div class="alert">${x}</div>`).join('')}
  <h3>✅ Pontos positivos</h3>${d['PONTOS POSITIVOS'].map(x=>`<div class="alert">${x}</div>`).join('')}</div>
  <div class="panel"><div id="grafico"></div></div><div class="panel"><div id="graficoDiv"></div></div>`;
  document.getElementById('resultado').innerHTML=html;
  Plotly.newPlot('grafico',j.grafico.data,j.grafico.layout,{responsive:true});
  Plotly.newPlot('graficoDiv',j.grafico_dividendos.data,j.grafico_dividendos.layout,{responsive:true});
  document.getElementById('status').innerText='✅ Análise concluída.';
 }catch(e){document.getElementById('resultado').innerHTML='<div class="panel">❌ Erro ao consultar o servidor.</div>';document.getElementById('status').innerText='Erro.'}
}
async function mercado(tipo){
 const el=document.getElementById('mercado');el.style.display='block';el.innerHTML='⏳ Carregando...';document.getElementById('resultado').innerHTML='';
 try{
  const r=await fetch('/api/mercado?tipo='+tipo);const j=await r.json();if(!r.ok){el.innerHTML='❌ '+j.erro;return}
  const cols=Object.keys(j.dados[0]||{});let h=`<h2>${tipo==='acoes'?'📈 Ações':tipo==='fiis'?'🏢 FIIs':tipo==='oportunidades'?'🔥 Oportunidades':'🏆 Ranking'}</h2><div style="overflow:auto"><table><thead><tr>${cols.map(c=>`<th>${c}</th>`).join('')}</tr></thead><tbody>`;
  h+=j.dados.map(x=>'<tr>'+cols.map(c=>`<td>${x[c]??'N/D'}</td>`).join('')+'</tr>').join('');h+='</tbody></table></div>';el.innerHTML=h;
 }catch(e){el.innerHTML='❌ Erro ao carregar mercado.'}
}
async function atualizar(){await fetch('/api/atualizar',{method:'POST'});document.getElementById('status').innerText='🔄 Cache limpo. Os próximos dados serão buscados novamente.'}
document.getElementById('ticker').addEventListener('keydown',e=>{if(e.key==='Enter')analisar()});
</script>
</body></html>
'''


@app.get("/")
def index():
    return render_template_string(HTML)


@app.get("/api/pesquisa")
def api_pesquisa():
    return jsonify({"resultados": pesquisar_ativo(request.args.get("q", ""))})


@app.get("/api/analisar")
def api_analisar():
    ticker = request.args.get("ticker", "")
    if not ticker:
        return jsonify({"erro": "Digite um ticker."}), 400
    d = analisar_ativo(ticker)
    if d is None:
        return jsonify({"erro": f"Não foi possível encontrar ou analisar '{ticker.upper()}'."}), 404
    return jsonify({
        "dados": limpar_para_json(d),
        "grafico": grafico_preco(d),
        "grafico_dividendos": grafico_dividendos(d)
    })


@app.get("/api/mercado")
def api_mercado():
    tipo = request.args.get("tipo", "ranking")

    if tipo == "acoes":
        df = analisar_lista(ACOES_PADRAO)
    elif tipo == "fiis":
        df = analisar_lista(FIIS_PADRAO)
    elif tipo == "oportunidades":
        acoes = analisar_lista(ACOES_PADRAO)
        fiis = analisar_lista(FIIS_PADRAO)
        partes = [x for x in [acoes, fiis] if not x.empty]
        df = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
        if not df.empty:
            df = df[(df["Nota"] >= 7) & (~df["Risco"].str.contains("Alto", na=False))]
            df = df.sort_values("Nota", ascending=False).head(15)
    else:
        acoes = analisar_lista(ACOES_PADRAO)
        fiis = analisar_lista(FIIS_PADRAO)
        if not acoes.empty: acoes["Tipo"] = "Ação"
        if not fiis.empty: fiis["Tipo"] = "FII"
        partes = [x for x in [acoes, fiis] if not x.empty]
        df = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
        if not df.empty:
            colunas = ["Tipo","Ticker","Nome","Preço","DY (%)","P/L","P/VP","ROE (%)","Var. 1A (%)","Nota","Risco","Conclusão"]
            df = df[[c for c in colunas if c in df.columns]].sort_values("Nota", ascending=False)

    if df.empty:
        return jsonify({"erro": "Nenhum ativo foi encontrado agora."}), 503
    df = df.replace({np.nan: None})
    return jsonify({"dados": df.to_dict(orient="records")})


@app.post("/api/atualizar")
def api_atualizar():
    CACHE.clear()
    CACHE_TIME.clear()
    CACHE_SEARCH.clear()
    CACHE_SEARCH_TIME.clear()
    return jsonify({"ok": True, "atualizado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S")})


@app.get("/exportar-excel")
def exportar_excel():
    acoes = analisar_lista(ACOES_PADRAO)
    fiis = analisar_lista(FIIS_PADRAO)
    partes = [x for x in [acoes, fiis] if not x.empty]
    ranking = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()

    oportunidades = pd.DataFrame()
    if not ranking.empty:
        oportunidades = ranking[
            (ranking["Nota"] >= 7) &
            (~ranking["Risco"].str.contains("Alto", na=False))
        ].head(15)

    arquivo = io.BytesIO()
    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        if not acoes.empty: acoes.to_excel(writer, sheet_name="Acoes", index=False)
        if not fiis.empty: fiis.to_excel(writer, sheet_name="FIIs", index=False)
        if not oportunidades.empty: oportunidades.to_excel(writer, sheet_name="Oportunidades", index=False)
        if not ranking.empty: ranking.to_excel(writer, sheet_name="Ranking", index=False)
    arquivo.seek(0)

    return send_file(
        arquivo,
        as_attachment=True,
        download_name="INVEST_ANALYZER_5_0.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
