"""
Interactive Streamlit Dashboard for Banking Stock Historical Analysis.
Provides interactive charts, technical indicators, risk-return comparisons, and CSV export.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from data_fetcher import fetch_historical_data, get_bank_info, DEFAULT_BANK_TICKERS
from bank_analysis import (
    compute_returns_and_growth,
    compute_technical_indicators,
    calculate_risk_return_metrics,
    compare_multiple_banks
)

# Page configuration
st.set_page_config(
    page_title="Banking Sector Historical Stock Analysis",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .metric-title {
        font-size: 13px;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 22px;
        font-weight: bold;
        color: #212529;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🏦 Banking Stock Explorer")
st.sidebar.markdown("Explore historical market performance, risk-adjusted metrics, and technical indicators.")

# Bank selection
selected_bank_name = st.sidebar.selectbox(
    "Select Primary Bank:",
    list(DEFAULT_BANK_TICKERS.keys()),
    index=0
)
primary_ticker = DEFAULT_BANK_TICKERS[selected_bank_name]

# Period selection
period_option = st.sidebar.selectbox(
    "Select Historical Period:",
    ["1y", "2y", "3y", "5y", "10y", "max"],
    index=3
)

# Additional comparison banks
compare_selection = st.sidebar.multiselect(
    "Compare with other banks:",
    [b for b in DEFAULT_BANK_TICKERS.keys() if b != selected_bank_name],
    default=["State Bank of India (SBI)", "Nifty Bank Index"] if selected_bank_name != "State Bank of India (SBI)" else ["HDFC Bank", "Nifty Bank Index"]
)

# Fetch Primary Data
@st.cache_data(ttl=3600)
def load_data(ticker, period):
    df = fetch_historical_data(ticker, period=period)
    df = compute_returns_and_growth(df)
    df = compute_technical_indicators(df)
    return df

@st.cache_data(ttl=3600)
def load_info(ticker):
    return get_bank_info(ticker)

try:
    with st.spinner(f"Fetching data for {selected_bank_name}..."):
        df_primary = load_data(primary_ticker, period_option)
        info_primary = load_info(primary_ticker)
        
        # Benchmark for metrics
        bench_ticker = DEFAULT_BANK_TICKERS.get("Nifty Bank Index", "^NSEBANK")
        df_bench = load_data(bench_ticker, period_option) if primary_ticker != bench_ticker else None
        metrics_primary = calculate_risk_return_metrics(df_primary, benchmark_df=df_bench)

    # Header section
    st.title(f"📊 {selected_bank_name} ({primary_ticker}) Analysis")
    st.caption(f"Historical Data Horizon: **{df_primary.index.min().strftime('%d %b %Y')}** to **{df_primary.index.max().strftime('%d %b %Y')}** | Currency: **INR (₹)**")

    # Top KPI Metrics Row
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns(6)
    
    current_price = metrics_primary.get("Current Price (INR)", df_primary["Close"].iloc[-1])
    cagr = metrics_primary.get("CAGR (%)", 0.0)
    volatility = metrics_primary.get("Annualized Volatility (%)", 0.0)
    sharpe = metrics_primary.get("Sharpe Ratio (Rf=6.5%)", 0.0)
    max_dd = metrics_primary.get("Max Drawdown (%)", 0.0)
    var_95 = metrics_primary.get("Historical VaR 95% (Daily %)", 0.0)

    with kpi_col1:
        st.metric("Current Price", f"₹{current_price:,.2f}")
    with kpi_col2:
        st.metric("CAGR (Ann. Return)", f"{cagr}%", delta=f"{cagr:.1f}%")
    with kpi_col3:
        st.metric("Annualized Volatility", f"{volatility}%")
    with kpi_col4:
        st.metric("Sharpe Ratio", f"{sharpe}")
    with kpi_col5:
        st.metric("Max Drawdown", f"{max_dd}%", delta=f"{max_dd}%", delta_color="inverse")
    with kpi_col6:
        st.metric("1-Day VaR (95%)", f"{var_95}%")

    # Tabs for different analysis views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Price & Technicals",
        "⚖️ Comparative Performance",
        "🛡️ Risk & Drawdown",
        "📊 Returns Distribution",
        "💾 Raw Data & Export"
    ])

    with tab1:
        st.subheader("Price Trend, Moving Averages & Volume")
        
        # Technical options
        show_sma50 = st.checkbox("Show 50-Day SMA", value=True)
        show_sma200 = st.checkbox("Show 200-Day SMA", value=True)
        show_bb = st.checkbox("Show Bollinger Bands", value=True)

        fig_price = go.Figure()
        # Candlestick or Line
        chart_type = st.radio("Chart Type:", ["Candlestick", "Line"], horizontal=True)
        if chart_type == "Candlestick" and "Open" in df_primary.columns:
            fig_price.add_trace(go.Candlestick(
                x=df_primary.index,
                open=df_primary["Open"],
                high=df_primary["High"],
                low=df_primary["Low"],
                close=df_primary["Close"],
                name="OHLC Price"
            ))
        else:
            fig_price.add_trace(go.Scatter(
                x=df_primary.index, y=df_primary["Close"],
                mode="lines", name="Close Price", line=dict(color="#1f77b4", width=2)
            ))

        if show_sma50 and "SMA_50" in df_primary.columns:
            fig_price.add_trace(go.Scatter(
                x=df_primary.index, y=df_primary["SMA_50"],
                mode="lines", name="50-Day SMA", line=dict(color="#ff7f0e", width=1.5, dash="dash")
            ))
        if show_sma200 and "SMA_200" in df_primary.columns:
            fig_price.add_trace(go.Scatter(
                x=df_primary.index, y=df_primary["SMA_200"],
                mode="lines", name="200-Day SMA", line=dict(color="#2ca02c", width=1.5, dash="dot")
            ))
        if show_bb and "BB_Upper" in df_primary.columns:
            fig_price.add_trace(go.Scatter(
                x=df_primary.index, y=df_primary["BB_Upper"],
                mode="lines", name="BB Upper (+2σ)", line=dict(color="rgba(128,128,128,0.4)", width=1)
            ))
            fig_price.add_trace(go.Scatter(
                x=df_primary.index, y=df_primary["BB_Lower"],
                mode="lines", name="BB Lower (-2σ)", line=dict(color="rgba(128,128,128,0.4)", width=1),
                fill="tonexty", fillcolor="rgba(200,200,200,0.15)"
            ))

        fig_price.update_layout(
            height=500,
            xaxis_title="Date",
            yaxis_title="Price (INR)",
            template="plotly_white",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_price, use_container_width=True)

        # Oscillators: RSI and MACD
        col_rsi, col_macd = st.columns(2)
        with col_rsi:
            st.subheader("Relative Strength Index (RSI 14)")
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(
                x=df_primary.index, y=df_primary["RSI_14"],
                mode="lines", name="RSI", line=dict(color="#8c564b", width=1.5)
            ))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
            fig_rsi.update_layout(height=280, template="plotly_white", yaxis=dict(range=[0, 100]), margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_rsi, use_container_width=True)

        with col_macd:
            st.subheader("MACD (12, 26, 9)")
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=df_primary.index, y=df_primary["MACD"], mode="lines", name="MACD", line=dict(color="#1f77b4", width=1.5)))
            fig_macd.add_trace(go.Scatter(x=df_primary.index, y=df_primary["MACD_Signal"], mode="lines", name="Signal", line=dict(color="#ff7f0e", width=1.5)))
            colors = ["green" if v >= 0 else "red" for v in df_primary["MACD_Hist"]]
            fig_macd.add_trace(go.Bar(x=df_primary.index, y=df_primary["MACD_Hist"], name="Histogram", marker_color=colors))
            fig_macd.update_layout(height=280, template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_macd, use_container_width=True)

    with tab2:
        st.subheader("Cumulative Growth & Cross-Bank Benchmark")
        
        all_selected_banks = [selected_bank_name] + compare_selection
        comparison_dict = {}
        for b_name in all_selected_banks:
            t = DEFAULT_BANK_TICKERS[b_name]
            try:
                b_df = load_data(t, period_option)
                comparison_dict[b_name] = b_df
            except Exception:
                pass

        # Normalized returns plot
        fig_comp = go.Figure()
        for b_name, b_df in comparison_dict.items():
            norm_growth = (b_df["Close"] / b_df["Close"].iloc[0]) * 10000
            fig_comp.add_trace(go.Scatter(
                x=norm_growth.index, y=norm_growth,
                mode="lines", name=f"{b_name} (₹{norm_growth.iloc[-1]:,.0f})",
                line=dict(width=3 if b_name == selected_bank_name else 1.8)
            ))
        fig_comp.update_layout(
            title="Growth of Initial ₹10,000 Investment",
            xaxis_title="Date",
            yaxis_title="Portfolio Value (INR)",
            template="plotly_white",
            height=480
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        # Comparative Metrics Table
        st.subheader("Quantitative Risk-Return Summary Table")
        bench_key = "Nifty Bank Index" if "Nifty Bank Index" in comparison_dict else None
        comp_metrics, comp_corr = compare_multiple_banks(
            comparison_dict,
            benchmark_key=bench_key or "",
            risk_free_rate=0.065
        )
        st.dataframe(comp_metrics, use_container_width=True)

        # Correlation Heatmap
        st.subheader("Returns Correlation Matrix")
        fig_heatmap = px.imshow(
            comp_corr,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu_r",
            labels=dict(color="Correlation")
        )
        fig_heatmap.update_layout(height=400)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    with tab3:
        st.subheader("Risk & Drawdown Analysis")
        
        # Volatility
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(
            x=df_primary.index, y=df_primary["Volatility_30D_Ann"],
            mode="lines", name=f"{selected_bank_name} 30D Ann. Volatility (%)",
            line=dict(color="#1f77b4", width=1.8)
        ))
        fig_vol.update_layout(
            title="30-Day Rolling Annualized Volatility (%)",
            xaxis_title="Date",
            yaxis_title="Annualized Volatility (%)",
            template="plotly_white",
            height=350
        )
        st.plotly_chart(fig_vol, use_container_width=True)

        # Underwater Drawdown Plot
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=df_primary.index, y=df_primary["Drawdown"] * 100,
            mode="lines", name="Drawdown (%)",
            line=dict(color="#d62728", width=1.5),
            fill="tozeroy", fillcolor="rgba(214, 39, 40, 0.25)"
        ))
        fig_dd.update_layout(
            title="Underwater Drawdown Profile (%)",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            template="plotly_white",
            height=350
        )
        st.plotly_chart(fig_dd, use_container_width=True)

    with tab4:
        st.subheader("Daily Returns Distribution & Value at Risk (VaR)")
        ret_series = df_primary["Daily_Return"].dropna() * 100
        v95 = np.percentile(ret_series, 5)
        v99 = np.percentile(ret_series, 1)

        fig_dist = px.histogram(
            ret_series,
            nbins=80,
            marginal="box",
            labels={"value": "Daily Return (%)"},
            title=f"{selected_bank_name} - Return Frequency Distribution"
        )
        fig_dist.add_vline(x=v95, line_dash="dash", line_color="red", annotation_text=f"95% VaR ({abs(v95):.2f}%)")
        fig_dist.add_vline(x=v99, line_dash="dot", line_color="purple", annotation_text=f"99% VaR ({abs(v99):.2f}%)")
        fig_dist.update_layout(template="plotly_white", height=450)
        st.plotly_chart(fig_dist, use_container_width=True)

    with tab5:
        st.subheader("Historical Data Table & Export")
        st.dataframe(df_primary.tail(50), use_container_width=True)
        csv_data = df_primary.to_csv().encode("utf-8")
        st.download_button(
            label=f"📥 Download {selected_bank_name} Clean Data (CSV)",
            data=csv_data,
            file_name=f"{primary_ticker}_historical_data.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"Error loading stock data: {e}")
    st.info("Please verify the internet connection or try another ticker.")
