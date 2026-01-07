import streamlit as st
import pandas as pd
import time
from bot_logic import TradingBot
import plotly.express as px
from datetime import datetime

# Page Config
st.set_page_config(
    page_title="Solana Sniper Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional UI Styling
st.markdown("""
<style>
    /* Force Light Theme Overrides */
    .stApp {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Input Borders Red - Field and Buttons */
    .stNumberInput input {
        background-color: #f0f5f1 !important;
        color: #000000 !important;
        border-right: 1px solid #ccc !important;
    }
    .stNumberInput button {
        background-color: #f0f5f1 !important;
        color: #000000 !important;
    }
    
    /* Text Colors */
    h1, h2, h3, p, div, span {
        color: #000000 !important;
    }
    
    /* Metrics Override */
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        color: #000000 !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #555555 !important;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #ccc;
    }
    .stButton>button:hover {
        background-color: #ff4b4b !important;
        color: #ffffff !important;
        border-color: #ff4b4b !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #f0f0f0 !important;
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Bot
if 'bot' not in st.session_state:
    st.session_state.bot = TradingBot()
bot = st.session_state.bot

if 'scanner_running' not in st.session_state:
    st.session_state.scanner_running = False

# --- SIDEBAR: CONTROLS ---
with st.sidebar:
    st.title("⚡ Sniper Config")
    
    with st.expander("Strategy Settings", expanded=True):
        bot.trade_amount = st.number_input("Trade Amount (SOL)", 0.1, 10.0, bot.trade_amount)
        bot.profit_target = st.slider("Take Profit (%)", 5, 200, int(bot.profit_target*100)) / 100
        bot.stop_loss = st.slider("Stop Loss (%)", -90, -5, int(bot.stop_loss*100)) / 100
        bot.min_liquidity = st.number_input("Min Liquidity ($)", 1000, 500000, bot.min_liquidity)
        bot.min_score = st.slider("Min Score (Strength)", 50, 100, bot.min_score)

    with st.expander("Wallet Actions", expanded=False):
        deposit_amount = st.number_input("Deposit SOL", 0.0, 1000.0, 0.0)
        if st.button("Add Funds"):
            if deposit_amount > 0:
                bot.deposit_sol(deposit_amount)
                st.success(f"Added {deposit_amount} SOL")
                time.sleep(1)
                st.rerun()

    st.divider()
    
    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("▶ Start", type="primary", use_container_width=True):
        st.session_state.scanner_running = True
        st.rerun()
    if col_btn2.button("⏹ Stop", type="secondary", use_container_width=True):
        st.session_state.scanner_running = False
        st.rerun()

    status_color = "green" if st.session_state.scanner_running else "red"
    st.markdown(f"**Status:** <span style='color:{status_color}'>{'Running' if st.session_state.scanner_running else 'Stopped'}</span>", unsafe_allow_html=True)

# --- SCANNING LOGIC ---
if st.session_state.scanner_running:
    new_tokens = bot.fetch_new_tokens()
    for token in new_tokens:
        addr = token['tokenAddress']
        if addr not in bot.seen_tokens:
            bot.seen_tokens.add(addr)
            
            pair_data = bot.get_token_details(addr)
            if pair_data:
                strength, score = bot.analyze_token(pair_data)
                
                # Log to DB
                scan_data = {
                    'address': addr,
                    'symbol': token.get('header', 'Unknown') if 'header' in token else pair_data['baseToken']['symbol'],
                    'icon': token.get('icon', None),
                    'liquidity': float(pair_data.get('liquidity', {}).get('usd', 0)),
                    'score': score,
                    'strength': strength,
                    'time': datetime.now().isoformat()
                }
                bot.db.log_scan(scan_data)
                
                # Auto Trade
                if strength == 'STRONG':
                    if bot.enter_position(token, pair_data):
                        st.toast(f"Snipe! Bought {scan_data['symbol']}", icon="🎯")

    # Update Active Positions
    bot.update_positions()

# --- MAIN DASHBOARD ---
st.title("SOLANA SNIPER TERMINAL")

# 1. Stats Row
stats_cols = st.columns(4)
with stats_cols[0]:
    st.metric("Wallet Balance", f"{bot.balance:.4f} SOL")
with stats_cols[1]:
    st.metric("Active Positions", len(bot.positions))
with stats_cols[2]:
    st.metric("Total Trades", len(bot.history))
with stats_cols[3]:
    pnl_total = sum(t['pnl'] for t in bot.history)
    st.metric("Total PnL", f"{pnl_total:.4f} SOL", delta_color="normal")

# 2. Main Workspace
tab1, tab2, tab3 = st.tabs(["📡 Live Feed", "📜 Active Positions", "📜 Trade History"])

with tab1:
    st.subheader("Market Scanner")
    # Fetch recent scans from DB
    recent_scans = bot.db.get_recent_scans(limit=20)
    if recent_scans:
        df_scan = pd.DataFrame(recent_scans)
        st.dataframe(
            df_scan[['time', 'icon', 'symbol', 'strength', 'score', 'liquidity']],
            column_config={
                "icon": st.column_config.ImageColumn("Icon", width="small"),
                "liquidity": st.column_config.NumberColumn("Liquidity", format="$%.2f"),
                "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
                "time": st.column_config.DatetimeColumn("Detected At", format="HH:mm:ss")
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )
    else:
        st.info("Scanner waiting for data...")

with tab2:
    st.subheader("Active Positions")
    positions = bot.positions
    if positions:
        df_pos = pd.DataFrame(positions)
        
        # Format PnL colors
        def color_pnl(val):
            color = 'green' if val >= 0 else 'red'
            return f'color: {color}'

        # Display dataframe with styling
        st.dataframe(
            df_pos[['symbol', 'avg_entry_price', 'current_price', 'pnl', 'pnl_pct']].rename(columns={'avg_entry_price': 'Entry Price', 'current_price': 'Current Price', 'pnl': 'PnL (SOL)', 'pnl_pct': 'PnL %', 'symbol': 'Symbol'}).style.format({
                'Entry Price': '{:.8f}',
                'Current Price': '{:.8f}',
                'PnL (SOL)': '{:.4f}',
                'PnL %': '{:.2f}%'
            }).map(color_pnl, subset=['PnL (SOL)', 'PnL %']),
            use_container_width=True,
            height=500
        )
    else:
        st.caption("No active trades.")

with tab3:
    history = bot.history
    if history:
        df_hist = pd.DataFrame(history)
        st.dataframe(
            df_hist[['entry_time', 'symbol', 'reason', 'pnl', 'pnl_pct']],
            column_config={
                "pnl_pct": st.column_config.NumberColumn("PnL %", format="%.2f%%"),
                "pnl": st.column_config.NumberColumn("PnL (SOL)", format="%.4f")
            },
            use_container_width=True
        )
    else:
        st.text("History empty.")

# Auto-refresh loop
if st.session_state.scanner_running or bot.positions:
    time.sleep(3)
    st.rerun()
