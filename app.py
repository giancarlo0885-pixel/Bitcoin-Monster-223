import os
import math
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Garibaldi Crypto Prediction Bot", page_icon="₿", layout="wide")

st.title("GARIBALDI CRYPTO PREDICTION BOT™")
st.caption("Railway-ready demo app with live market data, training mode, and risk alerts.")

DEFAULT_TICKERS = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD"]

with st.sidebar:
    st.header("Settings")
    tickers_raw = st.text_input("Crypto tickers", ", ".join(DEFAULT_TICKERS))
    days_ahead = st.slider("Forecast days", 1, 30, 5)
    period = st.selectbox("History period", ["30d", "60d", "90d", "180d", "1y"], index=2)
    train_mode = st.toggle("Training Mode", value=True)


def clean_tickers(text: str):
    items = [x.strip().upper() for x in text.replace("\n", ",").split(",") if x.strip()]
    return items or DEFAULT_TICKERS


def fetch_history(ticker: str, period: str = "90d") -> pd.DataFrame:
    data = yf.Ticker(ticker).history(period=period, interval="1d")
    if data.empty or "Close" not in data:
        return pd.DataFrame()
    data = data.dropna(subset=["Close"])
    return data


def oracle_forecast(close: pd.Series, days: int):
    prices = close.astype(float).values
    if len(prices) < 10:
        return None
    spot = float(prices[-1])
    returns = np.diff(np.log(prices))
    mu = float(np.mean(returns))
    sigma = float(np.std(returns))
    target = spot * math.exp((mu - 0.5 * sigma**2) * days)
    radius = sigma * math.sqrt(days)
    floor = target * math.exp(-2 * radius)
    ceiling = target * math.exp(2 * radius)
    momentum = (spot / float(prices[-7]) - 1) * 100 if len(prices) >= 7 else 0
    return {
        "Spot": spot,
        "Target": target,
        "Floor": floor,
        "Ceiling": ceiling,
        "Daily Vol %": sigma * 100,
        "7D Momentum %": momentum,
    }


def signal_from_forecast(row):
    if row["7D Momentum %"] > 7 and row["Target"] > row["Spot"]:
        return "Bullish Watch"
    if row["7D Momentum %"] < -7:
        return "High Risk"
    if row["Target"] > row["Spot"]:
        return "Lean Bullish"
    return "Neutral / Wait"


tickers = clean_tickers(tickers_raw)
rows = []
charts = {}
errors = []

for ticker in tickers:
    try:
        hist = fetch_history(ticker, period)
        if hist.empty:
            errors.append(f"No data returned for {ticker}.")
            continue
        forecast = oracle_forecast(hist["Close"], days_ahead)
        if forecast is None:
            errors.append(f"Not enough data for {ticker}.")
            continue
        forecast["Ticker"] = ticker
        forecast["Signal"] = signal_from_forecast(forecast)
        rows.append(forecast)
        charts[ticker] = hist["Close"]
    except Exception as exc:
        errors.append(f"{ticker}: {exc}")

if errors:
    with st.expander("Data warnings"):
        for err in errors:
            st.warning(err)

if rows:
    df = pd.DataFrame(rows)
    df = df[["Ticker", "Spot", "Target", "Floor", "Ceiling", "Daily Vol %", "7D Momentum %", "Signal"]]
    st.subheader("Market Oracle Table")
    st.dataframe(df.style.format({
        "Spot": "${:,.2f}",
        "Target": "${:,.2f}",
        "Floor": "${:,.2f}",
        "Ceiling": "${:,.2f}",
        "Daily Vol %": "{:.2f}%",
        "7D Momentum %": "{:.2f}%",
    }), use_container_width=True)

    selected = st.selectbox("Chart ticker", df["Ticker"].tolist())
    st.line_chart(charts[selected])

    if train_mode:
        st.subheader("Training Mode")
        st.write("This mode simulates signal review only. It does not place trades.")
        st.write("Use the table to compare target, floor, ceiling, volatility, and 7-day momentum before making any decision.")
else:
    st.error("No market data loaded. Check ticker symbols like BTC-USD or ETH-USD.")

st.divider()
st.caption(f"Last run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | Educational tool only, not financial advice.")
