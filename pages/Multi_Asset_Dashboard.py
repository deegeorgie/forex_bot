#!/usr/bin/env python
"""
Multi-Asset Trading Dashboard

Displays unified portfolio metrics across all asset types:
- Forex, Stocks, Indices, Commodities, Crypto
- Asset-specific performance
- Capital allocation breakdown
- Risk metrics by asset class
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import logging

from mt5_connector import connect, get_open_positions, get_account_balance, get_account_equity, get_account_margin_info
from portfolio_manager import PortfolioManager, AssetType
from capital_allocator import CapitalAllocator, AllocationStrategy
from data_layer import DataLayer
from multi_asset_executor import MultiAssetExecutor

logging.basicConfig(level=logging.INFO)

# Page config
st.set_page_config(
    page_title="Multi-Asset Portfolio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar configuration
st.sidebar.header("⚙️ Multi-Asset Configuration")

allocation_strategy = st.sidebar.selectbox(
    "Capital Allocation Strategy",
    [s.value.replace('_', ' ').title() for s in AllocationStrategy],
    help="Choose how to allocate capital across asset types"
)

strategy_map = {s.value.replace('_', ' ').title(): s for s in AllocationStrategy}
selected_strategy = strategy_map[allocation_strategy]

if st.sidebar.button("🔄 Recalculate Allocations", use_container_width=True):
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("📈 Settings")

show_detailed_positions = st.sidebar.checkbox("Show Detailed Positions", value=False)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 300, 60)

# Main content
st.title("🌍 Multi-Asset Portfolio Dashboard")

try:
    # Connect to MT5
    connect()
    
    # Get account info
    balance = get_account_balance()
    equity = get_account_equity()
    margin_info = get_account_margin_info()
    
    # Initialize components
    portfolio = PortfolioManager()
    allocator = CapitalAllocator(selected_strategy)
    executor = MultiAssetExecutor(allocator)
    data_layer = DataLayer()
    
    # Get open positions
    mt5_positions = get_open_positions()
    
    if mt5_positions:
        for pos in mt5_positions:
            portfolio.add_position(pos)
    
    # Calculate metrics
    metrics = portfolio.calculate_metrics(balance, equity)
    allocations = allocator.allocate_capital(balance, max_total_positions=16)
    
    # TOP ROW: Key Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "💰 Balance",
            f"${balance:,.0f}",
            f"${equity - balance:,.0f}",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "📊 Equity",
            f"${equity:,.0f}",
            f"{(equity / balance - 1) * 100:.2f}%",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            "📍 Positions",
            f"{metrics.total_positions}",
            f"L:{metrics.long_positions} S:{metrics.short_positions}"
        )
    
    with col4:
        st.metric(
            "💹 Total Profit",
            f"${metrics.total_profit:,.0f}",
            f"{metrics.total_profit_pct:.2f}%",
            delta_color="off"
        )
    
    with col5:
        st.metric(
            "🎯 Win Rate",
            f"{metrics.win_rate:.1f}%",
            f"Avg: {metrics.average_profit_pct:.2f}%"
        )
    
    st.divider()
    
    # PORTFOLIO BREAKDOWN
    col_portfolio, col_allocation = st.columns(2)
    
    with col_portfolio:
        st.subheader("📈 Portfolio by Asset Type")
        
        # Prepare data for pie chart
        positions_data = []
        profit_data = []
        
        for asset_type in AssetType:
            count = metrics.positions_by_asset.get(asset_type, 0)
            profit = metrics.profit_by_asset.get(asset_type, 0)
            
            if count > 0 or profit != 0:
                positions_data.append({'Asset': asset_type.value.upper(), 'Positions': count})
                profit_data.append({'Asset': asset_type.value.upper(), 'Profit': profit})
        
        if positions_data:
            fig_positions = px.pie(
                positions_data,
                names='Asset',
                values='Positions',
                title='Position Count Distribution',
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            st.plotly_chart(fig_positions, use_container_width=True)
        else:
            st.info("No positions yet")
    
    with col_allocation:
        st.subheader("💳 Capital Allocation")
        
        allocation_data = []
        for asset_type, allocation in allocations.items():
            allocation_data.append({
                'Asset': asset_type.value.upper(),
                'Capital': allocation.allocated_capital,
            })
        
        fig_allocation = px.bar(
            allocation_data,
            x='Asset',
            y='Capital',
            title='Capital Allocation by Asset Type',
            color_discrete_sequence=['#636EFA'],
        )
        fig_allocation.update_layout(showlegend=False)
        st.plotly_chart(fig_allocation, use_container_width=True)
    
    st.divider()
    
    # ASSET-SPECIFIC DETAILS
    st.subheader("🔍 Asset Type Performance Details")
    
    asset_cols = st.columns(len([a for a in AssetType if a != AssetType.OTHER]))
    
    asset_types_list = [a for a in AssetType if a != AssetType.OTHER]
    
    for idx, asset_type in enumerate(asset_types_list):
        with asset_cols[idx]:
            count = metrics.positions_by_asset.get(asset_type, 0)
            profit = metrics.profit_by_asset.get(asset_type, 0)
            profit_pct = metrics.profit_pct_by_asset.get(asset_type, 0)
            allocation = allocations.get(asset_type)
            
            st.write(f"**{asset_type.value.upper()}**")
            st.metric("Positions", count)
            st.metric("Profit", f"${profit:,.0f}", f"{profit_pct:.2f}%")
            
            if allocation:
                st.metric("Allocation", f"${allocation.allocated_capital:,.0f}")
                st.metric("Max Lots", f"{allocation.lot_size:.3f}")
    
    st.divider()
    
    # POSITION DETAILS
    if show_detailed_positions and mt5_positions:
        st.subheader("📋 Open Positions Details")
        
        # Create detailed position table
        position_data = []
        for pos in mt5_positions:
            asset_type = portfolio._detect_asset_type(pos.symbol)
            
            position_data.append({
                'Ticket': pos.ticket,
                'Symbol': pos.symbol,
                'Asset': asset_type.value.upper(),
                'Type': 'BUY' if pos.type == 0 else 'SELL',
                'Volume': pos.volume,
                'Open Price': f"{pos.price_open:.5f}",
                'Profit': f"${pos.profit:.2f}",
                'SL': f"{pos.sl:.5f}",
                'TP': f"{pos.tp:.5f}",
            })
        
        df_positions = pd.DataFrame(position_data)
        st.dataframe(df_positions, use_container_width=True, hide_index=True)
    
    # ALLOCATION DETAILS
    st.subheader("💡 Capital Allocation Details")
    
    allocation_details = []
    for asset_type, allocation in allocations.items():
        allocation_details.append({
            'Asset': asset_type.value.upper(),
            'Capital': f"${allocation.allocated_capital:,.0f}",
            '%': f"{allocation.capital_percentage:.1f}%",
            'Max Pos': allocation.max_positions,
            'Lot Size': f"{allocation.lot_size:.3f}",
            'Leverage': f"{allocation.leverage:.1f}x",
            'Max DD (pips)': allocation.max_drawdown_pips,
        })
    
    df_allocations = pd.DataFrame(allocation_details)
    st.dataframe(df_allocations, use_container_width=True, hide_index=True)
    
    # BEST/WORST POSITIONS
    col_best, col_worst = st.columns(2)
    
    with col_best:
        st.subheader("🏆 Best Position")
        if metrics.max_profit_position:
            best = metrics.max_profit_position
            st.success(f"{best.symbol} - ${best.profit:,.2f}")
            st.caption(f"Type: {'BUY' if best.type == 0 else 'SELL'} | Volume: {best.volume} | Profit %: {best.profit_pct:.2f}%")
        else:
            st.info("No positions yet")
    
    with col_worst:
        st.subheader("📉 Worst Position")
        if metrics.max_loss_position:
            worst = metrics.max_loss_position
            st.error(f"{worst.symbol} - ${worst.profit:,.2f}")
            st.caption(f"Type: {'BUY' if worst.type == 0 else 'SELL'} | Volume: {worst.volume} | Loss %: {worst.profit_pct:.2f}%")
        else:
            st.info("No positions yet")
    
    st.divider()
    
    # RISK METRICS
    st.subheader("⚠️ Risk Metrics")
    
    risk_cols = st.columns(3)
    
    with risk_cols[0]:
        st.metric(
            "Margin Used",
            f"${margin_info.get('margin', 0):,.0f}",
            f"{margin_info.get('margin_percent', 0):.1f}% of equity"
        )
    
    with risk_cols[1]:
        st.metric(
            "Free Margin",
            f"${margin_info.get('free_margin', 0):,.0f}"
        )
    
    with risk_cols[2]:
        drawdown_pct = (balance - equity) / balance * 100 if balance > 0 else 0
        st.metric(
            "Current Drawdown",
            f"{drawdown_pct:.2f}%",
            delta_color="inverse"
        )
    
    # Footer
    st.divider()
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Strategy: {allocation_strategy}")

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    logging.error(f"Dashboard error: {e}", exc_info=True)
finally:
    pass  # Keep connection open for auto-refresh
