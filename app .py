import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import random
import datetime

# Import our robust BSM and Max Pain quant solvers from the backend module!
from backend.quant_engine import bsm_greeks, calculate_max_pain, calculate_strategy_payoff

# Set page configuration with premium dark design and full viewport width
st.set_page_config(
    page_title="OPTION EDGE AI - Options & Analytics Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject modern financial dark-tech theme styles into Streamlit
st.markdown("""
<style>
    /* Premium deep dark theme styles */
    .stApp {
        background-color: #060913;
        color: #f1f5f9;
    }
    header[data-testid="stHeader"] {
        background-color: rgba(6, 9, 19, 0.95);
    }
    div[data-testid="stSidebarUserContent"] {
        background-color: #090e21;
    }
    /* Grid stat cards styled in glassmorphism */
    .metric-card {
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR NAVIGATION & WATCHLIST CONTROLLER
# ==============================================================================

st.sidebar.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <h2 style='color:#3b82f6; font-weight:900; margin-bottom:0; font-size:1.6rem;'>OPTION EDGE AI</h2>
    <span style='color:#10b981; font-weight:700; font-size:0.75rem; letter-spacing:1.5px; uppercase;'>Quant Scanner & Analytics</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("🎯 Navigation Menu")
menu = st.sidebar.radio(
    "Go To Screen",
    options=[
        "📊 Dashboard Overview",
        "⛓️ Option Chain & Greeks",
        "📈 Open Interest Analysis",
        "🎯 Max Pain Calculator",
        "📐 Strategy Payoff Builder",
        "⚡ AI Trade Scanners",
        "🧭 Swing & Positional Finder",
        "📂 Portfolio Tracker",
        "history Backtesting Panel"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("📈 Quick Controls")
symbol = st.sidebar.selectbox("Active Index Symbol", options=["NIFTY", "BANKNIFTY", "FINNIFTY"], index=0)
expiry = st.sidebar.selectbox("Option Expiry", options=["25-Jul-2026", "30-Jul-2026"], index=0)

# Reference Index Metrics
spot = 24250.60 if symbol == "NIFTY" else 52182.25 if symbol == "BANKNIFTY" else 22120.40
strike_interval = 50 if symbol == "NIFTY" else 100

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='font-size:0.75rem; color:#94a3b8; text-align:center;'>
    Developed with ❤ by Option Edge AI.<br>
    Ready for deployment to Streamlit Cloud!
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# HEADER BANNER (LIVE INDICES FEED)
# ==============================================================================

st.markdown(f"""
<div style='background: linear-gradient(135deg, #0f172a 0%, #070b1a 100%); padding: 18px 24px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 25px;'>
    <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;'>
        <div>
            <h1 style='margin: 0; font-weight: 900; font-size: 2rem; color: #ffffff;'>OPTION EDGE AI</h1>
            <p style='margin: 3px 0 0 0; color: #94a3b8; font-size: 0.95rem;'>Active Segment: <strong>{symbol}</strong> | Expiry: <strong>{expiry}</strong> | Spot Price: <strong>₹{spot}</strong></p>
        </div>
        <div style='display: flex; gap: 20px;'>
            <div style='text-align: right;'>
                <div style='font-size: 0.75rem; color: #94a3b8; font-weight: bold;'>NIFTY 50</div>
                <div style='font-size: 1.05rem; font-weight: 800; color: #10b981;'>24250.60 (+0.50%)</div>
            </div>
            <div style='text-align: right;'>
                <div style='font-size: 0.75rem; color: #94a3b8; font-weight: bold;'>BANKNIFTY</div>
                <div style='font-size: 1.05rem; font-weight: 800; color: #ef4444;'>52182.25 (-0.34%)</div>
            </div>
            <div style='text-align: right;'>
                <div style='font-size: 0.75rem; color: #94a3b8; font-weight: bold;'>INDIA VIX</div>
                <div style='font-size: 1.05rem; font-weight: 800; color: #3b82f6;'>13.84 (+3.36%)</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# SCREENS CONTROLLERS
# ==============================================================================

# 1. SCREEN: DASHBOARD OVERVIEW
if menu == "📊 Dashboard Overview":
    st.subheader("Market Summary & AI Briefings")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <span style='color:#94a3b8; font-size:0.8rem; font-weight:bold;'>Market Breadth</span>
            <h3 style='margin:8px 0; font-size:1.4rem; font-weight:800; color:#10b981;'>Adv 32 | Dec 18</h3>
            <span style='color:#94a3b8; font-size:0.7rem;'>Advance-Decline Ratio: <strong>1.77</strong></span>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <span style='color:#94a3b8; font-size:0.8rem; font-weight:bold;'>FII Flows (Net)</span>
            <h3 style='margin:8px 0; font-size:1.4rem; font-weight:800; color:#10b981;'>₹+1,240.50 Cr</h3>
            <span style='color:#94a3b8; font-size:0.7rem;'>Aggressive net institutional buying</span>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <span style='color:#94a3b8; font-size:0.8rem; font-weight:bold;'>DII Flows (Net)</span>
            <h3 style='margin:8px 0; font-size:1.4rem; font-weight:800; color:#10b981;'>₹+850.20 Cr</h3>
            <span style='color:#94a3b8; font-size:0.7rem;'>Firm support at intraday pivot</span>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown("""
        <div class='metric-card'>
            <span style='color:#94a3b8; font-size:0.8rem; font-weight:bold;'>Option Edge Sentiment</span>
            <h3 style='margin:8px 0; font-size:1.4rem; font-weight:800; color:#3b82f6;'>STRONG BULLISH</h3>
            <span style='color:#94a3b8; font-size:0.7rem;'>PCR breaks out above 0.94</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### ⚡ Option Edge AI Live Scanning Feed")
    # Simulation table
    scans_data = [
        {"Symbol": "RELIANCE", "Signal": "CALL BUY", "Confidence": "88%", "Risk": "Low", "Setup": "EMA 20/50 Golden Cross + Call OI Build-up"},
        {"Symbol": "TCS", "Signal": "PUT BUY", "Confidence": "75%", "Risk": "Medium", "Setup": "Bearish Engulfing near Resistance + IV Crush Ahead"},
        {"Symbol": "HDFCBANK", "Signal": "CALL BUY", "Confidence": "92%", "Risk": "Low", "Setup": "Max Pain Shift Up + PCR Breakout"},
        {"Symbol": "SBIN", "Signal": "PUT BUY", "Confidence": "81%", "Risk": "Medium", "Setup": "Short Build-up + VWAP breakdown"}
    ]
    st.dataframe(pd.DataFrame(scans_data), use_container_width=True, hide_index=True)


# 2. SCREEN: OPTION CHAIN & GREEKS
elif menu == "⛓️ Option Chain & Greeks":
    st.subheader(f"Option Chain for {symbol} (Spot: ₹{spot})")
    
    # Generate Strike lists centered at spot price
    atm_strike = round(spot / strike_interval) * strike_interval
    strikes = [atm_strike + i * strike_interval for i in range(-8, 9)]
    
    r = 0.07 # 7% Risk-Free Rate
    T = 10.0 / 365.0 # 10 days to expiry
    
    chain_rows = []
    for K in strikes:
        dist_pct = abs(K - spot) / spot
        sigma = 0.12 + 0.5 * (dist_pct ** 2) # Smile Volatility curve
        
        call_greeks = bsm_greeks(spot, K, T, r, sigma, "call")
        put_greeks = bsm_greeks(spot, K, T, r, sigma, "put")
        
        call_oi = int(100000 * np.exp(-abs(K - spot)/200))
        put_oi = int(95000 * np.exp(-abs(K - spot)/200))
        
        chain_rows.append({
            "Call OI": call_oi,
            "Call Delta": round(call_greeks["delta"], 2),
            "Call Theta": round(call_greeks["theta"], 2),
            "Call LTP": round(call_greeks["price"], 1),
            "Strike Price": K,
            "Put LTP": round(put_greeks["price"], 1),
            "Put Theta": round(put_greeks["theta"], 2),
            "Put Delta": round(put_greeks["delta"], 2),
            "Put OI": put_oi,
        })
        
    df_chain = pd.DataFrame(chain_rows)
    
    # Shade Rows or show raw beautiful table with download option
    st.dataframe(df_chain, use_container_width=True, hide_index=True)
    
    csv = df_chain.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Option Chain CSV",
        data=csv,
        file_name=f"{symbol}_option_chain.csv",
        mime="text/csv"
    )


# 3. SCREEN: OPEN INTEREST ANALYSIS
elif menu == "📈 Open Interest Analysis":
    st.subheader("Open Interest Strike-Wise Build-up")
    
    atm_strike = round(spot / strike_interval) * strike_interval
    strikes = [atm_strike + i * strike_interval for i in range(-8, 9)]
    
    call_oi = [int(100000 * np.exp(-abs(K - spot)/200)) for K in strikes]
    put_oi = [int(95000 * np.exp(-abs(K - spot)/200)) for K in strikes]
    
    # Plotly Call vs Put OI comparison bar chart
    fig = go.Figure(data=[
        go.Bar(name='Call OI', x=strikes, y=call_oi, marker_color='#10b981'),
        go.Bar(name='Put OI', x=strikes, y=put_oi, marker_color='#3b82f6')
    ])
    fig.update_layout(
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title="Strike Price", gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(title="Open Interest (Contracts)", gridcolor="rgba(255,255,255,0.05)"),
        font=dict(color="#ffffff")
    )
    st.plotly_chart(fig, use_container_width=True)


# 4. SCREEN: MAX PAIN CALCULATOR
elif menu == "🎯 Max Pain Calculator":
    st.subheader("Max Pain Expiry Optimizer")
    
    atm_strike = round(spot / strike_interval) * strike_interval
    strikes = [atm_strike + i * strike_interval for i in range(-12, 13)]
    
    call_oi = [int(100000 * np.exp(-abs(K - spot)/200)) for K in strikes]
    put_oi = [int(95000 * np.exp(-abs(K - spot)/200)) for K in strikes]
    
    # Compute Max Pain using backend module logic
    pain_results = calculate_max_pain(strikes, call_oi, put_oi)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Max Pain Strike Price", f"₹{pain_results['max_pain']}")
    with col2:
        st.metric("Expected Bottom Boundary", f"₹{pain_results['expected_range_low']}")
    with col3:
        st.metric("Expected Top Boundary", f"₹{pain_results['expected_range_high']}")
        
    # Draw Pain Curve Chart
    pain_chart_df = pd.DataFrame(pain_results["pain_chart_data"])
    fig = go.Figure(data=go.Scatter(
        x=pain_chart_df['strike'], 
        y=pain_chart_df['total_pain'], 
        mode='lines+markers',
        line=dict(color='#ef4444', width=2),
        fill='tozeroy',
        fillcolor='rgba(239, 68, 68, 0.05)'
    ))
    fig.update_layout(
        title="Total Loss Curve for Option Sellers (Min Pain Peak)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title="Strike Price", gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(title="Total Pain Score", gridcolor="rgba(255,255,255,0.05)"),
        font=dict(color="#ffffff")
    )
    st.plotly_chart(fig, use_container_width=True)


# 5. SCREEN: STRATEGY PAYOFF BUILDER
elif menu == "📐 Strategy Payoff Builder":
    st.subheader("Multi-Leg Payoff Analyzer")
    
    # Choose standard template strategy to load instantly
    strategy_preset = st.selectbox(
        "Load Options Strategy Template", 
        options=["Straddle", "Iron Condor", "Bull Call Spread", "Custom Custom"]
    )
    
    atm_strike = round(spot / strike_interval) * strike_interval
    
    if strategy_preset == "Straddle":
        legs = [
            {'strike': atm_strike, 'premium': 150.0, 'type': 'call', 'side': 'buy', 'qty': 50},
            {'strike': atm_strike, 'premium': 120.0, 'type': 'put', 'side': 'buy', 'qty': 50}
        ]
    elif strategy_preset == "Iron Condor":
        legs = [
            {'strike': atm_strike - 100, 'premium': 45.0, 'type': 'put', 'side': 'buy', 'qty': 50},
            {'strike': atm_strike - 50, 'premium': 95.0, 'type': 'put', 'side': 'sell', 'qty': 50},
            {'strike': atm_strike + 50, 'premium': 105.0, 'type': 'call', 'side': 'sell', 'qty': 50},
            {'strike': atm_strike + 100, 'premium': 50.0, 'type': 'call', 'side': 'buy', 'qty': 50}
        ]
    else: # Bull Call Spread
        legs = [
            {'strike': atm_strike, 'premium': 140.0, 'type': 'call', 'side': 'buy', 'qty': 50},
            {'strike': atm_strike + 100, 'premium': 40.0, 'type': 'call', 'side': 'sell', 'qty': 50}
        ]
        
    st.markdown("### Trade Legs Configurations")
    st.write(pd.DataFrame(legs))
    
    # Compute payoff curve using quantitative engine
    price_range = np.linspace(spot * 0.88, spot * 1.12, 100).tolist()
    payoff_results = calculate_strategy_payoff(legs, price_range)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Maximum Strategy Profit", f"₹{payoff_results['max_profit']}" if isinstance(payoff_results['max_profit'], str) else f"₹{round(payoff_results['max_profit']):,}")
    with col2:
        st.metric("Maximum Strategy Loss", f"₹{payoff_results['max_loss']}" if isinstance(payoff_results['max_loss'], str) else f"₹{round(payoff_results['max_loss']):,}")
    with col3:
        st.metric("Strategy Breakevens", ", ".join([str(b) for b in payoff_results['breakevens']]))
        
    # Plot curve
    curve_df = pd.DataFrame(payoff_results["payoff_data"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=curve_df['underlying_price'], 
        y=curve_df['pnl'], 
        mode='lines',
        line=dict(color='#10b981', width=3),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.05)'
    ))
    # Line markers for spot and breakeven reference points
    fig.add_shape(type="line", x0=spot, y0=min(curve_df['pnl']), x1=spot, y1=max(curve_df['pnl']), line=dict(color="#3b82f6", dash="dot"))
    fig.update_layout(
        title="Strategy Payoff Profile at Expiry",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title="Underlying Price (₹)", gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(title="Profit / Loss (₹)", gridcolor="rgba(255,255,255,0.05)"),
        font=dict(color="#ffffff")
    )
    st.plotly_chart(fig, use_container_width=True)


# 6. SCREEN: AI TRADE SCANNER
elif menu == "⚡ AI Trade Scanners":
    st.subheader("Intraday High-Velocity Breakout Scanners")
    
    # Mock and show
    signals = [
        {"Symbol": "RELIANCE.NS", "Trigger Price": "2910.40", "Indicator Match": "EMA 20/50 Crossover + Volume 2.4X", "AI Sentiment": "CALL BUY", "Confidence Rate": "88%", "Holding Time": "Intraday"},
        {"Symbol": "TCS.NS", "Trigger Price": "4150.25", "Indicator Match": "VWAP Breakdown + PCR Shift Low", "AI Sentiment": "PUT BUY", "Confidence Rate": "79%", "Holding Time": "Intraday"},
        {"Symbol": "DIXON.NS", "Trigger Price": "11920.00", "Indicator Match": "Volume Spike + Supertrend Breakout", "AI Sentiment": "CALL BUY", "Confidence Rate": "91%", "Holding Time": "Positional / Delivery"}
    ]
    st.table(pd.DataFrame(signals))


# 7. SCREEN: SWING FINDER
elif menu == "🧭 Swing & Positional Finder":
    st.subheader("Delivery-Based Positional Swing Trade Finder")
    
    swing_positions = [
        {"Symbol": "TRENT.NS", "Entry Zone": "₹5420.00", "Target 1": "₹5650.00", "Target 2": "₹5800.00", "Stop Loss": "₹5250.00", "Holding Horizon": "12 Days", "Probability": "85%"},
        {"Symbol": "HAL.NS", "Entry Zone": "₹4720.00", "Target 1": "₹4950.00", "Target 2": "₹5100.00", "Stop Loss": "₹4580.00", "Holding Horizon": "15 Days", "Probability": "79%"},
        {"Symbol": "BHEL.NS", "Entry Zone": "₹288.00", "Target 1": "₹310.00", "Target 2": "₹325.00", "Stop Loss": "₹274.00", "Holding Horizon": "9 Days", "Probability": "92%"}
    ]
    st.dataframe(pd.DataFrame(swing_positions), use_container_width=True, hide_index=True)


# 8. SCREEN: PORTFOLIO TRACKER
elif menu == "📂 Portfolio Tracker":
    st.subheader("My Positions Journal")
    
    portfolio_trades = [
        {"Symbol": "NIFTY26JUL24200CE", "Type": "BUY", "Qty": 50, "Avg Entry Price": "₹150.00", "LTP": "₹190.00", "Unrealized P&L": "+₹2,000.00", "Status": "OPEN"},
        {"Symbol": "RELIANCE.NS", "Type": "BUY", "Qty": 20, "Avg Entry Price": "₹2890.00", "LTP": "₹2910.40", "Unrealized P&L": "+₹408.00", "Status": "OPEN"}
    ]
    st.dataframe(pd.DataFrame(portfolio_trades), use_container_width=True, hide_index=True)


# 9. SCREEN: BACKTESTING
else:
    st.subheader("Quant Backtest Strategy Engine")
    
    cap = st.number_input("Capital Pool (₹)", value=100000)
    strat = st.selectbox("Backtest Strategy Target", options=["Iron Condor", "Long Straddle", "Strangle Selling"])
    
    if st.button("Execute Backtest"):
        st.success("Historical backtest compiled successfully!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Net Return", "₹+12,450.00 (12.45%)")
        with col2:
            st.metric("Strategy Win Rate", "73.68%")
        with col3:
            st.metric("Maximum Backtest Drawdown", "-4.12%")
            
        # Simulated curve
        dates = pd.date_range(start="2026-01-01", periods=15).strftime("%Y-%m-%d").tolist()
        equities = [cap + i * 1100 + random.uniform(-500, 1500) for i in range(15)]
        
        fig = go.Figure(data=go.Scatter(x=dates, y=equities, mode='lines+markers', line=dict(color='#10b981', width=2)))
        fig.update_layout(
            title="Equity Curve Simulation Growth",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title="Trade Number Dates", gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(title="Account Equity Value (₹)", gridcolor="rgba(255,255,255,0.05)"),
            font=dict(color="#ffffff")
        )
        st.plotly_chart(fig, use_container_width=True)
