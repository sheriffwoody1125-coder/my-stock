import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide", page_title="全自動個人資產獵人儀表板")
st.title("💼 個人持股即時追蹤儀表板")

# 1. 初始資料設定
initial_tw = {
    '0050.TW': {'shares': 2965.0, 'cost': 189512.0},
    '00878.TW': {'shares': 122946.0, 'cost': 2486507.0},
    '00919.TW': {'shares': 8006.0, 'cost': 198822.0},
    '00924.TW': {'shares': 3000.0, 'cost': 65755.0},
    '2330.TW': {'shares': 1297.0, 'cost': 830532.0},
    '00713.TW': {'shares': 10000.0, 'cost': 475740.0},
    '00929.TW': {'shares': 10000.0, 'cost': 182379.0}
}

initial_us = {
    'ARKX': {'shares': 90.0, 'cost': 2969.45},
    'GRID': {'shares': 30.0, 'cost': 5902.90},
    'NLR': {'shares': 80.0, 'cost': 11341.0},
    'NVDA': {'shares': 359.04195, 'cost': 57248.95},
    'RKLB': {'shares': 30.0, 'cost': 3756.91},
    'TSLA': {'shares': 219.45375, 'cost': 81563.27},
    'UFO': {'shares': 280.0, 'cost': 14639.10},
    'GOOGL': {'shares': 52.57872, 'cost': 10559.77},
    'VOO': {'shares': 14.82757, 'cost': 8506.89}
}

# 2. 側邊欄：動態修改持股數量與成本
st.sidebar.header("⚙️ 持股數量與成本調整")
holdings = {}

st.sidebar.subheader("🇹🇼 台股部位")
for ticker, data in initial_tw.items():
    name = ticker.split('.')[0]
    shares = st.sidebar.number_input(f"{name} 股數", value=data['shares'], step=1.0, key=f"s_{ticker}")
    cost = st.sidebar.number_input(f"{name} 總成本", value=data['cost'], step=100.0, key=f"c_{ticker}")
    if shares > 0:
        holdings[ticker] = {'shares': shares, 'cost': cost, 'type': 'TW'}

st.sidebar.subheader("🇺🇸 美股部位")
for ticker, data in initial_us.items():
    shares = st.sidebar.number_input(f"{ticker} 股數", value=data['shares'], step=0.01, key=f"s_{ticker}")
    cost = st.sidebar.number_input(f"{ticker} 總成本", value=data['cost'], step=10.0, key=f"c_{ticker}")
    if shares > 0:
        holdings[ticker] = {'shares': shares, 'cost': cost, 'type': 'US'}

# 3. 獲取即時數據與運算
@st.cache_data(ttl=60)  # 快取60秒，避免頻繁請求被 yfinance 鎖IP
def get_stock_data(tickers):
    data = {}
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            # 獲取最新價格
            hist = stock.history(period="2d")
            price = hist['Close'].iloc[-1] if not hist.empty else 0
            # 獲取新聞
            news = stock.news[:2] if stock.news else []
            data[t] = {'price': price, 'news': news}
        except:
            data[t] = {'price': 0, 'news': []}
    return data

tickers_list = list(holdings.keys())
live_data = get_stock_data(tickers_list)

# 4. 建立資料表
rows = []
for t, h in holdings.items():
    current_price = live_data[t]['price']
    market_value = current_price * h['shares']
    pnl = market_value - h['cost']
    pnl_p = (pnl / h['cost'] * 100) if h['cost'] > 0 else 0
    
    rows.append({
        '標的': t.split('.')[0],
        '市場': h['type'],
        '持股數': h['shares'],
        '總成本': h['cost'],
        '即時股價': round(current_price, 2),
        '現值': round(market_value, 2),
        '未實現損益': round(pnl, 2),
        '報酬率(%)': round(pnl_p, 2)
    })

df = pd.DataFrame(rows)

# 5. 儀表板主畫面
tab1, tab2, tab3 = st.tabs(["📊 資產總覽", "📈 歷史走勢", "📰 相關新聞"])

with tab1:
    st.subheader("💰 即時損益狀況")
    if not df.empty:
        st.dataframe(df.style.format({
            '持股數': '{:,.2f}', '總成本': '{:,.2f}', '即時股價': '{:,.2f}', 
            '現值': '{:,.2f}', '未實現損益': '{:,.2f}', '報酬率(%)': '{:+.2f}%'
        }), use_container_width=True)
    else:
        st.warning("請在左側輸入至少一項持股。")

with tab2:
    st.subheader("📈 歷史走勢圖表")
    selected_stock = st.selectbox("選擇要查看歷史走勢的標的", tickers_list)
    period = st.selectbox("時間範圍", ["1mo", "3mo", "1y", "5y"], index=2)
    
    if selected_stock:
        hist_data = yf.Ticker(selected_stock).history(period=period)
        fig = go.Figure(data=[go.Scatter(x=hist_data.index, y=hist_data['Close'], mode='lines', name='收盤價')])
        fig.update_layout(title=f"{selected_stock} 歷史走勢", xaxis_title="日期", yaxis_title="價格")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("📰 最新持股相關新聞 (Yahoo Finance)")
    for t in tickers_list:
        news_items = live_data[t]['news']
        if news_items:
            st.markdown(f"#### 🔍 {t.split('.')[0]} 相關報導")
            for item in news_items:
                st.markdown(f"- [{item['title']}]({item['link']})")