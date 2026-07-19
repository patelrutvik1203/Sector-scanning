import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit.components.v1 as components
import os

# Set page configuration with high-end dashboard icon
st.set_page_config(
    page_title="RRG Pro - Relative Rotation Graphs",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling via CSS injection
st.markdown("""
<style>
    /* Styling Streamlit components for a premium dark-tech feel */
    .stApp {
        background-color: #070b19;
        color: #f8fafc;
    }
    header[data-testid="stHeader"] {
        background-color: rgba(7, 11, 25, 0.9);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #0f172a;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        transition: all 0.3s;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
    }
    .stSidebar {
        background-color: #0c1122 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    div[data-testid="stExpander"] {
        background-color: #0f172a;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to compute Relative Rotation Graph (RRG) metrics (Standard JdK Index Model)
def calculate_rrg(tickers, benchmark, period="1y", interval="1d", window=14):
    try:
        # Step 1: Clean and unique list of tickers
        all_tickers = list(set([t.strip() for t in tickers if t.strip()] + [benchmark.strip()]))
        
        # Download Closing prices directly
        data = yf.download(all_tickers, period=period, interval=interval, progress=False)
        
        if data.empty:
            return None, "No data returned from Yahoo Finance. Please check your internet connection or ticker symbols."
            
        # Extract 'Close' column safely
        # yf.download returns a MultiIndex column DataFrame if multiple tickers are requested.
        # Structure of Close DataFrame: Columns are Tickers, Index is Date.
        prices = pd.DataFrame()
        
        if isinstance(data.columns, pd.MultiIndex):
            if 'Close' in data.columns.levels[0]:
                prices = data['Close']
            elif 'Adj Close' in data.columns.levels[0]:
                prices = data['Adj Close']
            else:
                return None, "Could not find Close or Adj Close prices in MultiIndex columns."
        else:
            # Single ticker download fallback (if yfinance returned a flat DataFrame)
            if 'Close' in data.columns:
                prices = pd.DataFrame({all_tickers[0]: data['Close']})
            elif 'Adj Close' in data.columns:
                prices = pd.DataFrame({all_tickers[0]: data['Adj Close']})
            else:
                return None, f"Could not parse closing prices. Available columns: {list(data.columns)}"

        # Handle missing data
        prices = prices.ffill().bfill()
        
        # Validate that benchmark and tickers exist in downloaded dataset
        if benchmark not in prices.columns:
            return None, f"Benchmark symbol '{benchmark}' could not be resolved. Please verify on Yahoo Finance."
            
        valid_tickers = [t for t in tickers if t in prices.columns and not prices[t].isna().all()]
        if not valid_tickers:
            return None, "None of the tracked symbols could be resolved. Please verify tickers in the sidebar."

        # Safety length check for rolling calculations
        if len(prices) < window + 5:
            return None, f"The lookback contains only {len(prices)} bars, which is too short for a smoothing window of {window}. Please select a longer lookback or a shorter smoothing window."

        benchmark_close = prices[benchmark]
        rrg_data = {}
        
        # Step 2: Loop through tickers and calculate Relative Strength, RS-Ratio, and RS-Momentum
        for ticker in valid_tickers:
            if ticker == benchmark:
                continue
            
            # RS = (Price of Security / Price of Benchmark) * 100
            rs = (prices[ticker] / benchmark_close) * 100
            
            # RS-Ratio = 100 + ((RS - Rolling Mean) / Rolling StdDev) * 10
            rolling_mean_rs = rs.rolling(window=window).mean()
            rolling_std_rs = rs.rolling(window=window).std(ddof=0)
            
            # Avoid division by zero
            rolling_std_rs = rolling_std_rs.replace(0, np.nan)
            rs_ratio = 100 + ((rs - rolling_mean_rs) / rolling_std_rs) * 10
            
            # RS-Momentum: Rate of change of RS-Ratio, normalized
            # ROC = ((Current RS-Ratio / Previous RS-Ratio) - 1) * 100
            rs_ratio_roc = ((rs_ratio / rs_ratio.shift(1)) - 1) * 100
            
            rolling_mean_roc = rs_ratio_roc.rolling(window=window).mean()
            rolling_std_roc = rs_ratio_roc.rolling(window=window).std(ddof=0)
            
            rolling_std_roc = rolling_std_roc.replace(0, np.nan)
            rs_momentum = 100 + ((rs_ratio_roc - rolling_mean_roc) / rolling_std_roc) * 10
            
            # Combine into ticker DataFrame
            ticker_df = pd.DataFrame({
                'Date': prices.index,
                'RS_Ratio': rs_ratio,
                'RS_Momentum': rs_momentum
            }).dropna()
            
            # Explicitly remove infinite values from dataframe rows
            ticker_df = ticker_df[np.isfinite(ticker_df['RS_Ratio']) & np.isfinite(ticker_df['RS_Momentum'])]
            
            if not ticker_df.empty:
                rrg_data[ticker] = ticker_df
                
        return rrg_data, None
    except Exception as e:
        return None, f"Calculation Exception: {str(e)}"

# ============================================
# SIDEBAR CONTROLS
# ============================================

st.sidebar.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <h2 style='color:#10b981; font-weight:800; margin-bottom:0;'>RRG PRO ⚡</h2>
    <p style='color:#94a3b8; font-size:0.85rem; margin-top:0;'>Institutional Sector Rotation</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("🎯 Market Settings")
market_choice = st.sidebar.selectbox(
    "Select Target Market",
    options=["Indian NSE (Nifty 50)", "US Equities (S&P 500)", "Crypto Currencies", "Custom List"],
    index=0
)

# Define defaults based on selection
if market_choice == "Indian NSE (Nifty 50)":
    benchmark_default = "^NSEI"
    tickers_default = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS", "ITC.NS", "AXISBANK.NS", "LT.NS", "BHARTIENTL.NS"]
elif market_choice == "US Equities (S&P 500)":
    benchmark_default = "SPY"
    tickers_default = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "AMD", "JPM"]
elif market_choice == "Crypto Currencies":
    benchmark_default = "BTC-USD"
    tickers_default = ["ETH-USD", "SOL-USD", "BNB-USD", "ADA-USD", "XRP-USD", "DOGE-USD", "DOT-USD", "LINK-USD"]
else:
    benchmark_default = "^NSEI"
    tickers_default = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]

benchmark = st.sidebar.text_input("Benchmark Ticker", value=benchmark_default)
tickers_input = st.sidebar.text_area(
    "Assets to Track (comma-separated)",
    value=", ".join(tickers_default),
    help="Enter ticker symbols supported by Yahoo Finance."
)
tickers = [t.strip() for t in tickers_input.split(",") if t.strip()]

st.sidebar.subheader("⚙️ Calculations & Trails")
timeframe = st.sidebar.selectbox("Timeframe", options=["Daily", "Weekly"], index=0)
interval = "1d" if timeframe == "Daily" else "1wk"

lookback = st.sidebar.selectbox(
    "Data History Lookback",
    options=["6 Months", "1 Year", "2 Years", "3 Years"],
    index=1
)
lookback_map = {
    "6 Months": "6m",
    "1 Year": "1y",
    "2 Years": "2y",
    "3 Years": "3y"
}
period = lookback_map[lookback]

smoothing_window = st.sidebar.slider("Smoothing Window (bars)", min_value=5, max_value=30, value=14)
tail_length = st.sidebar.slider("Tail Length (bars to show history)", min_value=1, max_value=30, value=10)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='font-size:0.75rem; color:#94a3b8; text-align:center;'>
    Developed with ❤ for Premium Traders.<br>
    © 2026 RelativeRotationGraphs.com
</div>
""", unsafe_allow_html=True)

# ============================================
# MAIN BODY LAYOUT
# ============================================

# Top Dashboard Header
st.markdown("""
<div style='background:linear-gradient(135deg, #0f172a 0%, #070b19 100%); padding:24px; border-radius:16px; border:1px solid rgba(255,255,255,0.05); margin-bottom:30px;'>
    <h1 style='margin:0; font-weight:800; font-size:2.5rem; letter-spacing:-1px; color:#ffffff;'>Relative Rotation Graph® Dashboard</h1>
    <p style='margin:5px 0 0 0; color:#94a3b8; font-size:1.1rem;'>Visualize price trends, relative strength, and momentum cycles relative to <strong>{0}</strong></p>
</div>
""".format(benchmark), unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Live Interactive RRG", "🤝 Strike.money Partner Page", "📖 RRG Methodology"])

# TAB 1: LIVE INTERACTIVE RRG CHART (DATA-DRIVEN)
with tab1:
    st.subheader("Interactive Sector Rotation Map")
    
    with st.spinner("Fetching Yahoo Finance data and running JdK normalization..."):
        rrg_results, error = calculate_rrg(tickers, benchmark, period=period, interval=interval, window=smoothing_window)
        
    if error:
        st.error(f"Error calculating RRG: {error}")
        st.info("""
        💡 **Troubleshooting Tips:**
        1. **Check your connection:** Ensure your device can access Yahoo Finance (`finance.yahoo.com`).
        2. **Verify Tickers:** Symbols like Indian stocks must have suffixes (e.g., `RELIANCE.NS` for NSE, `500325.BO` for BSE).
        3. **Adjust Smoothing:** If using a short lookback period (like 6 Months) with a large window (like 30), try shortening the smoothing window.
        """)
    elif not rrg_results:
        st.warning("No data found for the selected tickers or benchmark. Please check your symbols.")
    else:
        # Create Plotly Chart
        fig = go.Figure()

        # Gather points to determine boundary margins
        all_x = []
        all_y = []
        for asset, df in rrg_results.items():
            # Get only the last 'tail_length' elements for scaling calculations
            tail_df = df.tail(tail_length)
            all_x.extend(tail_df['RS_Ratio'].tolist())
            all_y.extend(tail_df['RS_Momentum'].tolist())
            
        # Deep filter to guarantee 100% finite real numbers (eliminates NaN and Inf before Plotly rendering)
        clean_x = [float(x) for x in all_x if np.isfinite(x)]
        clean_y = [float(y) for y in all_y if np.isfinite(y)]

        if len(clean_x) > 0 and len(clean_y) > 0:
            min_x = min(98.0, min(clean_x) - 0.5)
            max_x = max(102.0, max(clean_x) + 0.5)
            min_y = min(98.0, min(clean_y) - 0.5)
            max_y = max(102.0, max(clean_y) + 0.5)
            
            # Guard against mathematical singularities
            if min_x >= max_x:
                min_x, max_x = 95.0, 105.0
            if min_y >= max_y:
                min_y, max_y = 95.0, 105.0
        else:
            min_x, max_x, min_y, max_y = 95.0, 105.0, 95.0, 105.0

        # Configure background quadrant annotations/shading
        fig.add_shape(type="rect", x0=100.0, y0=100.0, x1=max_x, y1=max_y, fillcolor="rgba(16, 185, 129, 0.03)", line_width=0, layer="below") # Leading
        fig.add_shape(type="rect", x0=100.0, y0=min_y, x1=max_x, y1=100.0, fillcolor="rgba(245, 158, 11, 0.03)", line_width=0, layer="below") # Weakening
        fig.add_shape(type="rect", x0=min_x, y0=min_y, x1=100.0, y1=100.0, fillcolor="rgba(239, 68, 68, 0.03)", line_width=0, layer="below") # Lagging
        fig.add_shape(type="rect", x0=min_x, y0=100.0, x1=100.0, y1=max_y, fillcolor="rgba(59, 130, 246, 0.03)", line_width=0, layer="below") # Improving

        # Axis crosshair lines
        fig.add_shape(type="line", x0=100.0, y0=min_y, x1=100.0, y2=max_y, line=dict(color="rgba(255,255,255,0.15)", width=1.5, dash="dash"))
        fig.add_shape(type="line", x0=min_x, y0=100.0, x1=max_x, y2=100.0, line=dict(color="rgba(255,255,255,0.15)", width=1.5, dash="dash"))

        # Quadrant labels at extreme corners
        fig.add_annotation(x=max_x - 0.5, y=max_y - 0.3, text="LEADING (Green)", showarrow=false, font=dict(color="#10b981", size=14, weight="bold"))
        fig.add_annotation(x=max_x - 0.5, y=min_y + 0.3, text="WEAKENING (Yellow)", showarrow=false, font=dict(color="#f59e0b", size=14, weight="bold"))
        fig.add_annotation(x=min_x + 0.5, y=min_y + 0.3, text="LAGGING (Red)", showarrow=false, font=dict(color="#ef4444", size=14, weight="bold"))
        fig.add_annotation(x=min_x + 0.5, y=max_y - 0.3, text="IMPROVING (Blue)", showarrow=false, font=dict(color="#3b82f6", size=14, weight="bold"))

        # Plot individual assets and their trails
        for asset, df in rrg_results.items():
            tail_df = df.tail(tail_length)
            if tail_df.empty:
                continue
                
            # Most recent values
            latest = tail_df.iloc[-1]
            
            # Color assignment
            color_asset = "#10b981" # default green
            if latest['RS_Ratio'] >= 100.0 and latest['RS_Momentum'] >= 100.0:
                color_asset = "#10b981" # Leading
            elif latest['RS_Ratio'] >= 100.0 and latest['RS_Momentum'] < 100.0:
                color_asset = "#f59e0b" # Weakening
            elif latest['RS_Ratio'] < 100.0 and latest['RS_Momentum'] < 100.0:
                color_asset = "#ef4444" # Lagging
            else:
                color_asset = "#3b82f6" # Improving

            # Draw Historical Trail line
            fig.add_trace(go.Scatter(
                x=tail_df['RS_Ratio'],
                y=tail_df['RS_Momentum'],
                mode='lines',
                line=dict(color=color_asset, width=2, dash='dot'),
                hoverinfo='skip',
                showlegend=False
            ))
            
            # Draw Latest marker dot
            fig.add_trace(go.Scatter(
                x=[latest['RS_Ratio']],
                y=[latest['RS_Momentum']],
                mode='markers+text',
                marker=dict(color=color_asset, size=12, line=dict(color='#ffffff', width=1.5)),
                text=[asset.split(".")[0]], # Display short code (e.g. RELIANCE)
                textposition="top center",
                textfont=dict(color="#ffffff", size=10, weight="bold"),
                name=asset,
                hovertemplate=f"<b>{asset}</b><br>RS-Ratio: %{{x:.2f}}<br>RS-Momentum: %{{y:.2f}}<extra></extra>"
            ))

        # Adjust general chart aesthetics
        fig.update_layout(
            xaxis_title="Relative Strength Index (RS-Ratio)",
            yaxis_title="Relative Momentum Index (RS-Momentum)",
            xaxis=dict(range=[min_x, max_x], showgrid=False, zeroline=False),
            yaxis=dict(range=[min_y, max_y], showgrid=False, zeroline=False),
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="#0c1122",
            plot_bgcolor="#0c1122",
            height=700,
            showlegend=False,
            font=dict(color="#f8fafc")
        )

        st.plotly_chart(fig, use_container_width=True)
        
        # Display data summary table
        st.subheader("📊 Sector Standings (Latest Calculated Values)")
        latest_rows = []
        for asset, df in rrg_results.items():
            if not df.empty:
                latest = df.iloc[-1]
                quadrant = get_quadrant_name(latest['RS_Ratio'], latest['RS_Momentum'])
                latest_rows.append({
                    "Ticker": asset,
                    "RS-Ratio (Relative Strength)": round(latest['RS_Ratio'], 2),
                    "RS-Momentum (Relative Momentum)": round(latest['RS_Momentum'], 2),
                    "Quadrant State": quadrant
                })
        
        summary_df = pd.DataFrame(latest_rows).sort_values(by="RS-Ratio (Relative Strength)", ascending=False)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        # Export option
        csv = summary_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export RRG Standings to CSV",
            data=csv,
            file_name="rrg_standings.csv",
            mime="text/csv"
        )

def get_quadrant_name(x, y):
    if x >= 100.0 and y >= 100.0:
        return "🟢 Leading"
    elif x >= 100.0 and y < 100.0:
        return "🟡 Weakening"
    elif x < 100.0 and y < 100.0:
        return "🔴 Lagging"
    else:
        return "🔵 Improving"

# TAB 2: PARTNER LANDING PAGE (EMBEDDED HIGH FIDELITY)
with tab2:
    st.subheader("Official Partner Landing Page")
    st.write("Below is the identical, ultra-fast partner page for Strike.money featuring custom vector logos and interactive animated mechanics.")
    
    # Check if html file exists, if so read it and render it as an iframe
    if os.path.exists("strike_money_rrg_partner.html"):
        with open("strike_money_rrg_partner.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        components.html(html_content, height=900, scrolling=True)
    else:
        st.error("The local 'strike_money_rrg_partner.html' file was not found in the workspace.")

# TAB 3: METHODOLOGY & GUIDE
with tab3:
    st.subheader("📚 Relative Rotation Graphs (RRG) Explained")
    st.markdown("""
    ### What is an RRG?
    Developed by **Julius de Kempenaer**, **Relative Rotation Graphs (RRG)** are financial charts used to visualize relative strength and momentum relationships between multiple assets (like sectors or individual stocks) against a common benchmark index (such as the S&P 500 or NIFTY 50).
    
    Instead of plotting stock price trends, RRG maps price movements relative to the index along two key indicators:
    
    1. **RS-Ratio (X-Axis):** Represents the relative strength of the asset against the benchmark. A value over 100 indicates outperformance, while a value below 100 indicates underperformance.
    2. **RS-Momentum (Y-Axis):** Measures the rate of change or trend direction of relative strength. A value over 100 indicates strong upward momentum, while a value under 100 indicates weakening momentum.
    
    ---
    
    ### Understanding the Quadrants
    Assets typically rotate clockwise through these four stages:
    
    * **🟢 LEADING (Top-Right):** Outperforming the benchmark with strong upward momentum. Highly bullish. Optimal for trend followers.
    * **🟡 WEAKENING (Bottom-Right):** Still outperforming the benchmark, but momentum has topped out and is actively decelerating. Price might consolidate.
    * **🔴 LAGGING (Bottom-Left):** Underperforming the benchmark with continuing downward momentum. Avoid or short.
    * **🔵 IMPROVING (Top-Left):** Underperforming the benchmark, but momentum has bottomed out and is recovering. Perfect for early-stage breakout buyers.
    
    ---
    
    ### Mathematical Calculations (JdK Index Model)
    The JdK system utilizes double exponential smoothing and standard deviation normalization:
    
    $$RS_t = \\frac{\\text{Close}_{\\text{Asset}, t}}{\\text{Close}_{\\text{Benchmark}, t}} \\times 100$$
    
    $$RS\\_Ratio_t = 100 + \\left( \\frac{RS_t - \\text{Rolling Mean}(RS_t, n)}{\\text{Rolling StdDev}(RS_t, n)} \\right) \\times 10$$
    
    $$RS\\_Momentum_t = 100 + \\left( \\frac{\\text{ROC}(RS\\_Ratio_t, 1) - \\text{Rolling Mean}(\\text{ROC}, n)}{\\text{Rolling StdDev}(\\text{ROC}, n)} \\right) \\times 10$$
    
    *Where $n$ represents the user-selected Smoothing Window.*
    """)
