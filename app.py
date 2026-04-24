import streamlit as st
import hashlib
import json
from risk_management import apply_session_filters
from datetime import datetime

# Simple credentials (you can also load from a file)
VALID_CREDENTIALS = {
    'admin': hashlib.sha256('admin123'.encode()).hexdigest(),
    'user': hashlib.sha256('user123'.encode()).hexdigest(),
    'deebodiong': hashlib.sha256('jhlfd1974'.encode()).hexdigest()
}

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None

# Configure the page
st.set_page_config(
    page_title="Forex Algo Trading Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Login form
if not st.session_state.authenticated:
    st.title("🏠 Forex Trading Bot - Login")
    st.markdown("---")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if username in VALID_CREDENTIALS and VALID_CREDENTIALS[username] == password_hash:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success(f"Welcome {username}! Refreshing...")
                st.rerun()
            else:
                st.error("Invalid username or password")
else:
    # Logout button in sidebar
    with st.sidebar:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.success("Logged out successfully!")
            st.rerun()
    
    st.title("🏠 Forex Algo Trading Dashboard")
    
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
    
    st.markdown(f"Welcome **{st.session_state.username}**")
    st.markdown("---")

    st.markdown("""
    # Welcome to Your Forex Trading Bot

    This is the main dashboard for your algorithmic forex trading system.

    ## 📊 Available Features

    - **Trading Dashboard**: Real-time trading interface with charts and signals
    - **Backtesting**: Test your strategies on historical data
    - **Dictionary**: Learn trading terms and concepts
    - **Settings**: Configure your trading parameters

    ## 🚀 Getting Started

    Use the sidebar to navigate between different sections of the application.

    **Note**: Make sure MetaTrader 5 is running and properly configured before using the trading features.
    """)

    # Quick status check
    st.subheader("🔗 Connection Status")
    try:
        from mt5_connector import connect
        connect()
        st.success("✅ MetaTrader 5 connection successful")
    except Exception as e:
        st.error(f"❌ MetaTrader 5 connection failed: {e}")
        st.info("💡 Check your MT5 credentials in the Settings page")