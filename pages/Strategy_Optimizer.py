import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

st.title("🚀 Strategy Optimization Guide")

st.markdown("""
This guide provides recommended parameter configurations for different trading styles and timeframes.
Use these presets as a starting point and test them in the Backtesting page.
""")

# Define strategy presets
presets = {
    "🏎️ Aggressive (High Win Rate)": {
        "description": "Fast-moving strategies that capture quick profits",
        "SMA_SHORT": 30,
        "SMA_LONG": 100,
        "RSI_PERIOD": 14,
        "RSI_OVERSOLD": 25,
        "RSI_OVERBOUGHT": 75,
        "BB_PERIOD": 15,
        "BB_STD_DEV": 1.5,
        "MACD_FAST": 10,
        "MACD_SLOW": 20,
        "MACD_SIGNAL": 8,
        "SIGNAL_CONFIRMATION_COUNT": 2,
        "STOP_LOSS_PIPS": 30,
        "TAKE_PROFIT_PIPS": 60
    },
    "⚖️ Balanced (Recommended)": {
        "description": "Best for most traders - balance between success rate and profits",
        "SMA_SHORT": 50,
        "SMA_LONG": 200,
        "RSI_PERIOD": 14,
        "RSI_OVERSOLD": 30,
        "RSI_OVERBOUGHT": 70,
        "BB_PERIOD": 20,
        "BB_STD_DEV": 2.0,
        "MACD_FAST": 12,
        "MACD_SLOW": 26,
        "MACD_SIGNAL": 9,
        "SIGNAL_CONFIRMATION_COUNT": 2,
        "STOP_LOSS_PIPS": 50,
        "TAKE_PROFIT_PIPS": 100
    },
    "🛡️ Conservative (Low Risk)": {
        "description": "Waits for strong signals, fewer trades but higher quality",
        "SMA_SHORT": 70,
        "SMA_LONG": 250,
        "RSI_PERIOD": 21,
        "RSI_OVERSOLD": 35,
        "RSI_OVERBOUGHT": 65,
        "BB_PERIOD": 25,
        "BB_STD_DEV": 2.5,
        "MACD_FAST": 14,
        "MACD_SLOW": 28,
        "MACD_SIGNAL": 10,
        "SIGNAL_CONFIRMATION_COUNT": 3,
        "STOP_LOSS_PIPS": 70,
        "TAKE_PROFIT_PIPS": 150
    },
    "📈 Trending (Catch Trends)": {
        "description": "Optimized for strong directional moves",
        "SMA_SHORT": 20,
        "SMA_LONG": 50,
        "RSI_PERIOD": 12,
        "RSI_OVERSOLD": 20,
        "RSI_OVERBOUGHT": 80,
        "BB_PERIOD": 18,
        "BB_STD_DEV": 1.8,
        "MACD_FAST": 8,
        "MACD_SLOW": 24,
        "MACD_SIGNAL": 7,
        "SIGNAL_CONFIRMATION_COUNT": 2,
        "STOP_LOSS_PIPS": 40,
        "TAKE_PROFIT_PIPS": 120
    },
    "📊 Oscillating (Ranging Markets)": {
        "description": "Best for sideways/ranging markets",
        "SMA_SHORT": 40,
        "SMA_LONG": 120,
        "RSI_PERIOD": 16,
        "RSI_OVERSOLD": 28,
        "RSI_OVERBOUGHT": 72,
        "BB_PERIOD": 22,
        "BB_STD_DEV": 2.2,
        "MACD_FAST": 11,
        "MACD_SLOW": 25,
        "MACD_SIGNAL": 8,
        "SIGNAL_CONFIRMATION_COUNT": 2,
        "STOP_LOSS_PIPS": 45,
        "TAKE_PROFIT_PIPS": 90
    }
}

# Timeframe recommendations
timeframe_presets = {
    "M1 - Scalping (1 Minute)": {
        "recommendation": "Aggressive settings with tight stops",
        "SMA_SHORT": 10,
        "SMA_LONG": 30,
        "STOP_LOSS_PIPS": 5,
        "TAKE_PROFIT_PIPS": 10
    },
    "M5 - Short Term (5 Minute)": {
        "recommendation": "Balanced-Aggressive for rapid movements",
        "SMA_SHORT": 30,
        "SMA_LONG": 100,
        "STOP_LOSS_PIPS": 20,
        "TAKE_PROFIT_PIPS": 50
    },
    "M15 - Intraday (15 Minute)": {
        "recommendation": "Balanced settings",
        "SMA_SHORT": 50,
        "SMA_LONG": 200,
        "STOP_LOSS_PIPS": 40,
        "TAKE_PROFIT_PIPS": 80
    },
    "H1 - Hourly (1 Hour)": {
        "recommendation": "Conservative balanced settings",
        "SMA_SHORT": 50,
        "SMA_LONG": 200,
        "STOP_LOSS_PIPS": 50,
        "TAKE_PROFIT_PIPS": 100
    },
    "D1 - Daily": {
        "recommendation": "Conservative settings, hold positions overnight",
        "SMA_SHORT": 70,
        "SMA_LONG": 250,
        "STOP_LOSS_PIPS": 100,
        "TAKE_PROFIT_PIPS": 200
    }
}

st.header("📋 Strategy Presets")

col1, col2 = st.columns([3, 1])

with col1:
    selected_preset = st.selectbox(
        "Select a Strategy Preset",
        list(presets.keys()),
        help="Choose a preset based on your trading style"
    )

with col2:
    st.write("")  # Spacing

# Display selected preset details
preset_data = presets[selected_preset]
st.info(f"💡 {preset_data['description']}")

# Create comparison table
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📊 Moving Averages")
    st.metric("Short SMA", preset_data['SMA_SHORT'])
    st.metric("Long SMA", preset_data['SMA_LONG'])

with col2:
    st.subheader("📈 RSI Settings")
    st.metric("RSI Period", preset_data['RSI_PERIOD'])
    st.metric("Oversold Level", preset_data['RSI_OVERSOLD'])
    st.metric("Overbought Level", preset_data['RSI_OVERBOUGHT'])

with col3:
    st.subheader("🎯 Risk Management")
    st.metric("Stop Loss (pips)", preset_data['STOP_LOSS_PIPS'])
    st.metric("Take Profit (pips)", preset_data['TAKE_PROFIT_PIPS'])
    st.metric("Signal Confirmations", preset_data['SIGNAL_CONFIRMATION_COUNT'])

st.markdown("---")

st.header("⏱️ Timeframe-Specific Settings")

selected_timeframe = st.selectbox(
    "Select Your Trading Timeframe",
    list(timeframe_presets.keys()),
    help="Different timeframes require different parameters"
)

tf_data = timeframe_presets[selected_timeframe]
st.info(f"✨ {tf_data['recommendation']}")

st.dataframe(
    pd.DataFrame({
        "Parameter": ["Short SMA", "Long SMA", "Stop Loss (pips)", "Take Profit (pips)"],
        "Value": [tf_data['SMA_SHORT'], tf_data['SMA_LONG'], tf_data['STOP_LOSS_PIPS'], tf_data['TAKE_PROFIT_PIPS']]
    }),
    use_container_width=True
)

st.markdown("---")

st.header("📊 Compare All Presets")

# Create comparison dataframe
comparison_data = []
for preset_name, preset_values in presets.items():
    comparison_data.append({
        "Strategy": preset_name,
        "SMA Short": preset_values['SMA_SHORT'],
        "SMA Long": preset_values['SMA_LONG'],
        "RSI Oversold": preset_values['RSI_OVERSOLD'],
        "RSI Overbought": preset_values['RSI_OVERBOUGHT'],
        "Stop Loss": preset_values['STOP_LOSS_PIPS'],
        "Take Profit": preset_values['TAKE_PROFIT_PIPS'],
        "Confirmations": preset_values['SIGNAL_CONFIRMATION_COUNT']
    })

comparison_df = pd.DataFrame(comparison_data)
st.dataframe(comparison_df, use_container_width=True)

st.markdown("---")

st.header("🎯 Apply Preset to Settings")

col1, col2 = st.columns(2)

with col1:
    if st.button("✅ Apply Current Preset", type="primary", use_container_width=True):
        # Create settings dict from selected preset
        new_settings = {
            'RSI_PERIOD': str(preset_data['RSI_PERIOD']),
            'RSI_OVERSOLD': str(preset_data['RSI_OVERSOLD']),
            'RSI_OVERBOUGHT': str(preset_data['RSI_OVERBOUGHT']),
            'BB_PERIOD': str(preset_data['BB_PERIOD']),
            'BB_STD_DEV': str(preset_data['BB_STD_DEV']),
            'MACD_FAST': str(preset_data['MACD_FAST']),
            'MACD_SLOW': str(preset_data['MACD_SLOW']),
            'MACD_SIGNAL': str(preset_data['MACD_SIGNAL']),
            'SMA_SHORT': str(preset_data['SMA_SHORT']),
            'SMA_LONG': str(preset_data['SMA_LONG']),
            'SIGNAL_CONFIRMATION_COUNT': str(preset_data['SIGNAL_CONFIRMATION_COUNT']),
            'STOP_LOSS_PIPS': str(preset_data['STOP_LOSS_PIPS']),
            'TAKE_PROFIT_PIPS': str(preset_data['TAKE_PROFIT_PIPS'])
        }
        
        # Save to .env
        try:
            env_path = ".env"
            existing_settings = {}
            
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.strip().split('=', 1)
                            existing_settings[key] = value
            
            existing_settings.update(new_settings)
            
            with open(env_path, 'w') as f:
                f.write("# Forex Trading Bot Configuration\n")
                f.write("# Auto-generated by Strategy Optimizer\n\n")
                for key, value in existing_settings.items():
                    f.write(f"{key}={value}\n")
            
            st.success(f"✅ Applied '{selected_preset}' preset!")
            st.balloons()
            st.info("🔄 Go to the Backtesting page to test this strategy")
        except Exception as e:
            st.error(f"❌ Error saving preset: {e}")

with col2:
    if st.button("⏱️ Apply Timeframe Settings", use_container_width=True):
        st.info("💡 Tip: Combine this with a strategy preset for best results")

st.markdown("---")

st.header("📚 Optimization Tips")

with st.expander("🎓 Learn More About Each Parameter", expanded=False):
    st.markdown("""
    ### Moving Averages (SMA)
    - **Short SMA**: Faster response to price changes (10-50)
    - **Long SMA**: Smoothed long-term trend (100-250)
    - **Use case**: Crossovers identify trend changes
    - **Tip**: Tighter SMA = more signals, wider SMA = fewer but higher quality signals
    
    ### RSI (Relative Strength Index)
    - **Period**: Usually 14, lower = more sensitive
    - **Oversold**: Values below this suggest buying (20-35)
    - **Overbought**: Values above this suggest selling (65-80)
    - **Use case**: Identify extreme price movements
    
    ### Bollinger Bands
    - **Period**: How many candles to calculate (15-25)
    - **Std Dev**: 2.0 is standard, higher = wider bands
    - **Use case**: Price extremes often bounce off bands
    
    ### MACD
    - **Fast/Slow**: Difference between fast and slow EMAs
    - **Signal**: When histogram crosses signal line
    - **Use case**: Identify momentum and trend changes
    
    ### Signal Confirmations
    - **Count**: 1-4 indicators must align
    - **1-2**: More trades, higher false signal rate
    - **3-4**: Fewer trades, higher quality signals
    """)

with st.expander("📈 Testing Your Optimized Strategy", expanded=False):
    st.markdown("""
    1. **Apply a preset** or adjust parameters in Settings
    2. **Go to Backtesting page**
    3. **Select a date range** (30-90 days recommended)
    4. **Click 'Run Backtest'**
    5. **Analyze results**:
       - Win Rate: Aim for 50%+
       - Profit Factor: Aim for 1.5+
       - Drawdown: Keep below 10%
    6. **Adjust parameters** if needed
    7. **Test different date ranges** to validate consistency
    8. **Paper trade first** before going live
    """)

with st.expander("💡 Common Optimization Strategies", expanded=False):
    st.markdown("""
    ### For Low Win Rate (< 50%)
    - Increase signal confirmations (require more indicators to align)
    - Tighten RSI levels (30→25 oversold, 70→75 overbought)
    - Widen moving average separations
    
    ### For Low Profit Factor (< 1.5)
    - Tighten stops (reduce per-trade losses)
    - Widen take profits (let winners run)
    - Add more confirmation signals
    
    ### For High Drawdown (> 10%)
    - Reduce lot sizes in Settings
    - Tighten stop losses
    - Increase signal confirmations
    
    ### For Too Few Trades
    - Decrease signal confirmations
    - Loosen RSI levels
    - Use shorter moving average periods
    """)

st.markdown("---")
st.success("💡 **Pro Tip**: Document your testing results to track what works for different market conditions!")
