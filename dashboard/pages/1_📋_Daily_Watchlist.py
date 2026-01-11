"""
Daily Watchlist - Today's Trade Signals

Shows current setups across all enabled strategies
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from config.config import UNIVERSES
from config.strategy_registry import STRATEGY_REGISTRY, get_enabled_strategies
from scripts.data_management.fetch_data import load_data

# Import strategy classes
from strategies.ma101_strategy import MA101Strategy
from strategies.donchian_strategy import DonchianStrategy
from strategies.swing_trading_strategy import SwingTradingStrategy
from strategies.qullamaggie_htf_strategy import QullamaggieHTFStrategy

# Page config
st.set_page_config(page_title="Daily Watchlist", page_icon="📋", layout="wide")

# Title
st.title("📋 Daily Watchlist")
st.markdown(f"**{datetime.now().strftime('%A, %B %d, %Y - %I:%M %p')}**")
st.markdown("---")

# Strategy mapping
STRATEGY_CLASSES = {
    'ma101_burns': MA101Strategy,
    'donchian_breakout': DonchianStrategy,
    'swing_trading_burns': SwingTradingStrategy,
    'qullamaggie_htf': QullamaggieHTFStrategy
}

# Sidebar filters
with st.sidebar:
    st.header("⚙️ Filters")
    
    # Strategy selection
    enabled_strategies = get_enabled_strategies()
    available_strategies = [s for s in enabled_strategies if s in STRATEGY_CLASSES]
    
    selected_strategies = st.multiselect(
        "Strategies",
        available_strategies,
        default=available_strategies,
        format_func=lambda x: STRATEGY_REGISTRY[x]['name']
    )
    
    # Universe selection
    universe_options = list(UNIVERSES.keys())
    selected_universe = st.selectbox(
        "Symbol Universe",
        universe_options,
        index=0
    )
    
    # Additional filters
    st.markdown("---")
    min_risk = st.number_input("Min Risk/Share ($)", value=0.0, step=0.5)
    max_risk = st.number_input("Max Risk/Share ($)", value=100.0, step=1.0)
    
    # Run scan button
    scan_button = st.button("🔍 Scan for Signals", type="primary", use_container_width=True)

# Main content
if scan_button or 'last_scan' not in st.session_state:
    with st.spinner("Scanning for signals..."):
        # Get symbols from selected universe
        symbols = UNIVERSES.get(selected_universe, ['SPY', 'QQQ', 'IWM'])
        
        if not symbols:
            st.warning(f"No symbols in universe: {selected_universe}")
            st.stop()
        
        # Collect all signals
        all_signals = []
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, symbol in enumerate(symbols):
            status_text.text(f"Scanning {symbol}... ({idx+1}/{len(symbols)})")
            progress_bar.progress((idx + 1) / len(symbols))
            
            try:
                # Load data
                df = load_data(symbol)
                
                if df.empty or len(df) < 200:
                    continue
                
                df['symbol'] = symbol
                
                # Run each selected strategy
                for strategy_id in selected_strategies:
                    if strategy_id not in STRATEGY_CLASSES:
                        continue
                    
                    try:
                        # Instantiate strategy
                        StrategyClass = STRATEGY_CLASSES[strategy_id]
                        strategy = StrategyClass()
                        
                        # Check for signal
                        signal = strategy.check_current_signal(df)
                        
                        if signal:
                            # Apply filters
                            if min_risk <= signal['risk_per_share'] <= max_risk:
                                signal['strategy_id'] = strategy_id
                                all_signals.append(signal)
                    
                    except Exception as e:
                        # Silently skip strategy errors
                        continue
            
            except Exception as e:
                # Silently skip symbol errors
                continue
        
        progress_bar.empty()
        status_text.empty()
        
        # Store results in session state
        st.session_state['last_scan'] = all_signals
        st.session_state['scan_time'] = datetime.now()

# Display results
if 'last_scan' in st.session_state:
    signals = st.session_state['last_scan']
    scan_time = st.session_state.get('scan_time', datetime.now())
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Signals", len(signals))
    
    with col2:
        unique_symbols = len(set(s['symbol'] for s in signals))
        st.metric("Unique Symbols", unique_symbols)
    
    with col3:
        if signals:
            avg_risk = sum(s['risk_per_share'] for s in signals) / len(signals)
            st.metric("Avg Risk/Share", f"${avg_risk:.2f}")
        else:
            st.metric("Avg Risk/Share", "—")
    
    with col4:
        minutes_ago = int((datetime.now() - scan_time).total_seconds() / 60)
        st.metric("Last Scan", f"{minutes_ago}m ago")
    
    st.markdown("---")
    
    # Display signals
    if signals:
        # Convert to DataFrame for display
        signals_df = pd.DataFrame(signals)
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Table View", "📈 By Strategy", "💰 By Risk"])
        
        with tab1:
            st.subheader("All Signals")
            
            # Format for display
            display_df = pd.DataFrame({
                'Symbol': signals_df['symbol'],
                'Strategy': signals_df['strategy_id'].map(
                    lambda x: STRATEGY_REGISTRY[x]['name'] if x in STRATEGY_REGISTRY else x
                ),
                'Signal': signals_df['signal'],
                'Entry': signals_df['entry_price'].map(lambda x: f"${x:.2f}"),
                'Stop': signals_df['stop_price'].map(lambda x: f"${x:.2f}"),
                'Risk/Share': signals_df['risk_per_share'].map(lambda x: f"${x:.2f}"),
                'Reason': signals_df['reason']
            })
            
            # Make rows clickable for details
            selected_row = st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Show detailed signal on click
            if st.checkbox("Show signal details"):
                selected_idx = st.selectbox(
                    "Select signal to view details:",
                    range(len(signals)),
                    format_func=lambda i: f"{signals[i]['symbol']} - {signals[i]['strategy']}"
                )
                
                if selected_idx is not None:
                    sig = signals[selected_idx]
                    
                    st.markdown("### Signal Details")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Symbol:** {sig['symbol']}")
                        st.markdown(f"**Strategy:** {sig['strategy']}")
                        st.markdown(f"**Signal:** {sig['signal']}")
                        st.markdown(f"**Entry Price:** ${sig['entry_price']:.2f}")
                        st.markdown(f"**Stop Price:** ${sig['stop_price']:.2f}")
                    
                    with col2:
                        st.markdown(f"**Risk/Share:** ${sig['risk_per_share']:.2f}")
                        if 'atr' in sig:
                            st.markdown(f"**ATR:** ${sig['atr']:.2f}")
                        if 'volume_ratio' in sig:
                            st.markdown(f"**Volume Ratio:** {sig['volume_ratio']:.1f}x")
                        st.markdown(f"**Date:** {sig['date']}")
                    
                    st.markdown(f"**Reason:** {sig['reason']}")
        
        with tab2:
            st.subheader("Signals by Strategy")
            
            # Group by strategy
            by_strategy = signals_df.groupby('strategy_id')
            
            for strategy_id, group in by_strategy:
                strategy_name = STRATEGY_REGISTRY.get(strategy_id, {}).get('name', strategy_id)
                
                with st.expander(f"**{strategy_name}** ({len(group)} signals)", expanded=True):
                    for _, sig in group.iterrows():
                        cols = st.columns([2, 2, 2, 2, 4])
                        cols[0].markdown(f"**{sig['symbol']}**")
                        cols[1].markdown(f"${sig['entry_price']:.2f}")
                        cols[2].markdown(f"${sig['stop_price']:.2f}")
                        cols[3].markdown(f"${sig['risk_per_share']:.2f}")
                        cols[4].markdown(f"_{sig['reason']}_")
        
        with tab3:
            st.subheader("Signals by Risk Level")
            
            # Sort by risk
            sorted_signals = sorted(signals, key=lambda x: x['risk_per_share'])
            
            # Group into risk buckets
            low_risk = [s for s in sorted_signals if s['risk_per_share'] < 1.0]
            med_risk = [s for s in sorted_signals if 1.0 <= s['risk_per_share'] < 3.0]
            high_risk = [s for s in sorted_signals if s['risk_per_share'] >= 3.0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 🟢 Low Risk (<$1)")
                if low_risk:
                    for sig in low_risk:
                        st.markdown(f"**{sig['symbol']}** - ${sig['risk_per_share']:.2f}")
                        st.caption(sig['strategy'])
                else:
                    st.info("No low-risk signals")
            
            with col2:
                st.markdown("### 🟡 Medium Risk ($1-3)")
                if med_risk:
                    for sig in med_risk:
                        st.markdown(f"**{sig['symbol']}** - ${sig['risk_per_share']:.2f}")
                        st.caption(sig['strategy'])
                else:
                    st.info("No medium-risk signals")
            
            with col3:
                st.markdown("### 🔴 High Risk (>$3)")
                if high_risk:
                    for sig in high_risk:
                        st.markdown(f"**{sig['symbol']}** - ${sig['risk_per_share']:.2f}")
                        st.caption(sig['strategy'])
                else:
                    st.info("No high-risk signals")
    
    else:
        st.info("🔍 No signals found. Try adjusting your filters or universe selection.")
        st.markdown("""
        **Tips:**
        - Expand your symbol universe
        - Enable more strategies
        - Adjust risk filters
        - Market may not be in a trending phase
        """)

else:
    st.info("👆 Click 'Scan for Signals' to generate today's watchlist")

# Footer
st.markdown("---")
st.caption("Signals are generated based on end-of-day data. Always verify setup before trading.")
