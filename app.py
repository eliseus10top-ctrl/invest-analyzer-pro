Perfeito. Vou montar uma versão standalone, pensada para o Render, sem Google Colab, sem IPython e sem depender de arquivos HTML externos.
Ela terá:

titulo = "🇧🇷 Ações brasileiras"


🇧🇷 FIIs
🇺🇸 Ações dos EUA
🔎 Busca automática de ticker
💰 Preço atual
📈 Variação diária, semanal, mensal e anual
📊 Médias móveis
📉 RSI
📊 MACD
📈 Volatilidade
💵 Dividend Yield quando disponível
📌 P/L, P/VP e outros fundamentos quando o Yahoo disponibilizar
⭐ Nota automática de 0–10
⚠️ Classificação de risco
🔥 Oportunidades
🏆 Ranking
💼 Carteira
Quantidade
Preço médio
Patrimônio
Lucro/prejuízo
Rentabilidade
📊 Gráficos
📥 Exportação para Excel
📱 Interface responsiva para celular
🛡️ Tratamento de erros do Yahoo Finance
🚀 Compatível com gunicorn app:app no Render
Importante: como você quer colocar diretamente no app.py, o código abaixo não precisa de templates/ nem de static/.
app.py
Substitua todo o conteúdo atual do seu app.py por este:
# ================================================================
# 🚀 INVEST ANALYZER PRO 6.0
# Flask + Yahoo Finance + Carteira + Indicadores + Ranking
# Compatível com Render
# ================================================================

import os
import io
import math
import time
import traceback
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_file, render_template_string

import pandas as pd
import numpy as np
import yfinance as yf


# ================================================================
# CONFIGURAÇÃO
# ================================================================

app = Flask(__name__)

app.config["JSON_SORT_KEYS"] = False

PORT = int(os.environ.get("PORT", 10000))

CACHE = {}
CACHE_TIME = 300  # 5 minutos


# ================================================================
# FUNÇÕES AUXILIARES
# ================================================================

def safe_float(value, default=None):
    try:
        if value is None:
            return default

        if isinstance(value, (float, np.floating)):
            if np.isnan(value) or np.isinf(value):
                return default

        if isinstance(value, str):
            value = value.replace("%", "").replace(",", ".").strip()

        result = float(value)

        if math.isnan(result) or math.isinf(result):
            return default

        return result

    except Exception:
        return default


def clean_number(value, decimals=2):
    value = safe_float(value)

    if value is None:
        return None

    return round(value, decimals)


def money_br(value):
    value = safe_float(value)

    if value is None:
        return "N/D"

    return "R$ {:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")


def money_us(value):
    value = safe_float(value)

    if value is None:
        return "N/D"

    return "$ {:,.2f}".format(value)


def pct(value):
    value = safe_float(value)

    if value is None:
        return "N/D"

    return "{:+.2f}%".format(value)


def normalize_ticker(ticker):
    if not ticker:
        return ""

    ticker = str(ticker).upper().strip()

    ticker = ticker.replace(" ", "")

    # Yahoo Finance Brasil
    if (
        ticker.endswith("11")
        or ticker.endswith("3")
        or ticker.endswith("4")
        or ticker.endswith("5")
        or ticker.endswith("6")
        or ticker.endswith("7")
        or ticker.endswith("8")
    ):
        if not ticker.endswith(".SA"):
            return ticker + ".SA"

    return ticker


def display_ticker(ticker):
    if ticker.endswith(".SA"):
        return ticker[:-3]

    return ticker


def is_brazilian(ticker):
    return ticker.endswith(".SA")


def get_currency(ticker):
    return "BRL" if is_brazilian(ticker) else "USD"


# ================================================================
# CACHE
# ================================================================

def cache_get(key):
    item = CACHE.get(key)

    if not item:
        return None

    timestamp, data = item

    if time.time() - timestamp > CACHE_TIME:
        CACHE.pop(key, None)
        return None

    return data


def cache_set(key, data):
    CACHE[key] = (time.time(), data)


# ================================================================
# DOWNLOAD YAHOO FINANCE
# ================================================================

def download_history(ticker, period="1y", interval="1d"):

    cache_key = f"HISTORY:{ticker}:{period}:{interval}"

    cached = cache_get(cache_key)

    if cached is not None:
        return cached

    try:
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if data is None or data.empty:
            return pd.DataFrame()

        # Corrige MultiIndex do yfinance
        if isinstance(data.columns, pd.MultiIndex):
            try:
                data.columns = data.columns.get_level_values(0)
            except Exception:
                data.columns = [
                    c[0] if isinstance(c, tuple) else c
                    for c in data.columns
                ]

        data = data.copy()

        required = ["Open", "High", "Low", "Close", "Volume"]

        for col in required:
            if col not in data.columns:
                data[col] = np.nan

        data = data.dropna(subset=["Close"])

        cache_set(cache_key, data)

        return data

    except Exception:
        return pd.DataFrame()


# ================================================================
# INDICADORES
# ================================================================

def calculate_rsi(series, period=14):

    try:
        delta = series.diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)

        rsi = 100 - (100 / (1 + rs))

        return rsi

    except Exception:
        return pd.Series(index=series.index, dtype=float)


def calculate_macd(series):

    try:
        ema12 = series.ewm(span=12, adjust=False).mean()
        ema26 = series.ewm(span=26, adjust=False).mean()

        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()

        histogram = macd - signal

        return macd, signal, histogram

    except Exception:
        empty = pd.Series(index=series.index, dtype=float)
        return empty, empty, empty


def calculate_indicators(data):

    if data.empty:
        return {}

    close = data["Close"]

    try:
        current = safe_float(close.iloc[-1])

        previous = safe_float(close.iloc[-2]) if len(close) >= 2 else None

        week = safe_float(close.iloc[-6]) if len(close) >= 6 else None

        month = safe_float(close.iloc[-22]) if len(close) >= 22 else None

        year = safe_float(close.iloc[0]) if len(close) > 1 else None

        daily_change = (
            ((current / previous) - 1) * 100
            if current is not None and previous not in (None, 0)
            else None
        )

        weekly_change = (
            ((current / week) - 1) * 100
            if current is not None and week not in (None, 0)
            else None
        )

        monthly_change = (
            ((current / month) - 1) * 100
            if current is not None and month not in (None, 0)
            else None
        )

        yearly_change = (
            ((current / year) - 1) * 100
            if current is not None and year not in (None, 0)
            else None
        )

        sma20 = close.rolling(20).mean()
        sma50 = close.rolling(50).mean()
        sma200 = close.rolling(200).mean()

        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()

        rsi = calculate_rsi(close)

        macd, signal, histogram = calculate_macd(close)

        returns = close.pct_change().dropna()

        volatility = (
            float(returns.std() * np.sqrt(252) * 100)
            if len(returns) > 10
            else None
        )

        high52 = safe_float(close.max())

        low52 = safe_float(close.min())

        distance_high = (
            ((current / high52) - 1) * 100
            if current is not None and high52 not in (None, 0)
            else None
        )

        distance_low = (
            ((current / low52) - 1) * 100
            if current is not None and low52 not in (None, 0)
            else None
        )

        result = {
            "current": clean_number(current),
            "previous": clean_number(previous),

            "daily_change": clean_number(daily_change),
            "weekly_change": clean_number(weekly_change),
            "monthly_change": clean_number(monthly_change),
            "yearly_change": clean_number(yearly_change),

            "sma20": clean_number(sma20.iloc[-1]),
            "sma50": clean_number(sma50.iloc[-1]),
            "sma200": clean_number(sma200.iloc[-1]),

            "ema20": clean_number(ema20.iloc[-1]),
            "ema50": clean_number(ema50.iloc[-1]),

            "rsi": clean_number(rsi.iloc[-1]),

            "macd": clean_number(macd.iloc[-1]),
            "macd_signal": clean_number(signal.iloc[-1]),
            "macd_histogram": clean_number(histogram.iloc[-1]),

            "volatility": clean_number(volatility),

            "high52": clean_number(high52),
            "low52": clean_number(low52),

            "distance_high": clean_number(distance_high),
            "distance_low": clean_number(distance_low),
        }

        return result

    except Exception:
        return {}


# ================================================================
# FUNDAMENTOS
# ================================================================

def get_fundamentals(ticker):

    cache_key = f"FUND:{ticker}"

    cached = cache_get(cache_key)

    if cached is not None:
        return cached

    result = {
        "name": display_ticker(ticker),
        "long_name": display_ticker(ticker),

        "sector": "N/D",
        "industry": "N/D",

        "market_cap": None,

        "pe": None,
        "forward_pe": None,

        "pb": None,

        "eps": None,

        "dividend_yield": None,
        "dividend_rate": None,

        "profit_margin": None,
        "roe": None,

        "debt_to_equity": None,

        "revenue_growth": None,
        "earnings_growth": None,

        "target_mean": None,

        "52w_high": None,
        "52w_low": None,

        "currency": get_currency(ticker)
    }

    try:
        info = {}

        try:
            info = yf.Ticker(ticker).info
        except Exception:
            info = {}

        if not isinstance(info, dict):
            info = {}

        result["long_name"] = (
            info.get("longName")
            or info.get("shortName")
            or display_ticker(ticker)
        )

        result["sector"] = info.get("sector") or "N/D"

        result["industry"] = info.get("industry") or "N/D"

        result["market_cap"] = safe_float(info.get("marketCap"))

        result["pe"] = safe_float(
            info.get("trailingPE")
        )

        result["forward_pe"] = safe_float(
            info.get("forwardPE")
        )

        result["pb"] = safe_float(
            info.get("priceToBook")
        )

        result["eps"] = safe_float(
            info.get("trailingEps")
        )

        dividend = info.get("dividendYield")

        if dividend is not None:

            dividend = safe_float(dividend)

            if dividend is not None:

                # Yahoo pode retornar 0.05 = 5%
                if abs(dividend) < 1:
                    dividend *= 100

        result["dividend_yield"] = dividend

        result["dividend_rate"] = safe_float(
            info.get("dividendRate")
        )

        margin = safe_float(info.get("profitMargins"))

        if margin is not None and abs(margin) < 1:
            margin *= 100

        result["profit_margin"] = margin

        roe = safe_float(info.get("returnOnEquity"))

        if roe is not None and abs(roe) < 1:
            roe *= 100

        result["roe"] = roe

        result["debt_to_equity"] = safe_float(
            info.get("debtToEquity")
        )

        growth = safe_float(info.get("revenueGrowth"))

        if growth is not None and abs(growth) < 1:
            growth *= 100

        result["revenue_growth"] = growth

        growth2 = safe_float(info.get("earningsGrowth"))

        if growth2 is not None and abs(growth2) < 1:
            growth2 *= 100

        result["earnings_growth"] = growth2

        result["target_mean"] = safe_float(
            info.get("targetMeanPrice")
        )

        result["52w_high"] = safe_float(
            info.get("fiftyTwoWeekHigh")
        )

        result["52w_low"] = safe_float(
            info.get("fiftyTwoWeekLow")
        )

        cache_set(cache_key, result)

        return result

    except Exception:

        return result


# ================================================================
# NOTA
# ================================================================

def calculate_score(indicators, fundamentals):

    score = 5.0

    # ------------------------------------------------------------
    # Tendência
    # ------------------------------------------------------------

    current = safe_float(indicators.get("current"))

    sma20 = safe_float(indicators.get("sma20"))
    sma50 = safe_float(indicators.get("sma50"))
    sma200 = safe_float(indicators.get("sma200"))

    if current and sma20:
        score += 0.5 if current > sma20 else -0.5

    if current and sma50:
        score += 0.5 if current > sma50 else -0.5

    if current and sma200:
        score += 0.7 if current > sma200 else -0.7

    # ------------------------------------------------------------
    # RSI
    # ------------------------------------------------------------

    rsi = safe_float(indicators.get("rsi"))

    if rsi is not None:

        if 45 <= rsi <= 65:
            score += 0.6

        elif 35 <= rsi < 45:
            score += 0.2

        elif rsi > 75:
            score -= 0.8

        elif rsi < 25:
            score += 0.3

    # ------------------------------------------------------------
    # MACD
    # ------------------------------------------------------------

    histogram = safe_float(
        indicators.get("macd_histogram")
    )

    if histogram is not None:

        if histogram > 0:
            score += 0.5
        else:
            score -= 0.3

    # ------------------------------------------------------------
    # Crescimento
    # ------------------------------------------------------------

    revenue_growth = safe_float(
        fundamentals.get("revenue_growth")
    )

    if revenue_growth is not None:

        if revenue_growth > 15:
            score += 0.6

        elif revenue_growth > 5:
            score += 0.3

        elif revenue_growth < -10:
            score -= 0.5

    # ------------------------------------------------------------
    # ROE
    # ------------------------------------------------------------

    roe = safe_float(
        fundamentals.get("roe")
    )

    if roe is not None:

        if roe > 20:
            score += 0.7

        elif roe > 10:
            score += 0.3

        elif roe < 0:
            score -= 0.6

    # ------------------------------------------------------------
    # P/L
    # ------------------------------------------------------------

    pe = safe_float(
        fundamentals.get("pe")
    )

    if pe is not None and pe > 0:

        if pe < 10:
            score += 0.5

        elif pe < 18:
            score += 0.3

        elif pe > 35:
            score -= 0.6

        elif pe > 50:
            score -= 1.0

    # ------------------------------------------------------------
    # Dívida
    # ------------------------------------------------------------

    debt = safe_float(
        fundamentals.get("debt_to_equity")
    )

    if debt is not None:

        if debt < 50:
            score += 0.3

        elif debt > 200:
            score -= 0.6

    # ------------------------------------------------------------
    # Limite
    # ------------------------------------------------------------

    score = max(0, min(10, score))

    return round(score, 1)


# ================================================================
# RISCO
# ================================================================

def calculate_risk(indicators):

    volatility = safe_float(
        indicators.get("volatility")
    )

    rsi = safe_float(
        indicators.get("rsi")
    )

    if volatility is None:
        return "Indeterminado"

    risk_points = 0

    if volatility < 15:
        risk_points += 0

    elif volatility < 30:
        risk_points += 1

    elif volatility < 50:
        risk_points += 2

    else:
        risk_points += 3

    if rsi is not None:

        if rsi > 75:
            risk_points += 1

        if rsi < 20:
            risk_points += 1

    if risk_points <= 0:
        return "Baixo"

    if risk_points <= 2:
        return "Moderado"

    if risk_points <= 4:
        return "Alto"

    return "Muito alto"


# ================================================================
# SINAL
# ================================================================

def calculate_signal(indicators, score):

    current = safe_float(indicators.get("current"))
    sma20 = safe_float(indicators.get("sma20"))
    sma50 = safe_float(indicators.get("sma50"))
    sma200 = safe_float(indicators.get("sma200"))

    rsi = safe_float(indicators.get("rsi"))

    macd_hist = safe_float(
        indicators.get("macd_histogram")
    )

    points = 0

    if current and sma20:
        points += 1 if current > sma20 else -1

    if current and sma50:
        points += 1 if current > sma50 else -1

    if current and sma200:
        points += 1 if current > sma200 else -1

    if macd_hist is not None:
        points += 1 if macd_hist > 0 else -1

    if rsi is not None:

        if 40 <= rsi <= 70:
            points += 1

        elif rsi > 80:
            points -= 1

    if score >= 8 and points >= 2:
        return "Forte"

    if score >= 7 and points >= 1:
        return "Positivo"

    if score <= 4 and points <= -2:
        return "Fraco"

    if score <= 5:
        return "Neutro"

    return "Positivo"


# ================================================================
# ANÁLISE COMPLETA
# ================================================================

def analyze_asset(raw_ticker):

    ticker = normalize_ticker(raw_ticker)

    if not ticker:
        return {
            "ok": False,
            "error": "Digite um ticker."
        }

    try:

        history = download_history(
            ticker,
            period="1y",
            interval="1d"
        )

        if history.empty:

            # Tenta novamente como EUA
            ticker2 = str(raw_ticker).upper().strip()

            history = download_history(
                ticker2,
                period="1y",
                interval="1d"
            )

            if not history.empty:
                ticker = ticker2

        if history.empty:

            return {
                "ok": False,
                "error": (
                    f"Não foi possível encontrar {raw_ticker}. "
                    "Verifique o código do ativo."
                )
            }

        indicators = calculate_indicators(history)

        fundamentals = get_fundamentals(ticker)

        score = calculate_score(
            indicators,
            fundamentals
        )

        risk = calculate_risk(
            indicators
        )

        signal = calculate_signal(
            indicators,
            score
        )

        # --------------------------------------------------------
        # Dados para gráfico
        # --------------------------------------------------------

        chart = []

        try:

            recent = history.tail(180)

            for index, row in recent.iterrows():

                try:

                    date = index.strftime("%Y-%m-%d")

                    close = safe_float(
                        row["Close"]
                    )

                    if close is not None:

                        chart.append({
                            "date": date,
                            "close": round(close, 4)
                        })

                except Exception:
                    continue

        except Exception:
            chart = []

        result = {

            "ok": True,

            "ticker": display_ticker(ticker),

            "yahoo_ticker": ticker,

            "name": fundamentals.get(
                "long_name"
            ),

            "currency": fundamentals.get(
                "currency"
            ),

            "fundamentals": fundamentals,

            "indicators": indicators,

            "score": score,

            "risk": risk,

            "signal": signal,

            "chart": chart,

            "updated_at": datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            )
        }

        return result

    except Exception as error:

        traceback.print_exc()

        return {
            "ok": False,
            "error": f"Erro ao analisar ativo: {str(error)}"
        }


# ================================================================
# BANCO TEMPORÁRIO DA CARTEIRA
# ================================================================
# Em Render, este armazenamento é temporário.
# Para uma carteira permanente por usuário, será necessário banco
# de dados/login posteriormente.

portfolio = []


# ================================================================
# PÁGINA HTML
# ================================================================

HTML = r"""
<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Invest Analyzer Pro 6.0</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background: #0b0d12;

    color: #f4f4f5;
}

header {
    padding: 22px 16px;

    background:
        linear-gradient(
            135deg,
            #111827,
            #0b0d12
        );

    border-bottom:
        1px solid #252a36;
}

.logo {
    max-width: 1200px;

    margin: auto;
}

.logo h1 {
    margin: 0;

    font-size: 28px;
}

.logo p {
    color: #9ca3af;

    margin:
        7px 0 0;
}

.container {

    width: 100%;

    max-width: 1200px;

    margin: auto;

    padding: 20px 14px 50px;
}

.search-box {

    background: #151923;

    border:
        1px solid #2b3240;

    border-radius: 20px;

    padding: 16px;

    margin-bottom: 18px;
}

.search-row {

    display: flex;

    gap: 10px;
}

input {

    flex: 1;

    min-width: 0;

    background: #1b202b;

    border:
        1px solid #353d4c;

    border-radius: 14px;

    padding: 17px;

    color: white;

    font-size: 17px;

    outline: none;
}

input:focus {
    border-color: #3b82f6;
}

button {

    border: 0;

    border-radius: 14px;

    padding: 15px 20px;

    background: #2f80ed;

    color: white;

    font-weight: bold;

    font-size: 15px;

    cursor: pointer;
}

button:hover {
    opacity: 0.9;
}

.btn-dark {
    background: #202633;
}

.btn-green {
    background: #159957;
}

.btn-red {
    background: #b83232;
}

.quick-grid {

    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 12px;

    margin-bottom: 18px;
}

.card {

    background: #171b24;

    border:
        1px solid #292f3b;

    border-radius: 20px;

    padding: 20px;

    box-shadow:
        0 10px 25px
        rgba(0,0,0,.12);
}

.quick-card {

    text-align: center;

    cursor: pointer;

    transition: .2s;
}

.quick-card:hover {
    transform: translateY(-2px);
}

.quick-icon {
    font-size: 28px;

    margin-bottom: 8px;
}

.quick-title {
    font-weight: bold;

    font-size: 16px;
}

h2 {
    margin-top: 0;
}

.section {
    margin-top: 18px;
}

.status {

    display: none;

    padding: 15px;

    margin-bottom: 16px;

    border-radius: 14px;

    background: #202633;

    color: #d1d5db;
}

.asset-header {

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 15px;
}

.ticker {
    font-size: 30px;

    font-weight: 800;
}

.asset-name {
    color: #9ca3af;

    margin-top: 5px;
}

.price {

    font-size: 30px;

    font-weight: 800;

    text-align: right;
}

.badge {

    display: inline-block;

    padding: 6px 10px;

    border-radius: 999px;

    font-size: 12px;

    font-weight: bold;

    margin-top: 8px;
}

.badge-green {
    background: #123d2a;

    color: #6ee7a8;
}

.badge-yellow {
    background: #453a12;

    color: #facc15;
}

.badge-red {
    background: #481d23;

    color: #f87171;
}

.stats {

    display: grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap: 12px;

    margin-top: 15px;
}

.stat {

    background: #10141c;

    padding: 15px;

    border-radius: 15px;

    border:
        1px solid #252b36;
}

.stat-label {

    color: #9ca3af;

    font-size: 13px;

    margin-bottom: 7px;
}

.stat-value {

    font-size: 19px;

    font-weight: bold;
}

.green {
    color: #4ade80;
}

.red {
    color: #f87171;
}

.yellow {
    color: #facc15;
}

.blue {
    color: #60a5fa;
}

.score {

    display: flex;

    align-items: center;

    justify-content: center;

    width: 100px;

    height: 100px;

    border-radius: 50%;

    border: 7px solid #2f80ed;

    font-size: 27px;

    font-weight: bold;
}

.score-box {

    display: flex;

    align-items: center;

    gap: 20px;
}

.grid {

    display: grid;

    grid-template-columns:
        repeat(2, 1fr);

    gap: 15px;
}

table {

    width: 100%;

    border-collapse: collapse;

    min-width: 700px;
}

.table-wrapper {

    overflow-x: auto;

    width: 100%;
}

th, td {

    padding: 13px 10px;

    border-bottom:
        1px solid #292f3b;

    text-align: left;
}

th {
    color: #9ca3af;

    font-size: 13px;
}

td {
    font-size: 14px;
}

.chart {

    width: 100%;

    height: 330px;

    background: #10141c;

    border-radius: 15px;

    padding: 10px;
}

canvas {

    width: 100% !important;

    height: 100% !important;
}

.portfolio-form {

    display: grid;

    grid-template-columns:
        1fr 1fr 1fr auto;

    gap: 10px;
}

.empty {

    padding: 30px;

    text-align: center;

    color: #9ca3af;
}

.loading {

    text-align: center;

    padding: 25px;

    color: #60a5fa;
}

.footer {

    text-align: center;

    color: #6b7280;

    font-size: 12px;

    padding: 30px 10px;
}

.disclaimer {

    background: #221d10;

    border:
        1px solid #54451c;

    color: #d6c98b;

    padding: 15px;

    border-radius: 15px;

    font-size: 13px;

    line-height: 1.5;

    margin-top: 20px;
}

@media (max-width: 850px) {

    .quick-grid {
        grid-template-columns:
            repeat(2, 1fr);
    }

    .stats {
        grid-template-columns:
            repeat(2, 1fr);
    }

    .grid {
        grid-template-columns: 1fr;
    }

    .portfolio-form {
        grid-template-columns: 1fr;
    }

    .search-row {
        flex-direction: column;
    }

    .asset-header {
        flex-direction: column;

        align-items: flex-start;
    }

    .price {
        text-align: left;
    }
}

@media (max-width: 500px) {

    .container {
        padding-left: 10px;
        padding-right: 10px;
    }

    header {
        padding: 18px 12px;
    }

    .logo h1 {
        font-size: 23px;
    }

    .quick-grid {
        gap: 9px;
    }

    .card {
        padding: 15px;
        border-radius: 16px;
    }

    .ticker {
        font-size: 25px;
    }

    .price {
        font-size: 26px;
    }

    .stats {
        gap: 8px;
    }

    .stat {
        padding: 12px;
    }

    .stat-value {
        font-size: 16px;
    }

}

</style>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

</head>

<body>

<header>

<div class="logo">

<h1>📊 Invest Analyzer Pro</h1>

<p>
Análise de ações, FIIs e mercado internacional
</p>

</div>

</header>


<div class="container">


<div class="search-box">

<div class="search-row">

<input
    id="ticker"
    placeholder="Digite o ativo. Ex.: PETR4, VALE3, MXRF11, AAPL"
    autocomplete="off"
>

<button onclick="analyze()">
📊 Analisar ativo
</button>

</div>

</div>


<div class="quick-grid">

<div class="card quick-card"
     onclick="analyzeTicker('PETR4')">

<div class="quick-icon">📈</div>

<div class="quick-title">
Ações
</div>

</div>


<div class="card quick-card"
     onclick="analyzeTicker('MXRF11')">

<div class="quick-icon">🏢</div>

<div class="quick-title">
FIIs
</div>

</div>


<div class="card quick-card"
     onclick="showOpportunities()">

<div class="quick-icon">🔥</div>

<div class="quick-title">
Oportunidades
</div>

</div>


<div class="card quick-card"
     onclick="showRanking()">

<div class="quick-icon">🏆</div>

<div class="quick-title">
Ranking
</div>

</div>


<div class="card quick-card"
     onclick="location.reload()">

<div class="quick-icon">🔄</div>

<div class="quick-title">
Atualizar
</div>

</div>


<div class="card quick-card"
     onclick="exportExcel()">

<div class="quick-icon">📊</div>

<div class="quick-title">
Exportar Excel
</div>

</div>

</div>


<div id="status" class="status"></div>


<div id="result"></div>


<div id="portfolio" class="section">

<div class="card">

<h2>💼 Minha Carteira</h2>

<div class="portfolio-form">

<input
    id="pTicker"
    placeholder="Ticker: PETR4"
>

<input
    id="pQty"
    type="number"
    step="0.0001"
    placeholder="Quantidade"
>

<input
    id="pPrice"
    type="number"
    step="0.01"
    placeholder="Preço médio"
>

<button
    class="btn-green"
    onclick="addPortfolio()">

Adicionar

</button>

</div>

<div id="portfolioResult"
     style="margin-top:20px">

<div class="empty">
Sua carteira está vazia.
</div>

</div>

</div>

</div>


<div class="disclaimer">

⚠️ <b>Aviso:</b>
Os dados são obtidos de fontes públicas, principalmente
Yahoo Finance. As informações podem apresentar atraso,
indisponibilidade ou inconsistências. A nota, risco e sinais
são indicadores automatizados e não constituem recomendação
de compra ou venda.

</div>


<div class="footer">

Invest Analyzer Pro 6.0
<br>
Dados financeiros para fins informativos.

</div>

</div>


<script>

let currentChart = null;


function showStatus(message) {

    const box = document.getElementById("status");

    box.style.display = "block";

    box.innerHTML = message;

}


function hideStatus() {

    document.getElementById("status").style.display = "none";

}


function analyzeTicker(ticker) {

    document.getElementById("ticker").value = ticker;

    analyze();

}


async function analyze() {

    const input =
        document.getElementById("ticker");

    const ticker =
        input.value.trim();

    if (!ticker) {

        showStatus(
            "⚠️ Digite um ticker para analisar."
        );

        return;
    }

    showStatus(
        "🔄 Consultando Yahoo Finance..."
    );

    document.getElementById("result").innerHTML =
        '<div class="card loading">⏳ Analisando ativo...</div>';

    try {

        const response = await fetch(
            "/api/analyze?ticker=" +
            encodeURIComponent(ticker)
        );

        const data = await response.json();

        if (!data.ok) {

            document.getElementById("result").innerHTML =
                '<div class="card">' +
                '❌ ' + escapeHtml(data.error) +
                '</div>';

            return;
        }

        hideStatus();

        renderAnalysis(data);

    } catch (error) {

        document.getElementById("result").innerHTML =
            '<div class="card">' +
            '❌ Erro de comunicação com o servidor.' +
            '</div>';

    }

}


function escapeHtml(text) {

    if (text === null ||
        text === undefined) {

        return "";

    }

    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function formatMoney(value, currency) {

    if (value === null ||
        value === undefined) {

        return "N/D";
    }

    const symbol =
        currency === "USD"
        ? "$"
        : "R$";

    return symbol + " " +
        Number(value).toLocaleString(
            "pt-BR",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        );
}


function formatPercent(value) {

    if (value === null ||
        value === undefined) {

        return "N/D";
    }

    const n = Number(value);

    return (
        n >= 0 ? "+" : ""
    ) +
    n.toFixed(2) +
    "%";
}


function colorClass(value) {

    if (value === null ||
        value === undefined) {

        return "";
    }

    return Number(value) >= 0
        ? "green"
        : "red";
}


function renderAnalysis(data) {

    const i = data.indicators;

    const f = data.fundamentals;

    const currency = data.currency;

    const score = Number(data.score || 0);

    let scoreClass = "badge-yellow";

    if (score >= 7) {
        scoreClass = "badge-green";
    }

    if (score <= 4) {
        scoreClass = "badge-red";
    }

    let riskClass =
        data.risk === "Baixo"
        ? "badge-green"
        : "badge-yellow";

    if (
        data.risk === "Alto" ||
        data.risk === "Muito alto"
    ) {
        riskClass = "badge-red";
    }

    document.getElementById("result").innerHTML = `

    <div class="card section">

        <div class="asset-header">

            <div>

                <div class="ticker">
                    ${escapeHtml(data.ticker)}
                </div>

                <div class="asset-name">
                    ${escapeHtml(data.name)}
                </div>

                <span class="badge ${scoreClass}">
                    ⭐ Nota ${score}/10
                </span>

                <span class="badge ${riskClass}">
                    ⚠️ ${escapeHtml(data.risk)}
                </span>

                <span class="badge badge-green">
                    📌 ${escapeHtml(data.signal)}
                </span>

            </div>


            <div>

                <div class="price">

                    ${formatMoney(
                        i.current,
                        currency
                    )}

                </div>

                <div class="${colorClass(i.daily_change)}">

                    ${formatPercent(
                        i.daily_change
                    )}

                    hoje

                </div>

            </div>

        </div>


        <div class="stats">

            ${stat(
                "1 semana",
                formatPercent(i.weekly_change),
                colorClass(i.weekly_change)
            )}

            ${stat(
                "1 mês",
                formatPercent(i.monthly_change),
                colorClass(i.monthly_change)
            )}

            ${stat(
                "1 ano",
                formatPercent(i.yearly_change),
                colorClass(i.yearly_change)
            )}

            ${stat(
                "Volatilidade",
                i.volatility !== null
                    ? Number(i.volatility).toFixed(2) + "%"
                    : "N/D"
            )}

        </div>

    </div>


    <div class="grid section">


        <div class="card">

            <h2>📈 Tendência</h2>

            <div class="stats">

                ${stat(
                    "Média 20",
                    formatMoney(
                        i.sma20,
                        currency
                    )
                )}

                ${stat(
                    "Média 50",
                    formatMoney(
                        i.sma50,
                        currency
                    )
                )}

                ${stat(
                    "Média 200",
                    formatMoney(
                        i.sma200,
                        currency
                    )
                )}

                ${stat(
                    "RSI",
                    i.rsi !== null
                        ? Number(i.rsi).toFixed(2)
                        : "N/D"
                )}

            </div>

        </div>


        <div class="card">

            <h2>📊 MACD</h2>

            <div class="stats">

                ${stat(
                    "MACD",
                    i.macd !== null
                        ? Number(i.macd).toFixed(4)
                        : "N/D"
                )}

                ${stat(
                    "Sinal",
                    i.macd_signal !== null
                        ? Number(i.macd_signal).toFixed(4)
                        : "N/D"
                )}

                ${stat(
                    "Histograma",
                    i.macd_histogram !== null
                        ? Number(i.macd_histogram).toFixed(4)
                        : "N/D"
                )}

                ${stat(
                    "Distância máxima",
                    formatPercent(i.distance_high)
                )}

            </div>

        </div>


    </div>


    <div class="card section">

        <h2>📉 Gráfico — últimos meses</h2>

        <div class="chart">

            <canvas id="priceChart"></canvas>

        </div>

    </div>


    <div class="card section">

        <h2>💰 Fundamentos</h2>

        <div class="table-wrapper">

        <table>

            <thead>

                <tr>

                    <th>Indicador</th>
                    <th>Valor</th>

                </tr>

            </thead>

            <tbody>

                <tr>
                    <td>Setor</td>
                    <td>${escapeHtml(f.sector)}</td>
                </tr>

                <tr>
                    <td>Indústria</td>
                    <td>${escapeHtml(f.industry)}</td>
                </tr>

                <tr>
                    <td>Capitalização</td>
                    <td>${formatLargeNumber(f.market_cap)}</td>
                </tr>

                <tr>
                    <td>P/L</td>
                    <td>${formatValue(f.pe)}</td>
                </tr>

                <tr>
                    <td>P/VP</td>
                    <td>${formatValue(f.pb)}</td>
                </tr>

                <tr>
                    <td>EPS/LPA</td>
                    <td>${formatValue(f.eps)}</td>
                </tr>

                <tr>
                    <td>Dividend Yield</td>
                    <td>${formatPercent(f.dividend_yield)}</td>
                </tr>

                <tr>
                    <td>ROE</td>
                    <td>${formatPercent(f.roe)}</td>
                </tr>

                <tr>
                    <td>Margem de lucro</td>
                    <td>${formatPercent(f.profit_margin)}</td>
                </tr>

                <tr>
                    <td>Crescimento receita</td>
                    <td>${formatPercent(f.revenue_growth)}</td>
                </tr>

                <tr>
                    <td>Crescimento lucro</td>
                    <td>${formatPercent(f.earnings_growth)}</td>
                </tr>

                <tr>
                    <td>Dívida/Patrimônio</td>
                    <td>${formatValue(f.debt_to_equity)}</td>
                </tr>

            </tbody>

        </table>

        </div>

    </div>


    <div class="card section">

        <h2>🎯 Faixa de preço</h2>

        <div class="stats">

            ${stat(
                "Mínima 1 ano",
                formatMoney(
                    i.low52,
                    currency
                )
            )}

            ${stat(
                "Máxima 1 ano",
                formatMoney(
                    i.high52,
                    currency
                )
            )}

            ${stat(
                "Distância da máxima",
                formatPercent(i.distance_high)
            )}

            ${stat(
                "Distância da mínima",
                formatPercent(i.distance_low)
            )}

        </div>

    </div>

    `;


    renderChart(data.chart);

}


function stat(label, value, cls="") {

    return `

        <div class="stat">

            <div class="stat-label">
                ${escapeHtml(label)}
            </div>

            <div class="stat-value ${cls}">
                ${escapeHtml(value)}
            </div>

        </div>

    `;

}


function formatValue(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "N/D";
    }

    const n = Number(value);

    if (!Number.isFinite(n)) {
        return "N/D";
    }

    return n.toFixed(2);

}


function formatLargeNumber(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "N/D";
    }

    const n = Number(value);

    if (!Number.isFinite(n)) {
        return "N/D";
    }

    if (n >= 1e12) {
        return (
            (n / 1e12).toFixed(2)
            + " tri"
        );
    }

    if (n >= 1e9) {
        return (
            (n / 1e9).toFixed(2)
            + " bi"
        );
    }

    if (n >= 1e6) {
        return (
            (n / 1e6).toFixed(2)
            + " mi"
        );
    }

    return n.toLocaleString(
        "pt-BR"
    );

}


function renderChart(points) {

    const canvas =
        document.getElementById(
            "priceChart"
        );

    if (!canvas) {
        return;
    }

    if (currentChart) {
        currentChart.destroy();
    }

    const labels =
        points.map(
            x => x.date
        );

    const values =
        points.map(
            x => x.close
        );

    currentChart =
        new Chart(
            canvas.getContext("2d"),
            {

                type: "line",

                data: {

                    labels: labels,

                    datasets: [{

                        label: "Preço",

                        data: values,

                        tension: 0.25,

                        pointRadius: 0,

                        borderWidth: 2,

                        fill: false

                    }]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        legend: {
                            display: false
                        }

                    },

                    scales: {

                        x: {
                            ticks: {
                                maxTicksLimit: 8
                            }
                        },

                        y: {

                            ticks: {

                                callback:
                                    function(value) {

                                        return Number(
                                            value
                                        ).toLocaleString(
                                            "pt-BR",
                                            {
                                                maximumFractionDigits: 2
                                            }
                                        );

                                    }

                            }

                        }

                    }

                }

            }
        );

}


async function addPortfolio() {

    const ticker =
        document
        .getElementById("pTicker")
        .value
        .trim();

    const quantity =
        document
        .getElementById("pQty")
        .value;

    const price =
        document
        .getElementById("pPrice")
        .value;

    if (
        !ticker ||
        !quantity ||
        !price
    ) {

        alert(
            "Preencha ticker, quantidade e preço médio."
        );

        return;
    }

    try {

        const response =
            await fetch(
                "/api/portfolio",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        ticker: ticker,

                        quantity:
                            Number(quantity),

                        price:
                            Number(price)

                    })

                }
            );

        const data =
            await response.json();

        if (!data.ok) {

            alert(data.error);

            return;
        }

        document
            .getElementById("pTicker")
            .value = "";

        document
            .getElementById("pQty")
            .value = "";

        document
            .getElementById("pPrice")
            .value = "";

        renderPortfolio(
            data.portfolio
        );

    } catch (error) {

        alert(
            "Erro ao adicionar ativo."
        );

    }

}


async function loadPortfolio() {

    try {

        const response =
            await fetch(
                "/api/portfolio"
            );

        const data =
            await response.json();

        renderPortfolio(
            data.portfolio
        );

    } catch (error) {

        console.log(error);

    }

}


function renderPortfolio(items) {

    const container =
        document.getElementById(
            "portfolioResult"
        );

    if (!items || items.length === 0) {

        container.innerHTML =
            '<div class="empty">' +
            'Sua carteira está vazia.' +
            '</div>';

        return;
    }

    let totalInvested = 0;

    let totalCurrent = 0;

    let rows = "";

    for (
        const item of items
    ) {

        const invested =
            item.quantity *
            item.average_price;

        const current =
            item.current_price !== null
            ? item.quantity *
              item.current_price
            : null;

        totalInvested +=
            invested;

        if (current !== null) {
            totalCurrent += current;
        }

        const profit =
            current !== null
            ? current - invested
            : null;

        rows += `

        <tr>

            <td>
                <b>${escapeHtml(item.ticker)}</b>
            </td>

            <td>
                ${Number(
                    item.quantity
                ).toLocaleString(
                    "pt-BR"
                )}
            </td>

            <td>
                ${formatMoney(
                    item.average_price,
                    item.currency
                )}
            </td>

            <td>
                ${formatMoney(
                    item.current_price,
                    item.currency
                )}
            </td>

            <td class="${
                profit !== null
                ? (
                    profit >= 0
                    ? "green"
                    : "red"
                )
                : ""
            }">

                ${
                    profit !== null
                    ? formatMoney(
                        profit,
                        item.currency
                    )
                    : "N/D"
                }

            </td>

            <td>

                <button
                    class="btn-red"
                    onclick="removePortfolio(
                        '${encodeURIComponent(item.ticker)}'
                    )">

                    Excluir

                </button>

            </td>

        </tr>

        `;

    }


    const profit =
        totalCurrent - totalInvested;


    container.innerHTML = `

        <div class="stats">

            ${stat(
                "Investido",
                formatMoney(
                    totalInvested,
                    "BRL"
                )
            )}

            ${stat(
                "Patrimônio",
                formatMoney(
                    totalCurrent,
                    "BRL"
                )
            )}

            ${stat(
                "Lucro/Prejuízo",
                formatMoney(
                    profit,
                    "BRL"
                ),
                profit >= 0
                ? "green"
                : "red"
            )}

        </div>


        <div
            class="table-wrapper"
            style="margin-top:20px"
        >

            <table>

                <thead>

                    <tr>

                        <th>Ativo</th>
                        <th>Qtd.</th>
                        <th>Preço médio</th>
                        <th>Preço atual</th>
                        <th>Resultado</th>
                        <th>Ação</th>

                    </tr>

                </thead>

                <tbody>

                    ${rows}

                </tbody>

            </table>

        </div>

    `;

}


async function removePortfolio(ticker) {

    if (
        !confirm(
            "Deseja excluir este ativo da carteira?"
        )
    ) {
        return;
    }

    try {

        const response =
            await fetch(
                "/api/portfolio/" +
                ticker,
                {
                    method: "DELETE"
                }
            );

        const data =
            await response.json();

        renderPortfolio(
            data.portfolio
        );

    } catch (error) {

        alert(
            "Erro ao excluir ativo."
        );

    }

}


async function showRanking() {

    showStatus(
        "🏆 Calculando ranking..."
    );

    try {

        const response =
            await fetch(
                "/api/ranking"
            );

        const data =
            await response.json();

        if (!data.ok) {

            showStatus(
                "❌ " + data.error
            );

            return;
        }

        hideStatus();

        let rows = "";

        for (
            let i = 0;
            i < data.items.length;
            i++
        ) {

            const item =
                data.items[i];

            rows += `

                <tr>

                    <td>
                        <b>${i + 1}º</b>
                    </td>

                    <td>
                        ${escapeHtml(
                            item.ticker
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            item.name
                        )}
                    </td>

                    <td>
                        ${Number(
                            item.score
                        ).toFixed(1)}/10
                    </td>

                    <td>
                        ${escapeHtml(
                            item.risk
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            item.signal
                        )}
                    </td>

                </tr>

            `;

        }

        document.getElementById(
            "result"
        ).innerHTML = `

            <div class="card section">

                <h2>
                    🏆 Ranking
                </h2>

                <div class="table-wrapper">

                    <table>

                        <thead>

                            <tr>

                                <th>#</th>
                                <th>Ativo</th>
                                <th>Nome</th>
                                <th>Nota</th>
                                <th>Risco</th>
                                <th>Sinal</th>

                            </tr>

                        </thead>

                        <tbody>

                            ${rows}

                        </tbody>

                    </table>

                </div>

            </div>

        `;

    } catch (error) {

        showStatus(
            "❌ Erro ao gerar ranking."
        );

    }

}


async function showOpportunities() {

    showStatus(
        "🔥 Procurando oportunidades..."
    );

    try {

        const response =
            await fetch(
                "/api/opportunities"
            );

        const data =
            await response.json();

        if (!data.ok) {

            showStatus(
                "❌ " + data.error
            );

            return;
        }

        hideStatus();

        let rows = "";

        for (
            const item of data.items
        ) {

            rows += `

            <tr>

                <td>
                    <b>${escapeHtml(
                        item.ticker
                    )}</b>
                </td>

                <td>
                    ${escapeHtml(
                        item.name
                    )}
                </td>

                <td>
                    ${Number(
                        item.score
                    ).toFixed(1)}/10
                </td>

                <td class="${
                    item.yearly_change >= 0
                    ? "green"
                    : "red"
                }">

                    ${formatPercent(
                        item.yearly_change
                    )}

                </td>

                <td>
                    ${escapeHtml(
                        item.risk
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        item.signal
                    )}
                </td>

            </tr>

            `;

        }

        document.getElementById(
            "result"
        ).innerHTML = `

            <div class="card section">

                <h2>
                    🔥 Oportunidades
                </h2>

                <div class="table-wrapper">

                    <table>

                        <thead>

                            <tr>

                                <th>Ativo</th>
                                <th>Nome</th>
                                <th>Nota</th>
                                <th>1 ano</th>
                                <th>Risco</th>
                                <th>Sinal</th>

                            </tr>

                        </thead>

                        <tbody>

                            ${rows}

                        </tbody>

                    </table>

                </div>

            </div>

        `;

    } catch (error) {

        showStatus(
            "❌ Erro ao buscar oportunidades."
        );

    }

}


function exportExcel() {

    window.location.href =
        "/export/excel";

}


document
    .getElementById("ticker")
    .addEventListener(
        "keydown",
        function(event) {

            if (
                event.key === "Enter"
            ) {

                analyze();

            }

        }
    );


loadPortfolio();

</script>

</body>

</html>
"""


# ================================================================
# ROTA PRINCIPAL
# ================================================================

@app.route("/")
def index():

    return render_template_string(
        HTML
    )


# ================================================================
# API DE ANÁLISE
# ================================================================

@app.route("/api/analyze")
def api_analyze():

    ticker = request.args.get(
        "ticker",
        ""
    )

    return jsonify(
        analyze_asset(ticker)
    )


# ================================================================
# API CARTEIRA - GET
# ================================================================

@app.route("/api/portfolio", methods=["GET"])
def get_portfolio():

    enriched = []

    for item in portfolio:

        try:

            analysis =
                analyze_asset(
                    item["ticker"]
                )

            if analysis.get("ok"):

                current =
                    analysis[
                        "indicators"
                    ].get("current")

                currency =
                    analysis.get(
                        "currency",
                        "BRL"
                    )

            else:

                current = None

                currency = "BRL"

            enriched.append({

                "ticker":
                    display_ticker(
                        item["ticker"]
                    ),

                "quantity":
                    item["quantity"],

                "average_price":
                    item["average_price"],

                "current_price":
                    current,

                "currency":
                    currency

            })

        except Exception:

            enriched.append({

                "ticker":
                    display_ticker(
                        item["ticker"]
                    ),

                "quantity":
                    item["quantity"],

                "average_price":
                    item["average_price"],

                "current_price":
                    None,

                "currency":
                    "BRL"

            })

    return jsonify({
        "ok": True,
        "portfolio": enriched
    })


# ================================================================
# API CARTEIRA - POST
# ================================================================

@app.route(
    "/api/portfolio",
    methods=["POST"]
)
def add_portfolio():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        ticker =
            normalize_ticker(
                data.get("ticker")
            )

        quantity =
            safe_float(
                data.get("quantity")
            )

        price =
            safe_float(
                data.get("price")
            )

        if not ticker:

            return jsonify({
                "ok": False,
                "error":
                    "Informe o ticker."
            }), 400

        if quantity is None or quantity <= 0:

            return jsonify({
                "ok": False,
                "error":
                    "Quantidade inválida."
            }), 400

        if price is None or price <= 0:

            return jsonify({
                "ok": False,
                "error":
                    "Preço médio inválido."
            }), 400

        # Se já existe, soma posição
        existing = None

        for item in portfolio:

            if item["ticker"] == ticker:

                existing = item
                break

        if existing:

            old_qty =
                existing["quantity"]

            old_price =
                existing["average_price"]

            total_qty =
                old_qty + quantity

            weighted =
                (
                    old_qty * old_price
                    +
                    quantity * price
                ) / total_qty

            existing[
                "quantity"
            ] = total_qty

            existing[
                "average_price"
            ] = weighted

        else:

            portfolio.append({

                "ticker":
                    ticker,

                "quantity":
                    quantity,

                "average_price":
                    price

            })


        # retorna carteira
        response =
            get_portfolio()

        return response

    except Exception as error:

        return jsonify({

            "ok": False,

            "error":
                f"Erro ao adicionar: {str(error)}"

        }), 500


# ================================================================
# API CARTEIRA - DELETE
# ================================================================

@app.route(
    "/api/portfolio/<ticker>",
    methods=["DELETE"]
)
def delete_portfolio(ticker):

    ticker = normalize_ticker(
        ticker
    )

    global portfolio

    portfolio = [
        item
        for item in portfolio
        if item["ticker"] != ticker
    ]

    return get_portfolio()


# ================================================================
# ATIVOS DO RANKING
# ================================================================

DEFAULT_ASSETS = [

    # Ações Brasil
    "PETR4",
    "VALE3",
    "ITUB4",
    "BBAS3",
    "WEGE3",

    # FIIs
    "MXRF11",
    "HGLG11",
    "KNRI11",
    "XPLG11",
    "BTLG11",

    # EUA
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA"

]


# ================================================================
# RANKING
# ================================================================

@app.route("/api/ranking")
def ranking():

    results = []

    for ticker in DEFAULT_ASSETS:

        try:

            analysis =
                analyze_asset(
                    ticker
                )

            if not analysis.get("ok"):
                continue

            results.append({

                "ticker":
                    analysis["ticker"],

                "name":
                    analysis["name"],

                "score":
                    analysis["score"],

                "risk":
                    analysis["risk"],

                "signal":
                    analysis["signal"]

            })

        except Exception:

            continue

    results.sort(
        key=lambda x:
            x["score"],
        reverse=True
    )

    return jsonify({

        "ok": True,

        "items":
            results

    })


# ================================================================
# OPORTUNIDADES
# ================================================================

@app.route("/api/opportunities")
def opportunities():

    results = []

    for ticker in DEFAULT_ASSETS:

        try:

            analysis =
                analyze_asset(
                    ticker
                )

            if not analysis.get("ok"):
                continue

            indicators =
                analysis[
                    "indicators"
                ]

            score =
                analysis[
                    "score"
                ]

            yearly =
                indicators.get(
                    "yearly_change"
                )

            # Critério simples:
            # nota >= 7
            # e risco não muito alto

            if (
                score >= 7
                and analysis["risk"]
                not in [
                    "Muito alto"
                ]
            ):

                results.append({

                    "ticker":
                        analysis[
                            "ticker"
                        ],

                    "name":
                        analysis[
                            "name"
                        ],

                    "score":
                        score,

                    "yearly_change":
                        yearly,

                    "risk":
                        analysis[
                            "risk"
                        ],

                    "signal":
                        analysis[
                            "signal"
                        ]

                })

        except Exception:

            continue


    results.sort(
        key=lambda x:
            x["score"],
        reverse=True
    )

    return jsonify({

        "ok": True,

        "items":
            results

    })


# ================================================================
# EXPORTAÇÃO EXCEL
# ================================================================

@app.route("/export/excel")
def export_excel():

    try:

        rows = []

        # --------------------------------------------------------
        # Carteira
        # --------------------------------------------------------

        for item in portfolio:

            analysis =
                analyze_asset(
                    item["ticker"]
                )

            indicators = (
                analysis.get(
                    "indicators",
                    {}
                )
                if analysis.get("ok")
                else {}
            )

            fundamentals = (
                analysis.get(
                    "fundamentals",
                    {}
                )
                if analysis.get("ok")
                else {}
            )

            current =
                safe_float(
                    indicators.get(
                        "current"
                    )
                )

            quantity =
                item["quantity"]

            average =
                item["average_price"]

            invested =
                quantity * average

            current_value = (
                quantity * current
                if current is not None
                else None
            )

            profit = (
                current_value - invested
                if current_value is not None
                else None
            )

            rows.append({

                "Ativo":
                    display_ticker(
                        item["ticker"]
                    ),

                "Quantidade":
                    quantity,

                "Preço Médio":
                    average,

                "Preço Atual":
                    current,

                "Investido":
                    invested,

                "Patrimônio":
                    current_value,

                "Lucro/Prejuízo":
                    profit,

                "Rentabilidade %":
                    (
                        profit /
                        invested *
                        100
                    )
                    if profit is not None
                    and invested
                    else None,

                "Nota":
                    analysis.get(
                        "score"
                    ),

                "Risco":
                    analysis.get(
                        "risk"
                    ),

                "Sinal":
                    analysis.get(
                        "signal"
                    ),

                "P/L":
                    fundamentals.get(
                        "pe"
                    ),

                "P/VP":
                    fundamentals.get(
                        "pb"
                    ),

                "Dividend Yield %":
                    fundamentals.get(
                        "dividend_yield"
                    ),

                "ROE %":
                    fundamentals.get(
                        "roe"
                    )

            })


        # --------------------------------------------------------
        # Se carteira vazia
        # --------------------------------------------------------

        if not rows:

            rows.append({

                "Aviso":
                    "Carteira vazia"

            })


        df =
            pd.DataFrame(
                rows
            )


        output =
            io.BytesIO()


        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                index=False,
                sheet_name="Carteira"
            )


        output.seek(0)


        return send_file(

            output,

            as_attachment=True,

            download_name=
                "invest_analyzer.xlsx",

            mimetype=
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        )

    except Exception as error:

        return jsonify({

            "ok": False,

            "error":
                f"Erro ao exportar Excel: {str(error)}"

        }), 500


# ================================================================
# HEALTH CHECK
# ================================================================

@app.route("/health")
def health():

    return jsonify({

        "status": "ok",

        "app":
            "Invest Analyzer Pro",

        "version":
            "6.0",

        "time":
            datetime.now().isoformat()

    })


# ================================================================
# ERROR HANDLERS
# ================================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "ok": False,

        "error":
            "Página não encontrada."

    }), 404


@app.errorhandler(500)
def server_error(error):

    return jsonify({

        "ok": False,

        "error":
            "Erro interno do servidor."

    }), 500


# ================================================================
# EXECUÇÃO
# ================================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "🚀 INVEST ANALYZER PRO 6.0"
    )

    print(
        "📊 Flask + Yahoo Finance"
    )

    print(
        "💼 Carteira + Indicadores + Ranking"
    )

    print(
        f"🌐 Porta: {PORT}"
    )

    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )
⚠️ E tem uma coisa importante no Render
O app.py sozinho não instala as bibliotecas. No seu requirements.txt, coloque exatamente:
Flask
gunicorn
yfinance
pandas
numpy
openpyxl
E no Render, o Start Command deve ser:
gunicorn app:app
Não coloque python app.py como Start Command.
Estrutura do seu GitHub
Deixe assim:
seu-projeto/
│
├── app.py
│
└── requirements.txt
Depois faça:
Substitua o app.py inteiro pelo código acima.
Substitua o requirements.txt.
Salve.
Faça commit no GitHub.
O Render fará o novo deploy.
Abra seu site.
Teste primeiro PETR4.
Depois teste AAPL.
Depois teste MXRF11.
Observação importante: a carteira desse código fica na memória do processo. No Render, ela pode ser perdida quando o serviço reiniciar. Para a próxima versão, o ideal é colocar SQLite/PostgreSQL + login, para cada usuário ter sua própria carteira salva permanentemente.
