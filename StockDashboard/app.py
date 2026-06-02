import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(
    page_title="Stock Dashboard",
    layout="wide"
)

st.title("Stock Dashboard")
@st.cache_data
def load_watchlist():
    return pd.read_csv("data/watchlist.csv")
watchlist_df = load_watchlist()

categories = sorted(watchlist_df["category"].unique())

selected_categories = st.multiselect(
    "Select categories",
    categories,
    default=["Owned", "Mag7"]
)
selected_watchlist = watchlist_df[
    watchlist_df["category"].isin(selected_categories)
]

default_tickers = selected_watchlist["ticker"].tolist()

extra_tickers_input = st.text_input(
    "Optional: add extra tickers separated by spaces or commas",
    value=""
)

extra_tickers = extra_tickers_input.upper().replace(",", " ").split()

tickers = default_tickers + extra_tickers
tickers = list(dict.fromkeys(tickers))

period = st.selectbox(
    "Select period",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3
)
st.write("Loaded tickers:", ", ".join(tickers))
chart_tickers = st.multiselect(
    "Select tickers to chart",
    tickers,
    default=tickers[:3]
)
fig = go.Figure()

for ticker in chart_tickers:
    df = yf.download(
        ticker,
        period=period,
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        st.warning(f"No data found for {ticker}")
        continue

    close = df["Close"].squeeze() 
    performance = (close / close.iloc[0] - 1) * 100
    fig.add_trace(
        go.Scatter(
            x=close.index,
            y=close.values,
            mode="lines",
            name=ticker
        )
    )
fig_perf = go.Figure()

for ticker in chart_tickers:
    df = yf.download(
        ticker,
        period=period,
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        continue

    close = df["Close"].squeeze()
    performance = (close / close.iloc[0] - 1) * 100

    fig_perf.add_trace(
        go.Scatter(
            x=performance.index,
            y=performance.values,
            mode="lines",
            name=ticker
        )
    )

fig_perf.update_layout(
    title="Performance comparison",
    xaxis_title="Date",
    yaxis_title="% return",
    height=600
)

st.plotly_chart(fig_perf, use_container_width=True)

fig.update_layout(
    title="Stock price comparison",
    xaxis_title="Date",
    yaxis_title="Price",
    height=600
)
st.subheader("Ticker Summary")

summary_rows = []

for ticker in tickers:
    df = yf.download(
        ticker,
        period="1y",
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        continue

    close = df["Close"].squeeze()

    latest_price = close.iloc[-1]
    ma20 = close.rolling(window=20).mean().iloc[-1]
    ma50 = close.rolling(window=50).mean().iloc[-1]
    ma200 = close.rolling(window=200).mean().iloc[-1]

    one_year_return = (latest_price / close.iloc[0] - 1) * 100

    price_vs_20 = ((latest_price / ma20) - 1) * 100
    price_vs_50 = ((latest_price / ma50) - 1) * 100
    price_vs_200 = ((latest_price / ma200) - 1) * 100

    if latest_price > ma20 and latest_price > ma50 and latest_price > ma200:
        trend_status = "Strong uptrend"
    elif latest_price > ma50 and latest_price > ma200:
        trend_status = "Uptrend"
    elif latest_price > ma200:
        trend_status = "Weakening"
    else:
        trend_status = "Below 200D"

    if ma20 > ma50 > ma200:
        ma_structure = "Bullish"
    elif ma20 < ma50 < ma200:
        ma_structure = "Bearish"
    else:
        ma_structure = "Mixed"

    summary_rows.append({
        "Ticker": ticker,
        "Price": latest_price,
        "1Y Return %": one_year_return,
        "Trend": trend_status,
        "MA Structure": ma_structure,
        "20D MA": ma20,
        "50D MA": ma50,
        "200D MA": ma200,
        "vs 20D %": price_vs_20,
        "vs 50D %": price_vs_50,
        "vs 200D %": price_vs_200
    })

summary_df = pd.DataFrame(summary_rows)

number_columns = [
    "Price",
    "1Y Return %",
    "20D MA",
    "50D MA",
    "200D MA",
    "vs 20D %",
    "vs 50D %",
    "vs 200D %"
]

for column in number_columns:
    summary_df[column] = summary_df[column].round(2)

st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True,
    height=420
)

csv_data = summary_df.to_csv(index=False)

st.download_button(
    label="Download table as CSV",
    data=csv_data,
    file_name="ticker_summary.csv",
    mime="text/csv"
)

