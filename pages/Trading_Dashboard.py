import MetaTrader5 as mt5
import streamlit as st
from mt5_connector import connect, place_order, get_account_balance, get_account_equity, calculate_lot_size, is_algorithmic_trading_enabled, get_open_positions, close_position, get_account_margin_info, get_available_symbols, check_pnl_constraint, can_place_order
from data import get_data
from strategy import compute_indicators, generate_signal, train_ml_model, load_ml_model
from risk_management import get_max_positions_limit, apply_session_filters, get_session_aware_symbols, get_session_aware_max_positions
import config
import logging
import pandas as pd
from typing import List, Dict
import time
import os
import csv
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)

# ============================================================================
# STATE PERSISTENCE FUNCTIONS - Save/Load Dashboard Controls Across Sessions
# ============================================================================

def get_state_file_path():
    """Get the path to the state persistence file."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state_dir = os.path.join(root_dir, "dashboard_state")
    if not os.path.exists(state_dir):
        os.makedirs(state_dir)
    return os.path.join(state_dir, "trading_dashboard_state.json")


def load_dashboard_state():
    """Load saved dashboard control state from file."""
    try:
        state_file = get_state_file_path()
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            logging.info("Dashboard state loaded from file")
            return state
        else:
            logging.info("No saved state found, using defaults")
            return None
    except Exception as e:
        logging.error(f"Failed to load dashboard state: {e}")
        return None


def save_dashboard_state(state_dict):
    """Save dashboard control state to file."""
    try:
        state_file = get_state_file_path()
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_dict, f, indent=2)
        logging.info("Dashboard state saved to file")
    except Exception as e:
        logging.error(f"Failed to save dashboard state: {e}")


def clear_dashboard_state():
    """Clear saved dashboard state and reset session state to defaults."""
    state_file = get_state_file_path()
    try:
        if os.path.exists(state_file):
            os.remove(state_file)
            logging.info("Dashboard state file removed")
    except Exception as e:
        logging.error(f"Failed to remove dashboard state: {e}")

    for key in get_default_state().keys():
        st.session_state.pop(key, None)

    st.experimental_rerun()


def get_default_state():
    """Get default values for all controls."""
    return {
        'auto_refresh': False,
        'refresh_interval': 10,
        'enable_auto_close': False,
        'auto_close_loss_pct': float(config.AUTO_CLOSE_MAX_LOSS_PERCENTAGE),
        'max_drawdown_pct': float(config.MAX_DRAWDOWN_PERCENTAGE * 100),
        'use_risk_management': False,
        'paper_trading': False,
        'auto_trade': False,
        'use_ml_signals': False,
        'timeframe': 'M5',
        'lot_size': config.LOT,
        'followed_symbol': config.SYMBOL,
    }


def initialize_session_state_from_saved():
    """Initialize session state with saved values or defaults."""
    saved_state = load_dashboard_state()
    defaults = get_default_state()
    
    # Merge saved state with defaults (saved values override defaults)
    merged_state = {**defaults, **(saved_state or {})}
    
    # Initialize session state keys if they don't exist
    for key, value in merged_state.items():
        if key not in st.session_state:
            st.session_state[key] = value
            logging.debug(f"Session state initialized: {key} = {value}")


def sync_state_to_file():
    """Save current session state to file."""
    state_dict = {
        'auto_refresh': st.session_state.get('auto_refresh', False),
        'refresh_interval': st.session_state.get('refresh_interval', 10),
        'enable_auto_close': st.session_state.get('enable_auto_close', False),
        'auto_close_loss_pct': st.session_state.get('auto_close_loss_pct', float(config.AUTO_CLOSE_MAX_LOSS_PERCENTAGE)),
        'max_drawdown_pct': st.session_state.get('max_drawdown_pct', float(config.MAX_DRAWDOWN_PERCENTAGE * 100)),
        'use_risk_management': st.session_state.get('use_risk_management', False),
        'paper_trading': st.session_state.get('paper_trading', False),
        'auto_trade': st.session_state.get('auto_trade', False),
        'use_ml_signals': st.session_state.get('use_ml_signals', False),
        'timeframe': st.session_state.get('timeframe', 'M5'),
        'lot_size': st.session_state.get('lot_size', config.LOT),
        'followed_symbol': st.session_state.get('followed_symbol', config.SYMBOL),
    }
    save_dashboard_state(state_dict)


def log_auto_trade_to_file(trade_data):
    """Log auto trade to daily CSV file."""
    try:
        # Create logs directory if it doesn't exist
        logs_dir = "auto_trade_logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Create filename with current date
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{logs_dir}/auto_trades_{today}.csv"
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.isfile(filename)
        
        # Add additional trade information
        trade_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'date': today,
            'time': trade_data['time'],
            'symbol': trade_data['symbol'],
            'signal': trade_data['signal'],
            'lot_size': trade_data['lot'],
            'score': trade_data['score'],
            'account_balance': get_account_balance(),
            'account_equity': get_account_equity(),
            'margin_info': str(get_account_margin_info())
        }
        
        # Write to CSV file
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'date', 'time', 'symbol', 'signal', 'lot_size', 'score', 'account_balance', 'account_equity', 'margin_info']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(trade_entry)
        
        logging.info(f"Auto trade logged to {filename}")
        
    except Exception as e:
        logging.error(f"Failed to log auto trade to file: {e}")

def generate_daily_summary(date_str):
    """Generate a summary report for a specific date."""
    try:
        logs_dir = "auto_trade_logs"
        filename = f"{logs_dir}/auto_trades_{date_str}.csv"
        
        if not os.path.exists(filename):
            return None
            
        df = pd.read_csv(filename)
        
        summary = {
            'date': date_str,
            'total_trades': len(df),
            'buy_trades': len(df[df['signal'] == 'BUY']),
            'sell_trades': len(df[df['signal'] == 'SELL']),
            'total_lots': df['lot_size'].sum(),
            'avg_score': df['score'].mean(),
            'symbols_traded': df['symbol'].unique().tolist(),
            'start_balance': df['account_balance'].iloc[0] if len(df) > 0 else 0,
            'end_balance': df['account_balance'].iloc[-1] if len(df) > 0 else 0,
            'start_equity': df['account_equity'].iloc[0] if len(df) > 0 else 0,
            'end_equity': df['account_equity'].iloc[-1] if len(df) > 0 else 0,
        }
        
        return summary
        
    except Exception as e:
        logging.error(f"Failed to generate daily summary: {e}")
        return None


def perform_auto_close(open_positions, auto_close_loss_pct, balance):
    """
    Perform auto-close on losing positions based on loss percentage threshold.
    
    Args:
        open_positions: List of open positions from MT5
        auto_close_loss_pct: Loss percentage threshold for auto-closing
        balance: Current account balance
        
    Returns:
        Tuple: (closed_count, closed_details)
    """
    closed_count = 0
    closed_details = []
    
    if not open_positions:
        return 0, []
    
    for position in list(open_positions):
        # Only consider losing positions
        if position.profit >= 0:
            continue
        
        # Calculate loss percentage relative to position entry value
        # This is more meaningful than % of total balance
        try:
            # For forex: position entry value = volume (in lots) * entry price * 100000 (standard lot size)
            position_entry_value = position.volume * position.price_open * 100000
            
            # Calculate loss as percentage of entry value
            if position_entry_value > 0:
                position_loss_pct = (abs(position.profit) / position_entry_value) * 100
            else:
                position_loss_pct = 0
            
            logging.info(f"Position {position.ticket} ({position.symbol}): Loss ${abs(position.profit):.2f} = {position_loss_pct:.2f}% of entry value. Threshold: {auto_close_loss_pct:.2f}%")
            
            # Close if loss exceeds threshold
            if position_loss_pct >= auto_close_loss_pct:
                logging.info(f"Auto-closing position {position.ticket}: Loss {position_loss_pct:.2f}% >= threshold {auto_close_loss_pct:.2f}%")
                try:
                    close_position(position)
                    closed_count += 1
                    
                    closed_details.append({
                        'ticket': position.ticket,
                        'symbol': position.symbol,
                        'loss': abs(position.profit),
                        'loss_pct': position_loss_pct,
                        'status': 'Closed'
                    })
                    
                    # Log auto-closed position
                    close_action = 'CLOSE-BUY' if position.type == mt5.ORDER_TYPE_BUY else 'CLOSE-SELL'
                    trade_time = time.strftime('%H:%M:%S', time.localtime())
                    log_auto_trade_to_file({
                        'time': trade_time,
                        'symbol': position.symbol,
                        'signal': close_action,
                        'lot': position.volume,
                        'score': 0  # Auto-close has no score
                    })
                    
                except Exception as e:
                    logging.error(f"Failed to close position {position.ticket}: {e}")
                    closed_details.append({
                        'ticket': position.ticket,
                        'symbol': position.symbol,
                        'loss': abs(position.profit),
                        'loss_pct': position_loss_pct,
                        'status': f'Error: {str(e)}'
                    })
        
        except Exception as e:
            logging.error(f"Error processing position {position.ticket}: {e}")
    
    return closed_count, closed_details


def display_auto_close_results(closed_count, closed_details):
    """Display auto-close results in the UI."""
    if closed_count == 0:
        st.sidebar.info("✅ Auto-close check complete. No positions met the close criteria.")
    else:
        st.sidebar.success(f"✅ Auto-closed {closed_count} position(s)!")
        
        # Show details in expander
        with st.sidebar.expander(f"📋 Details ({closed_count} closed)"):
            for detail in closed_details:
                if detail['status'] == 'Closed':
                    st.write(f"✅ {detail['symbol']} (#{detail['ticket']}): Loss ${detail['loss']:.2f} ({detail['loss_pct']:.2f}%)")
                else:
                    st.warning(f"❌ {detail['symbol']} (#{detail['ticket']}): {detail['status']}")


def main():
    """Main Streamlit page function."""
    import streamlit as st
    import plotly.graph_objects as go
    
    # Initialize session state from saved dashboard state
    initialize_session_state_from_saved()
    
    st.title("📊 Forex Algo Trading Dashboard")
    
    # Current trading session indicator
    try:
        session_info = apply_session_filters(10)  # Base value doesn't matter for session info
        session_name = session_info['session_name']
        session_multiplier = session_info['session_multiplier']
        is_weekend = session_info['is_weekend']
        
        # Color coding based on session
        if is_weekend:
            session_color = "⚫"  # Black for weekend
            session_status = "CLOSED"
        elif session_name == "London/NY Overlap":
            session_color = "🟢"  # Green for high liquidity
            session_status = "HIGH LIQUIDITY"
        elif session_name in ["London Session", "New York Session"]:
            session_color = "🟡"  # Yellow for good liquidity
            session_status = "ACTIVE"
        else:  # Asian Session
            session_color = "🔴"  # Red for low liquidity
            session_status = "LOW LIQUIDITY"
            
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <strong>{session_color} Current Session: {session_name}</strong> | 
            Status: {session_status} | 
            Position Limit Multiplier: {session_multiplier:.1f}x
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"⚠️ Could not determine current trading session: {e}")

    # Sidebar controls
    st.sidebar.header("⚙️ Trading Controls")

    # Auto-refresh controls
    st.sidebar.subheader("🔄 Auto Refresh")
    auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=st.session_state.get('auto_refresh', False), key='auto_refresh')
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, st.session_state.get('refresh_interval', 10), disabled=not auto_refresh, key='refresh_interval')
    
    # Defensive check: Ensure auto_refresh is properly set (should always be True after widget creation)
    if not isinstance(auto_refresh, bool):
        auto_refresh = False
        st.warning("⚠️ Auto-refresh widget returned invalid value, defaulting to disabled")

    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.rerun()

    if st.sidebar.button("♻️ Reset sidebar settings"):
        clear_dashboard_state()

    # Track manual interaction so refresh does not interrupt button clicks
    if 'manual_action' not in st.session_state:
        st.session_state.manual_action = False
    if 'processing_action' not in st.session_state:
        st.session_state.processing_action = False

    # Note: Do NOT reset manual_action flag here - it needs to persist through the script
    # until after all button actions have been processed (see end of main() function)
    
    # Initialize variables with defaults (in case of early exit or errors)
    trading_enabled = False
    pnl_constraint_breached = False
    pnl_constraint = None
    margin_info = {'margin': 0.0, 'free_margin': 0.0, 'margin_level': 0.0}
    open_positions = []
    max_pnl_percent = 0.75
    mt5_connection_successful = False
    balance = 0
    equity = 0
    drawdown = 0

    if 'followed_symbol' not in st.session_state:
        st.session_state.followed_symbol = config.SYMBOL

    # Initialize last refresh time
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()

    # Read sidebar controls early (required for account connection checks)
    enable_auto_close = st.sidebar.checkbox("Enable Auto-close", value=st.session_state.get('enable_auto_close', False), key='enable_auto_close')
    
    auto_close_loss_pct = st.sidebar.slider(
        "Close position loss threshold (%)",
        0.1,
        10.0,
        st.session_state.get('auto_close_loss_pct', float(config.AUTO_CLOSE_MAX_LOSS_PERCENTAGE)),
        0.1,
        disabled=not enable_auto_close,
        key='auto_close_loss_pct'
    )
    if enable_auto_close:
        st.sidebar.info(f"Auto-close is enabled. Losing positions at or above {auto_close_loss_pct:.1f}% loss will be closed.")
        if st.sidebar.button("Run Auto-Close Now"):
            st.session_state.trigger_auto_close_now = True
            st.rerun()
    else:
        st.sidebar.info("Auto-close is disabled. No losing positions will be auto-closed.")

    max_drawdown_pct = st.sidebar.slider("Max account drawdown (%)", 1.0, 50.0, st.session_state.get('max_drawdown_pct', float(config.MAX_DRAWDOWN_PERCENTAGE * 100)), 0.5, key='max_drawdown_pct')
    
    use_risk_management = st.sidebar.checkbox("Use Risk Management", value=st.session_state.get('use_risk_management', False), key='use_risk_management')
    
    paper_trading = st.sidebar.checkbox("Paper Trading Mode", value=st.session_state.get('paper_trading', False), key='paper_trading')

    # Account connection
    try:
        connect()
        balance = get_account_balance()
        equity = get_account_equity()
        drawdown = (balance - equity) / balance if balance > 0 else 0
        mt5_connection_successful = True

        st.sidebar.success("✅ MT5 Connected")
        st.sidebar.metric("Balance", f"${balance:.2f}")
        st.sidebar.metric("Equity", f"${equity:.2f}")
        st.sidebar.metric("Drawdown", f"{drawdown:.1%}")

        try:
            margin_info = get_account_margin_info()
        except Exception as e:
            margin_info = {'margin': 0.0, 'free_margin': 0.0, 'margin_level': 0.0}
            logging.error(f"Failed to get margin info: {e}")

        try:
            open_positions = get_open_positions()
        except Exception as e:
            open_positions = []
            logging.error(f"Failed to get open positions: {e}")

        if drawdown > max_drawdown_pct / 100:
            st.sidebar.error("⚠️ Maximum drawdown exceeded!")
            trading_enabled = False
            if enable_auto_close and open_positions:
                for position in list(open_positions):
                    try:
                        close_position(position)
                        st.sidebar.warning(f"⚠️ Auto-closed position {position.ticket} due to drawdown limit.")
                        # Log auto-closed position
                        close_action = 'CLOSE-BUY' if position.type == mt5.ORDER_TYPE_BUY else 'CLOSE-SELL'
                        trade_time = time.strftime('%H:%M:%S', time.localtime())
                        log_auto_trade_to_file({
                            'time': trade_time,
                            'symbol': position.symbol,
                            'signal': close_action,
                            'lot': position.volume,
                            'score': 0  # Auto-close has no score
                        })
                    except Exception as e:
                        logging.error(f"Failed to auto-close position {position.ticket}: {e}")
        else:
            trading_enabled = True

        algo_trading_enabled = is_algorithmic_trading_enabled()
        if not paper_trading and not algo_trading_enabled:
            trading_enabled = False
            st.sidebar.error("❌ MT5 algo trading is disabled. Live order execution is blocked until Algo Trading is enabled in MT5.")
            st.sidebar.info("💡 Enable Algo Trading in MT5 toolbar before using live auto/manual execution.")
        elif not paper_trading:
            st.sidebar.success("✅ MT5 Algo Trading is enabled for live execution.")

        max_positions_info = get_session_aware_max_positions()
        max_positions = max_positions_info['final_max_positions']
        current_positions = get_open_positions()
        positions_count = len(current_positions)
        
        st.sidebar.markdown(f"""<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <strong>📊 Position Limit:</strong> {positions_count}/{max_positions}<br>
            <small>{max_positions_info['breakdown']}</small>
        </div>""", unsafe_allow_html=True)
        if len(open_positions) >= max_positions:
            trading_enabled = False
            st.sidebar.error(f"❌ Max open positions reached ({len(open_positions)}/{max_positions}). New trades are blocked.")

        followed_symbol = st.session_state.get('followed_symbol', config.SYMBOL)
        symbol_info = mt5.symbol_info(followed_symbol)
        symbol_tick = mt5.symbol_info_tick(followed_symbol)
        spread_pips = None
        if symbol_info and symbol_tick:
            spread_pips = (symbol_tick.ask - symbol_tick.bid) / symbol_info.point

        st.sidebar.markdown('---')
        st.sidebar.subheader('⚙️ Live Execution Status')
        status_cols = st.sidebar.columns(3)
        status_cols[0].metric('Algo Trading', 'Enabled' if algo_trading_enabled else 'Disabled')
        status_cols[1].metric('Spread', f"{spread_pips:.2f} pips" if spread_pips is not None else 'N/A')
        status_cols[2].metric('Position Limit', f"{len(open_positions)}/{max_positions}")

        if spread_pips is not None and spread_pips > config.MAX_SPREAD_PIPS:
            st.sidebar.warning(f"⚠️ High spread on {followed_symbol}: {spread_pips:.2f} pips")
        if len(open_positions) >= max_positions:
            st.sidebar.warning('⚠️ Trading blocked until positions are reduced.')

        if enable_auto_close and open_positions:
            # Check if "Run Auto-Close Now" button was clicked or if we're in regular auto-close cycle
            should_auto_close = enable_auto_close or st.session_state.get('trigger_auto_close_now', False)
            
            if should_auto_close:
                closed_count, closed_details = perform_auto_close(open_positions, auto_close_loss_pct, balance)
                
                # Display results
                display_auto_close_results(closed_count, closed_details)
                
                # Reset the trigger flag
                if st.session_state.get('trigger_auto_close_now', False):
                    st.session_state.trigger_auto_close_now = False
                
                # Refresh positions after auto-close
                try:
                    open_positions = get_open_positions()
                except Exception as e:
                    logging.error(f"Failed to refresh open positions after auto-close: {e}")

    except Exception as e:
        st.sidebar.error(f"❌ MT5 Connection Failed: {e}")
        logging.error(f"MT5 connection error: {e}")
        st.warning("⚠️ Trading Dashboard is running in limited mode - Account connection unavailable")
        # Set defaults and continue instead of stopping
        mt5_connection_successful = False
        pnl_constraint = {
            'within_limits': False,
            'max_allowed_pnl': 0,
            'current_pnl': 0,
            'utilization_percent': 100,
            'exceeded_by': 0
        }
        pnl_constraint_breached = True

    # Check P/L constraint immediately after successful MT5 connection (only if connection succeeded)
    if mt5_connection_successful:
        try:
            pnl_constraint = check_pnl_constraint(max_pnl_percent)
            pnl_constraint_breached = not pnl_constraint['within_limits']
        except Exception as e:
            logging.error(f"Failed to check P/L constraint: {e}")
            # Keep the default constraint set earlier
    
    # Update trading_enabled based on P/L constraint
    if pnl_constraint_breached:
        trading_enabled = False

    # Trading parameters
    available_symbols = get_available_symbols() or config.AVAILABLE_SYMBOLS
    if not available_symbols:
        st.error("No symbols are available from MT5 or configuration.")
        available_symbols = ["EURUSD"]  # Provide a fallback symbol
        st.warning(f"Using fallback symbol: {available_symbols[0]}")

    default_symbol = st.session_state.get('followed_symbol', config.SYMBOL)
    selected_index = available_symbols.index(default_symbol) if default_symbol in available_symbols else 0
    symbol = st.sidebar.selectbox("Symbol", available_symbols, index=selected_index, key='followed_symbol')

    timeframe_options = {"M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5,
                        "M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1}
    saved_timeframe = st.session_state.get('timeframe', 'M5')
    timeframe_label = st.sidebar.selectbox("Timeframe", list(timeframe_options.keys()),
                                           index=list(timeframe_options.keys()).index(saved_timeframe), key='timeframe')
    timeframe = timeframe_options[timeframe_label]

    lot = st.sidebar.slider("Lot size", 0.01, 1.0, st.session_state.get('lot_size', config.LOT), key='lot_size')
    
    auto_trade = st.sidebar.checkbox("Enable Auto Trading", value=st.session_state.get('auto_trade', False), key='auto_trade')
    
    use_ml_signals = st.sidebar.checkbox("Use Machine Learning for Signals", value=st.session_state.get('use_ml_signals', False), key='use_ml_signals')

    # Auto trading status
    if auto_trade:
        st.sidebar.info("🤖 **Auto Trading Active**")
        st.sidebar.warning("⚠️ Manual trades may conflict with auto trades")
        if 'last_auto_trade_time' in st.session_state and st.session_state.last_auto_trade_time > 0:
            last_trade_time = time.strftime('%H:%M:%S', time.localtime(st.session_state.last_auto_trade_time))
            st.sidebar.text(f"Last auto trade: {last_trade_time}")
    else:
        st.sidebar.info("👤 Manual Trading Mode")

    # Check algorithmic trading status
    if not paper_trading:
        algo_trading_enabled = is_algorithmic_trading_enabled()
        if algo_trading_enabled:
            st.sidebar.success("✅ Algorithmic trading enabled")
        else:
            st.sidebar.error("❌ Algorithmic trading disabled")
            st.sidebar.info("💡 Enable 'Algo Trading' button in MT5 terminal")

    # Session-aware symbol filtering info
    if config.ENABLE_SESSION_AWARE_TRADING:
        session_info = apply_session_filters(10)
        active_symbols = get_session_aware_symbols(available_symbols)
        session_name = session_info['session_name']
        is_weekend = session_info['is_weekend']
        
        if is_weekend:
            st.sidebar.warning(f"🔴 {session_name} - All symbols available (low liquidity)")
        else:
            symbols_str = ", ".join(active_symbols)
            st.sidebar.info(f"📍 {session_name}: {symbols_str}")

    # Risk management
    if use_risk_management:
        try:
            calculated_lot = calculate_lot_size(balance, config.RISK_PERCENTAGE, config.STOP_LOSS_PIPS, symbol)
            lot = min(lot, calculated_lot)
            st.sidebar.info(f"📊 Calculated lot: {calculated_lot:.2f}")
        except Exception as e:
            st.sidebar.error(f"❌ Risk calculation failed: {e}")

    # Cache data
    @st.cache_data(ttl=300 if not auto_refresh else 10)
    def get_cached_data(symbol, timeframe):
        return get_data(symbol, timeframe)

    @st.cache_data(ttl=300 if not auto_refresh else 10)
    def get_cached_indicators(df):
        return compute_indicators(df)

    def compute_signal_strength(last_row):
        """Compute a simple ranking score for watchlist signals."""
        score = 0
        score += int(last_row['MACD'] > last_row['MACD_signal'])
        score += int(last_row['MACD_histogram'] > 0)
        score += int(last_row['SMA_short'] > last_row['SMA_long'])
        score += int(last_row['RSI'] < config.RSI_OVERSOLD or last_row['RSI'] > config.RSI_OVERBOUGHT)
        score += int(last_row.get('momentum_direction', 0) != 0)
        return score

    def evaluate_symbol(symbol, timeframe, use_ml):
        try:
            df_symbol = get_cached_data(symbol, timeframe)
            df_symbol = get_cached_indicators(df_symbol)
            watch_signal = generate_signal(df_symbol, use_ml=use_ml)
            score = compute_signal_strength(df_symbol.iloc[-1])
            return {
                'symbol': symbol,
                'signal': watch_signal,
                'score': score,
                'last_time': df_symbol['time'].iloc[-1],
                'error': None
            }
        except Exception as e:
            logging.warning(f"Skipping {symbol} in watchlist: {e}")
            return {
                'symbol': symbol,
                'signal': 'ERROR',
                'score': 0,
                'last_time': None,
                'error': str(e)
            }

    def scan_watchlist(symbols, timeframe, use_ml):
        return [evaluate_symbol(symbol, timeframe, use_ml) for symbol in symbols]

    def get_auto_trade_candidate(ranked_watchlist):
        """Return the first BUY/SELL candidate from the ranked watchlist that passes spread check."""
        skipped_symbols = []
        for item in ranked_watchlist:
            if item['signal'] in ["BUY", "SELL"] and item['score'] >= 2:
                # Check spread for this symbol
                try:
                    symbol_tick = mt5.symbol_info_tick(item['symbol'])
                    symbol_info = mt5.symbol_info(item['symbol'])
                    if symbol_info and symbol_tick:
                        spread_pips = (symbol_tick.ask - symbol_tick.bid) / symbol_info.point
                        if spread_pips <= config.MAX_SPREAD_PIPS:
                            if skipped_symbols:
                                logging.info(f"Selected {item['symbol']} for auto-trade (skipped {len(skipped_symbols)} due to high spread: {', '.join(skipped_symbols)})")
                            return item
                        else:
                            skipped_symbols.append(f"{item['symbol']}({spread_pips:.1f}pips)")
                            logging.debug(f"Skipping {item['symbol']} due to high spread: {spread_pips:.2f} pips (max: {config.MAX_SPREAD_PIPS})")
                    else:
                        # If we can't get spread info, assume it's tradable
                        if skipped_symbols:
                            logging.info(f"Selected {item['symbol']} for auto-trade (skipped {len(skipped_symbols)} due to high spread)")
                        return item
                except Exception as e:
                    logging.warning(f"Failed to check spread for {item['symbol']}: {e}")
                    # If spread check fails, still consider the candidate
                    if skipped_symbols:
                        logging.info(f"Selected {item['symbol']} for auto-trade (skipped {len(skipped_symbols)} due to high spread)")
                    return item
        if skipped_symbols:
            logging.info(f"No eligible auto-trade candidates: all {len(skipped_symbols)} signals had high spreads: {', '.join(skipped_symbols)}")
        return None

    def execute_trade(action, symbol, lot, paper_trading):
        """Execute a trade order."""
        try:
            if paper_trading:
                st.success(f"📝 Paper {action} order simulated - {lot} lots of {symbol}")
                return True  # Paper trades always "succeed"
            else:
                # Check if algorithmic trading is enabled
                if not is_algorithmic_trading_enabled():
                    st.error("❌ Algorithmic trading is disabled in MetaTrader 5 terminal. Please enable the 'Algo Trading' button in MT5.")
                    st.info("💡 To enable algorithmic trading: Open MetaTrader 5 → Click the 'Algo Trading' button in the toolbar → Make sure it's green/active")
                    return False

                if not paper_trading:
                    current_positions = get_open_positions()
                    max_positions_info = get_session_aware_max_positions()
                    max_positions_limit = max_positions_info['final_max_positions']
                    if len(current_positions) >= max_positions_limit:
                        st.error(f"❌ Cannot execute order: max open positions reached ({len(current_positions)}/{max_positions_limit}).")
                        return False

                order_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL
                place_order(symbol, lot, order_type, config.STOP_LOSS_PIPS, config.TAKE_PROFIT_PIPS)
                st.success(f"✅ {action} order executed - {lot} lots of {symbol}")
                return True  # Real trade succeeded
        except Exception as e:
            st.error(f"❌ Failed to execute {action} order: {e}")
            return False  # Trade failed

    # Load and process data
    try:
        df = get_cached_data(symbol, timeframe)
        df = get_cached_indicators(df)
        signal = generate_signal(df, use_ml=use_ml_signals)

        # Apply session-aware filtering to focus on symbols with active trading sessions
        session_filtered_symbols = get_session_aware_symbols(available_symbols)
        watchlist = scan_watchlist(session_filtered_symbols, timeframe, use_ml_signals)
        # Filter out symbols with data errors
        valid_watchlist = [item for item in watchlist if item['error'] is None]
        ranked_watchlist = sorted(
            valid_watchlist,
            key=lambda item: (item['signal'] != 'HOLD', item['score']),
            reverse=True
        )
        top_watchlist = ranked_watchlist[:3]

        st.sidebar.markdown('---')
        st.sidebar.subheader('📡 Watchlist Signals')
        st.sidebar.markdown(f"**Following:** {st.session_state.followed_symbol}")

        if ranked_watchlist:
            for item in ranked_watchlist[:10]:
                row1, row2, row3, row4 = st.sidebar.columns([2, 1, 1, 1])
                row1.markdown(f"**{item['symbol']}**")
                row2.markdown(f"`{item['signal']}`")
                row3.markdown(f"**{item['score']}**")

                if item['symbol'] == st.session_state.followed_symbol:
                    row4.button(f"✔ Following", disabled=True, key=f"follow_{item['symbol']}_current")
                else:
                    if row4.button(f"Follow {item['symbol']}", key=f"follow_{item['symbol']}"):
                        st.session_state.followed_symbol = item['symbol']
                        st.rerun()
        else:
            st.sidebar.info('No watchlist symbols available.')

        with st.sidebar.expander('All Symbols Watchlist'):
            st.dataframe(pd.DataFrame(watchlist), use_container_width=True)

        # Track signal changes for the currently selected symbol
        if 'previous_signal' not in st.session_state:
            st.session_state.previous_signal = signal
        
        signal_changed = signal != st.session_state.previous_signal
        st.session_state.previous_signal = signal

        # Auto trading logic based on the strongest watchlist candidate
        auto_candidate = get_auto_trade_candidate(ranked_watchlist)
        if auto_trade and auto_candidate and trading_enabled and not pnl_constraint_breached:
            if 'last_auto_trade_time' not in st.session_state:
                st.session_state.last_auto_trade_time = 0
            if 'last_auto_trade_candidate' not in st.session_state:
                st.session_state.last_auto_trade_candidate = None
            if 'auto_trade_history' not in st.session_state:
                st.session_state.auto_trade_history = []

            candidate_id = (auto_candidate['symbol'], auto_candidate['signal'])
            current_time = time.time()
            if candidate_id != st.session_state.last_auto_trade_candidate:
                if current_time - st.session_state.last_auto_trade_time > 30:
                    # Check P/L constraint before auto trade
                    symbol_info = mt5.symbol_info(auto_candidate['symbol'])
                    if symbol_info:
                        pip_value = 10 ** (1 - symbol_info.digits)
                        estimated_loss = config.STOP_LOSS_PIPS * pip_value * lot
                    else:
                        estimated_loss = 500 * lot
                    
                    order_check = can_place_order(estimated_loss, max_pnl_percent)
                    
                    if not order_check['can_place']:
                        st.sidebar.warning(f"⚠️ Auto trade blocked: {order_check['reason'][:100]}...")
                    else:
                        trade_time = time.strftime('%H:%M:%S', time.localtime(current_time))
                        st.sidebar.success(f"🤖 Auto {auto_candidate['signal']} executed for {auto_candidate['symbol']} at {trade_time}")
                        trade_success = execute_trade(auto_candidate['signal'], auto_candidate['symbol'], lot, paper_trading)

                        # Only update state and log if trade was actually successful
                        if trade_success:
                            st.session_state.last_auto_trade_time = current_time
                            st.session_state.last_auto_trade_candidate = candidate_id
                            
                            st.session_state.auto_trade_history.append({
                                'time': trade_time,
                                'signal': auto_candidate['signal'],
                                'lot': lot,
                                'symbol': auto_candidate['symbol'],
                                'score': auto_candidate['score']
                            })

                            # Log to daily file
                            log_auto_trade_to_file(st.session_state.auto_trade_history[-1])

                            if len(st.session_state.auto_trade_history) > 10:
                                st.session_state.auto_trade_history = st.session_state.auto_trade_history[-10:]

                            logging.info(f"Auto trade executed: {auto_candidate['signal']} {lot} lots of {auto_candidate['symbol']} (score {auto_candidate['score']})")
                        else:
                            logging.warning(f"Auto trade failed: {auto_candidate['signal']} {lot} lots of {auto_candidate['symbol']} (score {auto_candidate['score']})")
        elif auto_trade and not auto_candidate and trading_enabled and not pnl_constraint_breached:
            st.sidebar.info("🤔 No eligible auto-trade candidates found. All signals either have low scores or high spreads.")
        elif auto_trade and pnl_constraint_breached:
            st.sidebar.error("⚠️ Auto trading suspended - P/L limit exceeded")
        elif auto_trade and not trading_enabled:
            st.sidebar.warning("⚠️ Auto trading is suspended. Trading is currently disabled due to account safety checks or execution rules.")

    except Exception as e:
        st.error(f"❌ Failed to load data for {symbol}: {e}")
        st.info("💡 Try selecting a different symbol from the dropdown. Some symbols may not have historical data available.")
        logging.error(f"Data loading error for {symbol}: {e}")
        # Continue to show at least the risk dashboard instead of stopping completely
        st.warning("⚠️ Dashboard is partially unavailable. Showing account status only.")
        # Set defaults for display
        signal = "ERROR"
        df = pd.DataFrame()
        ranked_watchlist = []

    # Risk dashboard
    position_count = len(open_positions) if 'open_positions' in locals() else 0
    unrealized_pnl = sum(position.profit for position in open_positions) if position_count else 0.0
    worst_open_loss = min((position.profit for position in open_positions), default=0.0)

    st.header("📉 Risk Dashboard")
    row1, row2, row3 = st.columns(3)
    row1.metric("Drawdown", f"{drawdown:.1%}", delta=f"Limit {max_drawdown_pct:.1f}%")
    row2.metric("Margin Level", f"{margin_info['margin_level']:.1f}%")
    
    # Open P/L with constraint indicator
    pnl_delta = f"{position_count} positions"
    if pnl_constraint_breached:
        pnl_delta += " ⚠️ LIMIT EXCEEDED"
    row3.metric("Open P/L", f"${unrealized_pnl:.2f}", delta=pnl_delta)

    row4, row5, row6 = st.columns(3)
    row4.metric("Free Margin", f"${margin_info['free_margin']:.2f}")
    row5.metric("Worst Open Loss", f"${worst_open_loss:.2f}")
    row6.metric("Auto-close threshold", f"{auto_close_loss_pct:.1f}%")

    # P/L Constraint Security Layer
    st.subheader("🔒 P/L Security Limit (75% of Free Margin)")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Max Allowed P/L", f"${pnl_constraint['max_allowed_pnl']:.2f}")
    with col2:
        st.metric("Current P/L", f"${abs(pnl_constraint['current_pnl']):.2f}")
    with col3:
        utilization_color = "🟢" if pnl_constraint['utilization_percent'] < 75 else "🟡" if pnl_constraint['utilization_percent'] < 100 else "🔴"
        st.metric("Utilization", f"{utilization_color} {pnl_constraint['utilization_percent']:.1f}%")
    with col4:
        if pnl_constraint_breached:
            st.metric("Status", "🔴 EXCEEDED", delta=f"By ${pnl_constraint['exceeded_by']:.2f}")
        else:
            headroom = pnl_constraint['max_allowed_pnl'] - abs(pnl_constraint['current_pnl'])
            st.metric("Headroom", f"${headroom:.2f}")
    
    # Display warning if constraint breached
    if pnl_constraint_breached:
        st.error(f"⚠️ **P/L Limit Breached!** Current P/L (${abs(pnl_constraint['current_pnl']):.2f}) exceeds 75% of Free Margin (${pnl_constraint['max_allowed_pnl']:.2f}). "
                f"Trading is **DISABLED** until P/L returns within limits. "
                f"Exceeded by: ${pnl_constraint['exceeded_by']:.2f}")
    elif pnl_constraint['utilization_percent'] > 60:
        st.warning(f"⚠️ **Approaching P/L Limit!** Currently using {pnl_constraint['utilization_percent']:.1f}% of allowed P/L. "
                  f"Headroom: ${pnl_constraint['max_allowed_pnl'] - abs(pnl_constraint['current_pnl']):.2f}")
    else:
        st.success(f"✅ **P/L Within Limits.** Using {pnl_constraint['utilization_percent']:.1f}% of allowed P/L. "
                  f"Headroom: ${pnl_constraint['max_allowed_pnl'] - abs(pnl_constraint['current_pnl']):.2f}")

    if position_count:
        st.subheader("📌 Open Positions")
        for position in open_positions:
            position_type = 'BUY' if position.type == mt5.ORDER_TYPE_BUY else 'SELL'
            with st.expander(f"Ticket {position.ticket} — {position.symbol} — {position_type}"):
                col_a, col_b = st.columns([3, 1])
                col_a.write(f"**Symbol:** {position.symbol}")
                col_a.write(f"**Type:** {position_type}")
                col_a.write(f"**Volume:** {position.volume}")
                col_a.write(f"**Open Price:** {position.price_open}")
                col_a.write(f"**SL:** {position.sl}")
                col_a.write(f"**TP:** {position.tp}")
                col_a.write(f"**Profit:** ${position.profit:.2f}")
                col_a.write(f"**Loss %:** {((abs(position.profit) / balance) * 100):.2f}%" if position.profit < 0 else "0.00%")

                if col_b.button(f"Close Position", key=f"close_position_{position.ticket}"):
                    try:
                        close_position(position)
                        st.success(f"✅ Closed position {position.ticket} ({position.symbol})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to close position {position.ticket}: {e}")

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        if not df.empty:
            signal_display = f"📈 {symbol} - {timeframe_label} | Signal: **{signal}**"
            if signal_changed:
                signal_display += " 🔔 **SIGNAL CHANGED!**"
            st.subheader(signal_display)

            # Price chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['time'], y=df['close'], name="Price", line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=df['time'], y=df['SMA_50'], name="SMA 50", line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=df['time'], y=df['SMA_200'], name="SMA 200", line=dict(color='red')))
            fig.update_layout(title=f"{symbol} Price Chart", xaxis_title="Time", yaxis_title="Price")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"📊 Unable to display chart - No data available for {symbol}")

    with col2:
        if not df.empty:
            # Trading buttons
            st.subheader("🎯 Quick Trade")
            
            # Show P/L constraint status for trading buttons
            if pnl_constraint_breached:
                st.error("🔴 **Trading BLOCKED** - P/L Limit Exceeded")
                st.info(f"Current P/L (${abs(pnl_constraint['current_pnl']):.2f}) exceeds 75% of Free Margin (${pnl_constraint['max_allowed_pnl']:.2f})")
            elif pnl_constraint['utilization_percent'] > 80:
                st.warning(f"⚠️ **High P/L Usage** - {pnl_constraint['utilization_percent']:.1f}% of limit. Proceed with caution.")
            
            # Estimate loss for new position (stop loss pips * lot size)
            symbol_info = mt5.symbol_info(symbol)
            symbol_tick = mt5.symbol_info_tick(symbol)
            if symbol_info and symbol_tick:
                pip_value = 10 ** (1 - symbol_info.digits)
                estimated_loss = config.STOP_LOSS_PIPS * pip_value * lot
                spread_pips = (symbol_tick.ask - symbol_tick.bid) / symbol_info.point
                if spread_pips > config.MAX_SPREAD_PIPS:
                    st.warning(f"⚠️ High spread for {symbol}: {spread_pips:.1f} pips. Live orders may be expensive or blocked.")
            else:
                estimated_loss = 500 * lot  # Conservative default estimate

            if st.button("🟢 BUY", type="primary", disabled=not trading_enabled):
                st.session_state.manual_action = True
                
                # Check P/L constraint before executing
                order_check = can_place_order(estimated_loss, max_pnl_percent)
                if not order_check['can_place']:
                    st.error(f"❌ Cannot place BUY order: {order_check['reason']}")
                else:
                    trade_success = execute_trade("BUY", symbol, lot, paper_trading)
                    # Only log if trade was actually successful
                    if trade_success:
                        trade_time = time.strftime('%H:%M:%S', time.localtime())
                        log_auto_trade_to_file({
                            'time': trade_time,
                            'symbol': symbol,
                            'signal': 'BUY',
                            'lot': lot,
                            'score': 0  # Manual trades have no score
                        })

            if st.button("🔴 SELL", type="secondary", disabled=not trading_enabled):
                st.session_state.manual_action = True
                
                # Check P/L constraint before executing
                order_check = can_place_order(estimated_loss, max_pnl_percent)
                if not order_check['can_place']:
                    st.error(f"❌ Cannot place SELL order: {order_check['reason']}")
                else:
                    trade_success = execute_trade("SELL", symbol, lot, paper_trading)
                    # Only log if trade was actually successful
                    if trade_success:
                        trade_time = time.strftime('%H:%M:%S', time.localtime())
                        log_auto_trade_to_file({
                            'time': trade_time,
                            'symbol': symbol,
                            'signal': 'SELL',
                            'lot': lot,
                            'score': 0  # Manual trades have no score
                        })

            st.subheader("📡 Watchlist Summary")
            if top_watchlist:
                for item in top_watchlist:
                    status = 'BUY' if item['signal'] == 'BUY' else 'SELL' if item['signal'] == 'SELL' else 'HOLD'
                    st.write(f"**{item['symbol']}** — {status} — score {item['score']}")
            else:
                st.write("No strong watchlist signals right now.")

            # Signal indicator
            st.subheader("📊 Current Signal")
            if signal == "BUY":
                if signal_changed:
                    st.success("🟢 BUY SIGNAL 🔔 **NEW!**")
                else:
                    st.success("🟢 BUY SIGNAL")
            elif signal == "SELL":
                if signal_changed:
                    st.error("🔴 SELL SIGNAL 🔔 **NEW!**")
                else:
                    st.error("🔴 SELL SIGNAL")
            else:
                if signal_changed:
                    st.warning("🟡 HOLD SIGNAL 🔔 **CHANGED!**")
                else:
                    st.warning("🟡 HOLD SIGNAL")
        else:
            st.info("📊 Trading controls unavailable - Please wait for data to load or select a different symbol")

    # Technical indicators charts
    if not df.empty:
        st.header("📊 Technical Analysis")

        tab1, tab2, tab3 = st.tabs(["RSI", "MACD", "Bollinger Bands"])

        with tab1:
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df['time'], y=df['RSI'], name="RSI", line=dict(color='purple')))
            fig_rsi.add_hline(y=70, line_dash="dash", annotation_text="Overbought")
            fig_rsi.add_hline(y=30, line_dash="dash", annotation_text="Oversold")
            fig_rsi.update_layout(title="RSI Indicator", xaxis_title="Time", yaxis_title="RSI")
            st.plotly_chart(fig_rsi, use_container_width=True)

        with tab2:
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=df['time'], y=df['MACD'], name="MACD", line=dict(color='blue')))
            fig_macd.add_trace(go.Scatter(x=df['time'], y=df['MACD_signal'], name="Signal", line=dict(color='red')))
            fig_macd.add_trace(go.Bar(x=df['time'], y=df['MACD_histogram'], name="Histogram"))
            fig_macd.add_trace(go.Scatter(x=df['time'], y=df['MACD'], name="MACD", line=dict(color='blue')))
            fig_macd.add_trace(go.Scatter(x=df['time'], y=df['MACD_signal'], name="Signal", line=dict(color='red')))
            fig_macd.add_trace(go.Bar(x=df['time'], y=df['MACD_histogram'], name="Histogram"))
            fig_macd.update_layout(title="MACD Indicator", xaxis_title="Time", yaxis_title="MACD")
            st.plotly_chart(fig_macd, use_container_width=True)

        with tab3:
            fig_bb = go.Figure()
            fig_bb.add_trace(go.Scatter(x=df['time'], y=df['close'], name="Price", line=dict(color='blue')))
            fig_bb.add_trace(go.Scatter(x=df['time'], y=df['BB_upper'], name="BB Upper", line=dict(color='red', dash='dash')))
            fig_bb.add_trace(go.Scatter(x=df['time'], y=df['BB_middle'], name="BB Middle", line=dict(color='orange', dash='dot')))
            fig_bb.add_trace(go.Scatter(x=df['time'], y=df['BB_lower'], name="BB Lower", line=dict(color='green', dash='dash')))
            fig_bb.update_layout(title="Bollinger Bands", xaxis_title="Time", yaxis_title="Price")
            st.plotly_chart(fig_bb, use_container_width=True)

        # ML Model section
        st.header("🤖 Machine Learning Model")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🧠 Train ML Model"):
                st.session_state.manual_action = True
                with st.spinner("Training ML model..."):
                    result = train_ml_model(df)

                if result is not None:
                    st.success("✅ ML model trained successfully!")
                else:
                    df_ml = df.dropna()
                    if len(df_ml) < 200:
                        st.warning("⚠️ Not enough data for training. Need at least 200 data points after indicator calculation.")
                        st.info(f"Data rows available after dropna: {len(df_ml)}")
                    else:
                        st.error("❌ Training failed. Check the server logs or model code for errors.")

        with col2:
            if st.button("🔍 Check ML Status"):
                st.session_state.manual_action = True
                model, scaler = load_ml_model()
                if model:
                    st.success("✅ ML model is loaded and ready!")
                else:
                    st.warning("⚠️ No trained ML model found.")
    else:
        st.info("📊 Technical analysis charts and ML models will be available once data loads successfully.")

    # Auto Trading History
    if auto_trade and 'auto_trade_history' in st.session_state and st.session_state.auto_trade_history:
        st.header("🤖 Auto Trading History")
        
        # Convert to DataFrame for display
        history_df = pd.DataFrame(st.session_state.auto_trade_history)
        st.dataframe(history_df, use_container_width=True)
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Download CSV"):
                st.session_state.manual_action = True
                csv_data = history_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Auto Trades CSV",
                    data=csv_data,
                    file_name=f"auto_trades_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("🗑️ Clear History"):
                st.session_state.manual_action = True
                st.session_state.auto_trade_history = []
                st.success("History cleared!")
                st.rerun()

    # Daily Auto Trade Logs
    st.header("📁 Daily Auto Trade Logs")

    logs_dir = "auto_trade_logs"
    if os.path.exists(logs_dir):
        log_files = [f for f in os.listdir(logs_dir) if f.startswith("auto_trades_") and f.endswith(".csv")]
        log_files.sort(reverse=True)  # Most recent first
        
        if log_files:
            st.subheader("Available Daily Logs")
            
            for log_file in log_files[:7]:  # Show last 7 days
                date_str = log_file.replace("auto_trades_", "").replace(".csv", "")
                file_path = os.path.join(logs_dir, log_file)
                
                try:
                    # Read and display summary
                    df_log = pd.read_csv(file_path)
                    trade_count = len(df_log)
                    total_lots = df_log['lot_size'].sum() if 'lot_size' in df_log.columns else 0
                    
                    col1, col2, col3 = st.columns([2, 2, 2])
                    with col1:
                        st.write(f"**{date_str}**")
                    with col2:
                        st.write(f"{trade_count} trades")
                    with col3:
                        if st.button(f"📥 Download {date_str}", key=f"download_{date_str}"):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                csv_content = f.read()
                            st.download_button(
                                label=f"Download {date_str} CSV",
                                data=csv_content,
                                file_name=log_file,
                                mime="text/csv",
                                key=f"dl_{date_str}"
                            )
                            
                    # Show preview of today's trades if it's today's file
                    today = datetime.now().strftime("%Y-%m-%d")
                    if date_str == today and len(df_log) > 0:
                        st.write("**Today's Trades:**")
                        st.dataframe(df_log.tail(5), use_container_width=True)
                        
                        # Show daily summary
                        summary = generate_daily_summary(date_str)
                        if summary:
                            st.write("**Daily Summary:**")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Trades", summary['total_trades'])
                            with col2:
                                st.metric("BUY/SELL", f"{summary['buy_trades']}/{summary['sell_trades']}")
                            with col3:
                                st.metric("Total Lots", f"{summary['total_lots']:.2f}")
                            with col4:
                                st.metric("Avg Score", f"{summary['avg_score']:.1f}")
                            
                            st.write(f"**Symbols Traded:** {', '.join(summary['symbols_traded'])}")
                            st.write(f"**Balance Change:** ${summary['end_balance'] - summary['start_balance']:.2f}")
                            st.write(f"**Equity Change:** ${summary['end_equity'] - summary['start_equity']:.2f}")
                        
                except Exception as e:
                    st.error(f"Error reading {log_file}: {e}")
        else:
            st.info("No daily log files found yet.")
    else:
        st.info("Daily log directory will be created when first auto trade executes.")

    # Generate Comprehensive Report
    st.header("📊 Trading Performance Report")

    if st.button("📈 Generate Full Report"):
        st.session_state.manual_action = True
        
        logs_dir = "auto_trade_logs"
        if os.path.exists(logs_dir):
            all_summaries = []
            total_trades = 0
            total_lots = 0.0
            
            for log_file in os.listdir(logs_dir):
                if log_file.startswith("auto_trades_") and log_file.endswith(".csv"):
                    date_str = log_file.replace("auto_trades_", "").replace(".csv", "")
                    summary = generate_daily_summary(date_str)
                    if summary:
                        all_summaries.append(summary)
                        total_trades += summary['total_trades']
                        total_lots += summary['total_lots']
            
            if all_summaries:
                # Sort by date
                all_summaries.sort(key=lambda x: x['date'], reverse=True)
                
                st.subheader("Overall Performance")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Days", len(all_summaries))
                with col2:
                    st.metric("Total Trades", total_trades)
                with col3:
                    st.metric("Total Lots", f"{total_lots:.2f}")
                with col4:
                    avg_daily = total_trades / len(all_summaries) if all_summaries else 0
                    st.metric("Avg Daily Trades", f"{avg_daily:.1f}")
                
                # Show daily summaries table
                st.subheader("Daily Performance")
                summary_df = pd.DataFrame(all_summaries)
                st.dataframe(summary_df, use_container_width=True)
                
                # Export full report
                csv_report = summary_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Full Report CSV",
                    data=csv_report,
                    file_name=f"trading_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No trading data available for report generation.")
        else:
            st.warning("No trading logs found.")

    # Reset manual action flag AFTER all button actions have completed
    # This prevents auto-refresh from interrupting button clicks
    if st.session_state.manual_action:
        time.sleep(0.5)  # Small delay to ensure actions complete
        st.session_state.manual_action = False
        logging.debug("Manual action completed, flag reset")

    # Auto-refresh logic (run only when no manual action occurred)
    # Only trigger rerun if auto_refresh is enabled AND sufficient time has passed
    if auto_refresh and not st.session_state.manual_action:
        current_time = time.time()
        if current_time - st.session_state.last_refresh >= refresh_interval:
            st.session_state.last_refresh = current_time
            logging.debug(f"Auto-refresh triggered (interval: {refresh_interval}s)")
            st.rerun()
    
    # Final state sync before app exits/reruns
    sync_state_to_file()


if __name__ == "__main__":
    main()

