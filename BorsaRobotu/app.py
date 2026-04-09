import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh # Otomatik yenileme için

# --- 1. OTOMATİK YENİLEME (Her 10 saniyede bir) ---
# Not: Eğer hata alırsan terminale 'pip install streamlit-autorefresh' yaz.
count = st_autorefresh(interval=10000, limit=1000, key="fizzbuzzcounter")

st.set_page_config(page_title="TradeVision Live", layout="wide")

# --- 2. GÖRSEL TASARIM ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .prediction-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #3498db;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .confidence-high { color: #28a745; font-weight: bold; font-size: 14px; }
    .confidence-mid { color: #f39c12; font-weight: bold; font-size: 14px; }
    .live-indicator { color: red; font-weight: bold; animation: blinker 1s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR VE MENÜ ---
with st.sidebar:
    st.title("🚀 TradeVision Live")
    
    # İstediğin Menü Sistemi
    stocks_dict = {
        "Türk Hava Yolları": "THYAO.IS",
        "Aselsan": "ASELS.IS",
        "Sasa Polyester": "SASA.IS",
        "Tüpraş": "TUPRS.IS",
        "Ereğli Demir Çelik": "EREGL.IS",
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Nvidia": "NVDA",
        "--- MANUEL GİRİŞ ---": "MANUAL"
    }
    
    selected_name = st.selectbox("Hisse/Varlık Seçin:", list(stocks_dict.keys()))
    
    if selected_name == "--- MANUEL GİRİŞ ---":
        symbol = st.text_input("Sembol Yazın (Örn: AAPL):", "BIMAS.IS").upper()
    else:
        symbol = stocks_dict[selected_name]
    
    st.markdown("---")
    st.write(f"⏱️ **Son Güncelleme:** {datetime.now().strftime('%H:%M:%S')}")
    st.markdown('<p class="live-indicator">● CANLI VERİ AKIŞI AKTİF</p>', unsafe_allow_html=True)

# --- 4. HESAPLAMA MOTORU ---
def get_analysis(data):
    last_price = float(data['Close'].iloc[-1])
    volatility = data['Close'].pct_change().std()
    
    # Trend analizi
    short_trend = (data['Close'].iloc[-1] / data['Close'].iloc[-20]) - 1
    
    def forecast(days):
        # Akıllı tahmin: Trend hızı + volatilite riski
        drift = short_trend * (days / 20)
        target = last_price * (1 + drift)
        conf = 95 - (volatility * 150 * np.sqrt(days))
        return target, max(min(conf, 99), 30)

    return {
        "1D": forecast(1),
        "14D": forecast(14),
        "1M": forecast(30),
        "1Y": forecast(365)
    }

# --- 5. VERİ ÇEKME VE GÖRÜNTÜLEME ---
data = yf.download(symbol, period="1y", interval="1d", progress=False)

if not data.empty:
    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
    data = data.dropna()
    
    preds = get_analysis(data)
    current_val = float(data['Close'].iloc[-1])

    c_left, c_right = st.columns([2, 1])

    with c_left:
        st.subheader(f"📊 {selected_name} Teknik Görünüm")
        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Fiyat")])
        fig.update_layout(template="plotly_white", height=500, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        st.subheader("💰 Tahmin Terminali")
        st.metric("Anlık Fiyat", f"{current_val:,.2f} TL")
        
        display_map = [("Yarın", "1D"), ("14 Gün Sonra", "14D"), ("1 Ay Sonra", "1M"), ("1 Yıl Sonra", "1Y")]
        
        for label, key in display_map:
            p_val, p_conf = preds[key]
            c_style = "confidence-high" if p_conf > 70 else "confidence-mid"
            st.markdown(f"""
                <div class="prediction-card">
                    <small style="color: #7f8c8d;">{label}</small><br>
                    <b style="font-size: 20px; color: #2c3e50;">{p_val:,.2f} TL</b><br>
                    <span class="{c_style}">Güven: %{p_conf:.1f}</span>
                </div>
            """, unsafe_allow_html=True)

else:
    st.error("Veri alınamadı, lütfen bekleyin veya sembolü kontrol edin.")