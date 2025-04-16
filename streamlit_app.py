import streamlit as st
import requests
import pandas as pd
import time
import matplotlib.pyplot as plt
import seaborn as sns

# Set Streamlit page config
st.set_page_config(page_title="Futures Correlation Analyzer", layout="wide")

# Functions
def get_top_futures_symbols(limit=20):
    url = 'https://fapi.binance.com/fapi/v1/ticker/24hr'
    response = requests.get(url)
    data = response.json()
    sorted_data = sorted(data, key=lambda x: float(x['quoteVolume']), reverse=True)
    top_symbols = []
    for item in sorted_data:
        if item['symbol'].endswith('USDT') and 'PERP' not in item['symbol']:
            top_symbols.append(item['symbol'])
        if len(top_symbols) >= limit:
            break
    return top_symbols

def fetch_ohlcv(symbol, days=100, interval='1d'):
    end_time = int(time.time() * 1000)
    start_time = end_time - days * 24 * 60 * 60 * 1000
    url = 'https://fapi.binance.com/fapi/v1/klines'
    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': start_time,
        'endTime': end_time,
        'limit': 1000
    }
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'num_trades',
        'taker_buy_base_vol', 'taker_buy_quote_vol', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    return df[['timestamp', 'close', 'volume']].set_index('timestamp')

def plot_correlations(price_corr, volume_corr):
    fig, axes = plt.subplots(1, 2, figsize=(25, 10))

    sns.heatmap(price_corr, annot=True, fmt=".2f", cmap="coolwarm", ax=axes[0])
    axes[0].set_title("Price Correlation")

    sns.heatmap(volume_corr, annot=True, fmt=".2f", cmap="viridis", ax=axes[1])
    axes[1].set_title("Volume Correlation")

    st.pyplot(fig)

# Streamlit UI
st.title("📈 Binance Futures Correlation Analyzer")

# Controls
days = st.slider("Select number of days to analyze", min_value=30, max_value=180, value=90)
symbol_limit = st.slider("Number of top futures to compare", min_value=5, max_value=25, value=10)

# Load and process data
with st.spinner("Fetching and analyzing data..."):
    symbols = get_top_futures_symbols(limit=symbol_limit)
    price_data = pd.DataFrame()
    volume_data = pd.DataFrame()

    for symbol in symbols:
        df = fetch_ohlcv(symbol, days=days)
        price_data[symbol] = df['close']
        volume_data[symbol] = df['volume']

    price_corr = price_data.corr()
    volume_corr = volume_data.corr()

# Show correlation heatmaps
st.subheader("🔗 Correlation Heatmaps")
plot_correlations(price_corr, volume_corr)

# Optionally show raw data
with st.expander("📊 View Raw Price and Volume Data"):
    st.write("Price Data", price_data.tail())
    st.write("Volume Data", volume_data.tail())
