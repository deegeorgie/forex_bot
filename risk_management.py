"""
Risk Management Utilities for Forex Trading Bot
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, time, timedelta
from mt5_connector import get_account_balance, get_account_equity, get_account_margin_info, get_open_positions
import config

logging.basicConfig(level=logging.INFO)

def calculate_max_positions_static(
    balance: float,
    equity: float,
    leverage: float,
    lot_size: float = 1.0,
    contract_size: float = 100000,
    safety_factor: float = 1.2,
    risk_per_trade_pct: float = 0.02,
    max_total_risk_pct: float = 0.10
) -> Dict:
    """
    Calculate maximum number of positions dynamically (static version)
    """

    # 1. Margin per position
    margin_per_position = (lot_size * contract_size) / leverage

    # 2. Free margin
    used_margin = 0  # assume no open trades for baseline
    free_margin = equity - used_margin

    # 3. Margin-based max positions
    max_by_margin = free_margin / (margin_per_position * safety_factor)

    # 4. Risk-based max positions
    risk_per_trade = balance * risk_per_trade_pct
    max_total_risk = balance * max_total_risk_pct

    max_by_risk = max_total_risk / risk_per_trade

    # 5. Final max positions (safe limit)
    max_positions = int(min(max_by_margin, max_by_risk))

    return {
        "margin_per_position": margin_per_position,
        "free_margin": free_margin,
        "max_positions_margin_limit": int(max_by_margin),
        "max_positions_risk_limit": int(max_by_risk),
        "recommended_max_positions": max_positions
    }


def apply_session_filters(max_positions_base: int, current_time: Optional[datetime] = None) -> Dict:
    """
    Apply market session filters to adjust max positions based on trading session

    Args:
        max_positions_base: Base max positions before session filtering
        current_time: Current UTC time (defaults to now)

    Returns:
        Dict with adjusted max positions and session info
    """

    if current_time is None:
        current_time = datetime.utcnow()

    # Convert to UTC time components
    current_hour = current_time.hour
    current_minute = current_time.minute
    current_time_decimal = current_hour + current_minute / 60.0

    # Define session boundaries (UTC)
    # Asian session: ~22:00 - 07:00 (9 hours, low liquidity)
    # London session: ~07:00 - 16:00 (9 hours, high liquidity)
    # New York session: ~13:30 - 22:00 (8.5 hours, high liquidity)

    sessions = {
        'asian': {
            'start': 22.0,  # 22:00 UTC
            'end': 7.0,     # 07:00 UTC
            'multiplier': 0.4,  # 40% of base during Asian session
            'name': 'Asian Session'
        },
        'london': {
            'start': 7.0,   # 07:00 UTC
            'end': 16.0,    # 16:00 UTC
            'multiplier': 0.8,  # 80% of base during London session
            'name': 'London Session'
        },
        'new_york': {
            'start': 13.5,  # 13:30 UTC
            'end': 22.0,    # 22:00 UTC
            'multiplier': 0.9,  # 90% of base during NY session
            'name': 'New York Session'
        }
    }

    # Check if it's weekend (Saturday 22:00 UTC to Sunday 22:00 UTC)
    is_weekend = current_time.weekday() >= 5  # Saturday = 5, Sunday = 6

    if is_weekend:
        session_multiplier = 0.2  # Very conservative on weekends
        current_session = 'weekend'
        session_name = 'Weekend'
    else:
        # Check for London/NY Overlap first (13:30 - 16:00 UTC) - highest liquidity
        if 13.5 <= current_time_decimal < 16.0:
            current_session = 'overlap'
            session_multiplier = 1.0  # Full limits during overlap
            session_name = 'London/NY Overlap'
        else:
            # Determine current session (outside of overlap)
            current_session = 'overlap'  # Default to overlap
            session_multiplier = 1.0     # Full limits during overlap (fallback)
            session_name = 'London/NY Overlap'

            # Check each session
            for session_key, session_info in sessions.items():
                start = session_info['start']
                end = session_info['end']

                if start > end:  # Session crosses midnight
                    if current_time_decimal >= start or current_time_decimal < end:
                        current_session = session_key
                        session_multiplier = session_info['multiplier']
                        session_name = session_info['name']
                        break
                else:  # Normal session
                    if start <= current_time_decimal < end:
                        current_session = session_key
                        session_multiplier = session_info['multiplier']
                        session_name = session_info['name']
                        break

    # Apply session multiplier
    max_positions_session = int(max_positions_base * session_multiplier)
    max_positions_session = max(1, max_positions_session)  # Minimum 1 position

    return {
        'max_positions_session_limit': max_positions_session,
        'session_multiplier': session_multiplier,
        'current_session': current_session,
        'session_name': session_name,
        'current_time_utc': current_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'is_weekend': is_weekend
    }


def get_session_aware_symbols(symbols: List[str], current_time: Optional[datetime] = None) -> List[str]:
    """
    Filter symbols based on current trading session for optimal liquidity/spreads.
    
    Only returns symbols that are actively trading during the current session.
    This reduces position clutter and focuses on liquid pairs.
    
    Args:
        symbols: List of symbols to filter
        current_time: Current UTC time (defaults to now)
    
    Returns:
        List of symbols that are actively trading in current session
    """
    if not config.ENABLE_SESSION_AWARE_TRADING:
        return symbols  # Return all symbols if session-aware trading is disabled
    
    if current_time is None:
        current_time = datetime.utcnow()
    
    # Get current session info
    session_info = apply_session_filters(10, current_time)
    current_session = session_info['current_session']
    is_weekend = session_info['is_weekend']
    
    # Don't filter on weekends - return all available symbols
    if is_weekend:
        logging.info("Weekend trading: All symbols available")
        return symbols
    
    # Filter symbols based on their assigned active sessions
    active_symbols = []
    for symbol in symbols:
        if symbol in config.SYMBOL_SESSION_MAP:
            allowed_sessions = config.SYMBOL_SESSION_MAP[symbol]
            if current_session in allowed_sessions:
                active_symbols.append(symbol)
                logging.debug(f"{symbol} active in {current_session} session")
            else:
                logging.debug(f"{symbol} filtered out (not active in {current_session} session)")
        else:
            # If symbol not in map, include it anyway (for backward compatibility)
            active_symbols.append(symbol)
            logging.debug(f"{symbol} not in session map, including by default")
    
    if not active_symbols:
        # If no symbols match current session, return all to prevent empty watchlist
        logging.warning(f"No symbols active in {current_session} session, returning all symbols")
        return symbols
    
    logging.info(f"Session-aware filtering: {current_session} session → {len(active_symbols)}/{len(symbols)} symbols active")
    return active_symbols


def calculate_symbol_aware_position_limit(
    base_max_positions: int,
    active_symbols: List[str],
    min_positions_per_symbol: int = 1,
    max_positions_per_symbol: int = 3
) -> Dict:
    """
    Calculate position limit adjusted for the number of active symbols in the current session.
    
    This ensures positions are distributed across active symbols rather than concentrated.
    With fewer symbols active, you can hold more positions per symbol.
    With more symbols active, positions are distributed across them.
    
    Args:
        base_max_positions: Base maximum positions (typically from session filter)
        active_symbols: List of symbols currently active in this session
        min_positions_per_symbol: Minimum positions per symbol (default 1)
        max_positions_per_symbol: Maximum positions per symbol (default 3)
    
    Returns:
        Dict with adjusted limits and breakdown
    """
    num_active = len(active_symbols) if active_symbols else 1
    
    # Calculate positions per symbol to maintain balance
    positions_per_symbol = base_max_positions / num_active
    
    # Clamp to reasonable limits
    positions_per_symbol = max(min_positions_per_symbol, 
                               min(max_positions_per_symbol, positions_per_symbol))
    
    # Recalculate total allowed positions across all active symbols
    adjusted_max_positions = int(positions_per_symbol * num_active)
    
    return {
        'base_max_positions': base_max_positions,
        'num_active_symbols': num_active,
        'active_symbols': active_symbols,
        'positions_per_symbol': round(positions_per_symbol, 2),
        'adjusted_max_positions': adjusted_max_positions,
        'concentration_ratio': num_active  # How many symbols to spread across
    }


def get_session_aware_max_positions(
    current_time: Optional[datetime] = None,
    apply_session_filters_flag: bool = True
) -> Dict:
    """
    Get maximum positions limit considering both session filters and active symbols.
    
    This is the recommended function to use for position limit checks when using
    session-aware trading.
    
    Args:
        current_time: Current UTC time (defaults to now)
        apply_session_filters_flag: Whether to apply session-based filters
    
    Returns:
        Dict with comprehensive position limit analysis
    """
    if current_time is None:
        current_time = datetime.utcnow()
    
    # If session-aware trading is disabled, return simple config-based limit
    if not config.ENABLE_SESSION_AWARE_TRADING:
        return {
            'final_max_positions': config.MAX_OPEN_POSITIONS,
            'session_max_positions': config.MAX_OPEN_POSITIONS,
            'session_name': 'Emergency Mode',
            'session_multiplier': 1.0,
            'active_symbols': config.AVAILABLE_SYMBOLS,
            'num_active_symbols': len(config.AVAILABLE_SYMBOLS),
            'positions_per_symbol': config.MAX_OPEN_POSITIONS / len(config.AVAILABLE_SYMBOLS) if config.AVAILABLE_SYMBOLS else config.MAX_OPEN_POSITIONS,
            'is_weekend': False,
            'current_time_utc': current_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'breakdown': f"Emergency Mode: {config.MAX_OPEN_POSITIONS} max positions (session-aware trading disabled)"
        }
    
    # Step 1: Get session-based position limit
    session_info = apply_session_filters(config.MAX_OPEN_POSITIONS, current_time)
    session_limit = session_info['max_positions_session_limit']
    
    # Step 2: Get active symbols for this session
    available_symbols = config.AVAILABLE_SYMBOLS
    active_symbols = get_session_aware_symbols(available_symbols, current_time)
    
    # Step 3: Adjust position limit based on number of active symbols
    symbol_aware_info = calculate_symbol_aware_position_limit(
        base_max_positions=session_limit,
        active_symbols=active_symbols,
        min_positions_per_symbol=1,
        max_positions_per_symbol=3
    )
    
    final_limit = symbol_aware_info['adjusted_max_positions']
    
    return {
        'final_max_positions': final_limit,
        'session_max_positions': session_limit,
        'session_name': session_info['session_name'],
        'session_multiplier': session_info['session_multiplier'],
        'active_symbols': active_symbols,
        'num_active_symbols': len(active_symbols),
        'positions_per_symbol': symbol_aware_info['positions_per_symbol'],
        'is_weekend': session_info['is_weekend'],
        'current_time_utc': session_info['current_time_utc'],
        'breakdown': f"{len(active_symbols)} symbols → {final_limit} max positions ({symbol_aware_info['positions_per_symbol']} per symbol)"
    }


def apply_performance_scaling(
    max_positions_base: int,
    win_rate: float,
    profit_factor: float,
    current_drawdown_pct: float,
    recent_trades_count: int = 20,
    max_scaling_factor: float = 2.0,
    min_scaling_factor: float = 0.3
) -> Dict:
    """
    Apply performance-based scaling to adjust max positions based on trading performance

    Args:
        max_positions_base: Base max positions before performance scaling
        win_rate: Win rate as decimal (0.0 to 1.0)
        profit_factor: Profit factor (gross profit / gross loss)
        current_drawdown_pct: Current drawdown as percentage
        recent_trades_count: Number of recent trades to consider
        max_scaling_factor: Maximum scaling factor (upper limit)
        min_scaling_factor: Minimum scaling factor (lower limit)

    Returns:
        Dict with adjusted max positions and performance metrics
    """

    # Performance score components
    win_rate_score = 0.0
    profit_factor_score = 0.0
    drawdown_penalty = 0.0

    # Win rate scoring
    if win_rate >= 0.7:
        win_rate_score = 1.5  # Excellent
    elif win_rate >= 0.6:
        win_rate_score = 1.2  # Good
    elif win_rate >= 0.5:
        win_rate_score = 1.0  # Neutral
    elif win_rate >= 0.4:
        win_rate_score = 0.7  # Below average
    else:
        win_rate_score = 0.4  # Poor

    # Profit factor scoring
    if profit_factor >= 2.0:
        profit_factor_score = 1.5  # Excellent
    elif profit_factor >= 1.5:
        profit_factor_score = 1.2  # Good
    elif profit_factor >= 1.2:
        profit_factor_score = 1.0  # Neutral
    elif profit_factor >= 1.0:
        profit_factor_score = 0.8  # Slightly profitable
    else:
        profit_factor_score = 0.3  # Losing

    # Drawdown penalty
    if current_drawdown_pct <= 0.02:  # 2% or less
        drawdown_penalty = 1.0
    elif current_drawdown_pct <= 0.05:  # 5%
        drawdown_penalty = 0.9
    elif current_drawdown_pct <= 0.10:  # 10%
        drawdown_penalty = 0.7
    elif current_drawdown_pct <= 0.15:  # 15%
        drawdown_penalty = 0.5
    else:  # Above 15%
        drawdown_penalty = 0.3

    # Recent trades confidence adjustment
    # Fewer trades = less confidence = more conservative scaling
    trades_confidence = min(1.0, recent_trades_count / 50.0)  # Full confidence at 50+ trades

    # Calculate overall performance multiplier
    base_performance_score = (win_rate_score + profit_factor_score) / 2.0
    performance_multiplier = base_performance_score * drawdown_penalty * trades_confidence

    # Clamp to reasonable bounds
    performance_multiplier = max(min_scaling_factor, min(max_scaling_factor, performance_multiplier))

    # Apply scaling
    max_positions_performance = int(max_positions_base * performance_multiplier)
    max_positions_performance = max(1, max_positions_performance)  # Minimum 1 position

    # Performance rating
    if performance_multiplier >= 1.0:
        performance_rating = "Excellent"
    elif performance_multiplier >= 0.8:
        performance_rating = "Good"
    elif performance_multiplier >= 0.6:
        performance_rating = "Neutral"
    elif performance_multiplier >= 0.4:
        performance_rating = "Below Average"
    else:
        performance_rating = "Poor"

    return {
        'max_positions_performance_limit': max_positions_performance,
        'performance_multiplier': performance_multiplier,
        'performance_rating': performance_rating,
        'win_rate_score': win_rate_score,
        'profit_factor_score': profit_factor_score,
        'drawdown_penalty': drawdown_penalty,
        'trades_confidence': trades_confidence,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'current_drawdown_pct': current_drawdown_pct,
        'recent_trades_count': recent_trades_count
    }


def calculate_performance_metrics_from_trades(trade_history: List[Dict], lookback_period_days: int = 30) -> Dict:
    """
    Calculate performance metrics from trade history

    Args:
        trade_history: List of trade dictionaries with keys: 'profit', 'close_time', etc.
        lookback_period_days: Number of days to look back for recent performance

    Returns:
        Dict with win_rate, profit_factor, current_drawdown_pct, recent_trades_count
    """

    if not trade_history:
        return {
            'win_rate': 0.5,
            'profit_factor': 1.0,
            'current_drawdown_pct': 0.0,
            'recent_trades_count': 0
        }

    # Filter recent trades
    cutoff_time = datetime.utcnow() - timedelta(days=lookback_period_days)
    recent_trades = [
        trade for trade in trade_history
        if isinstance(trade.get('close_time'), datetime) and trade['close_time'] > cutoff_time
    ]

    if not recent_trades:
        # If no recent trades, use all available
        recent_trades = trade_history[-50:]  # Last 50 trades

    if not recent_trades:
        return {
            'win_rate': 0.5,
            'profit_factor': 1.0,
            'current_drawdown_pct': 0.0,
            'recent_trades_count': 0
        }

    # Calculate win rate
    winning_trades = [t for t in recent_trades if t.get('profit', 0) > 0]
    win_rate = len(winning_trades) / len(recent_trades)

    # Calculate profit factor
    gross_profit = sum(t.get('profit', 0) for t in winning_trades)
    gross_loss = abs(sum(t.get('profit', 0) for t in recent_trades if t.get('profit', 0) < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0.0

    # Calculate current drawdown
    # This is a simplified calculation - in practice you'd track peak equity
    cumulative_pnl = 0
    peak_pnl = 0
    current_drawdown = 0

    for trade in sorted(recent_trades, key=lambda x: x.get('close_time', datetime.min)):
        cumulative_pnl += trade.get('profit', 0)
        if cumulative_pnl > peak_pnl:
            peak_pnl = cumulative_pnl
        elif peak_pnl > 0:
            drawdown = (peak_pnl - cumulative_pnl) / peak_pnl
            current_drawdown = max(current_drawdown, drawdown)

    return {
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'current_drawdown_pct': current_drawdown,
        'recent_trades_count': len(recent_trades)
    }


def calculate_max_positions_live(
    lot_size: float = 1.0,
    contract_size: float = 100000,
    safety_factor: float = 1.2,
    risk_per_trade_pct: float = 0.02,
    max_total_risk_pct: float = 0.10,
    min_margin_level: float = 200.0,  # Minimum margin level percentage
    dynamic_risk: bool = True,
    apply_session_filters_flag: bool = True,
    apply_performance_scaling_flag: bool = True,
    current_time: Optional[datetime] = None,
    performance_metrics: Optional[Dict] = None,
    trade_history: Optional[List[Dict]] = None,
    auto_calculate_performance: bool = True
) -> Dict:
    """
    Calculate maximum number of positions dynamically using live MT5 data

    Improvements over static version:
    - Uses live account balance, equity, margin info
    - Calculates actual used margin from open positions
    - Considers margin level to prevent margin calls
    - Dynamic risk adjustment based on current account state
    """

    try:
        # Get live account information
        balance = get_account_balance()
        equity = get_account_equity()
        margin_info = get_account_margin_info()

        # Get account leverage (assuming it's available in account info)
        # Note: MT5 account_info() should have leverage
        import MetaTrader5 as mt5
        account = mt5.account_info()
        leverage = account.leverage if account else 100  # fallback

        # Get current open positions to calculate used margin
        positions = get_open_positions()
        used_margin = sum(pos.margin for pos in positions) if positions else 0.0

        # Calculate free margin more accurately
        free_margin = margin_info['free_margin']

        # Current margin level
        margin_level = margin_info['margin_level'] or 0.0

        # 1. Margin per position
        margin_per_position = (lot_size * contract_size) / leverage

        # 2. Margin-based max positions (using actual free margin)
        max_by_margin = free_margin / (margin_per_position * safety_factor)

        # 3. Risk-based max positions
        # Dynamic risk adjustment based on margin level
        if dynamic_risk and margin_level > 0:
            if margin_level < min_margin_level:
                # Reduce risk if margin level is low
                risk_multiplier = margin_level / min_margin_level
                risk_per_trade_pct *= risk_multiplier
                max_total_risk_pct *= risk_multiplier
            elif margin_level > 500:
                # Slightly increase risk if margin level is very high
                risk_multiplier = min(1.2, margin_level / 500)
                risk_per_trade_pct *= risk_multiplier

        risk_per_trade = balance * risk_per_trade_pct
        max_total_risk = balance * max_total_risk_pct
        max_by_risk = max_total_risk / risk_per_trade

        # 4. Margin level constraint
        # Ensure we don't go below minimum margin level
        if margin_level > 0:
            # Estimate margin level after adding one more position
            estimated_used_after = used_margin + margin_per_position
            estimated_margin_level_after = (equity / estimated_used_after) * 100 if estimated_used_after > 0 else float('inf')

            if estimated_margin_level_after < min_margin_level:
                max_by_margin_level = 0  # Can't open any more
            else:
                # Calculate how many we can add while staying above min_margin_level
                # This is approximate: solve for n in: (equity) / (used_margin + n * margin_per_position) >= min_margin_level/100
                max_by_margin_level = (equity / (min_margin_level / 100) - used_margin) / margin_per_position
                max_by_margin_level = max(0, max_by_margin_level - 1)  # subtract 1 for safety
        else:
            max_by_margin_level = float('inf')

        # 5. Apply session filters
        session_info = {}
        if apply_session_filters_flag:
            session_info = apply_session_filters(max_positions, current_time)
            max_positions = session_info['max_positions_session_limit']

        # 6. Apply performance scaling
        performance_info = {}
        if apply_performance_scaling_flag:
            if performance_metrics is None and auto_calculate_performance and trade_history:
                # Auto-calculate performance metrics from trade history
                performance_metrics = calculate_performance_metrics_from_trades(trade_history)

            if performance_metrics:
                performance_info = apply_performance_scaling(
                    max_positions,
                    performance_metrics.get('win_rate', 0.5),
                    performance_metrics.get('profit_factor', 1.0),
                    performance_metrics.get('current_drawdown_pct', 0.0),
                    performance_metrics.get('recent_trades_count', 10)
                )
                max_positions = performance_info['max_positions_performance_limit']

        # Ensure non-negative
        max_positions = max(0, max_positions)

        # Build comprehensive return dictionary
        result = {
            "balance": balance,
            "equity": equity,
            "leverage": leverage,
            "used_margin": used_margin,
            "free_margin": free_margin,
            "margin_level": margin_level,
            "margin_per_position": margin_per_position,
            "max_positions_margin_limit": int(max_by_margin),
            "max_positions_risk_limit": int(max_by_risk),
            "max_positions_margin_level_limit": int(max_by_margin_level),
            "recommended_max_positions": max_positions,
            "dynamic_risk_applied": dynamic_risk,
            "current_open_positions": len(positions) if positions else 0,
            "session_filters_applied": apply_session_filters_flag,
            "performance_scaling_applied": apply_performance_scaling_flag
        }

        # Add session info if applied
        if session_info:
            result.update({
                "session_multiplier": session_info['session_multiplier'],
                "current_session": session_info['current_session'],
                "session_name": session_info['session_name'],
                "current_time_utc": session_info['current_time_utc'],
                "is_weekend": session_info['is_weekend']
            })

        # Add performance info if applied
        if performance_info:
            result.update({
                "performance_multiplier": performance_info['performance_multiplier'],
                "performance_rating": performance_info['performance_rating'],
                "win_rate": performance_info['win_rate'],
                "profit_factor": performance_info['profit_factor'],
                "current_drawdown_pct": performance_info['current_drawdown_pct'],
                "recent_trades_count": performance_info['recent_trades_count']
            })

        return result

    except Exception as e:
        logging.error(f"Failed to calculate max positions with live data: {e}")
        # Fallback to static calculation with better defaults
        # Use config.MAX_OPEN_POSITIONS as base and apply session filters
        try:
            if apply_session_filters_flag:
                session_info = apply_session_filters(config.MAX_OPEN_POSITIONS)
                return {
                    "recommended_max_positions": session_info['max_positions_session_limit'],
                    "session_name": session_info['session_name'],
                    "session_multiplier": session_info['session_multiplier'],
                    "is_weekend": session_info['is_weekend'],
                    "current_time_utc": session_info['current_time_utc'],
                    "fallback_mode": True
                }
        except Exception as fallback_error:
            logging.error(f"Failed to apply session filters in fallback: {fallback_error}")
        
        # Last resort fallback - use static with config values
        return calculate_max_positions_static(
            balance=10000,
            equity=10000,
            leverage=100,
            lot_size=lot_size,
            contract_size=contract_size,
            safety_factor=safety_factor,
            risk_per_trade_pct=risk_per_trade_pct,
            max_total_risk_pct=max_total_risk_pct
        )


def calculate_dynamic_risk_parameters(
    current_drawdown_pct: float,
    margin_level: float,
    volatility_index: float = 1.0,
    base_risk_per_trade_pct: float = 0.02,
    base_max_total_risk_pct: float = 0.10
) -> Dict[float, float]:
    """
    Calculate dynamic risk parameters based on current market conditions

    Args:
        current_drawdown_pct: Current drawdown as percentage
        margin_level: Current margin level percentage
        volatility_index: Market volatility index (1.0 = normal)
        base_risk_per_trade_pct: Base risk per trade percentage
        base_max_total_risk_pct: Base max total risk percentage

    Returns:
        Dict with adjusted risk_per_trade_pct and max_total_risk_pct
    """

    # Adjust for drawdown
    drawdown_multiplier = 1.0
    if current_drawdown_pct > 0.05:  # 5% drawdown
        drawdown_multiplier = max(0.5, 1.0 - (current_drawdown_pct - 0.05) * 2)
    elif current_drawdown_pct < -0.02:  # In profit
        drawdown_multiplier = min(1.2, 1.0 + (-current_drawdown_pct - 0.02) * 1.5)

    # Adjust for margin level
    margin_multiplier = 1.0
    if margin_level < 200:
        margin_multiplier = max(0.3, margin_level / 200)
    elif margin_level > 1000:
        margin_multiplier = min(1.5, margin_level / 1000)

    # Adjust for volatility
    volatility_multiplier = 1.0 / volatility_index  # Reduce risk in high volatility

    # Combine multipliers
    total_multiplier = drawdown_multiplier * margin_multiplier * volatility_multiplier
    total_multiplier = max(0.1, min(2.0, total_multiplier))  # Clamp between 0.1 and 2.0

    adjusted_risk_per_trade_pct = base_risk_per_trade_pct * total_multiplier
    adjusted_max_total_risk_pct = base_max_total_risk_pct * total_multiplier

    return {
        "risk_per_trade_pct": adjusted_risk_per_trade_pct,
        "max_total_risk_pct": adjusted_max_total_risk_pct,
        "drawdown_multiplier": drawdown_multiplier,
        "margin_multiplier": margin_multiplier,
        "volatility_multiplier": volatility_multiplier,
        "total_multiplier": total_multiplier
    }


# Example usage
if __name__ == "__main__":
    # Static version
    result_static = calculate_max_positions_static(
        balance=10000,
        equity=10000,
        leverage=100,
        lot_size=1.0
    )
    print("Static calculation:")
    print(result_static)

    # Example performance metrics
    performance_metrics = {
        'win_rate': 0.65,  # 65% win rate
        'profit_factor': 1.8,  # Good profit factor
        'current_drawdown_pct': 0.03,  # 3% drawdown
        'recent_trades_count': 25
    }

    # Live version (requires MT5 connection)
    try:
        result_live = calculate_max_positions_live(
            lot_size=0.1,
            risk_per_trade_pct=0.02,
            apply_session_filters_flag=True,
            apply_performance_scaling_flag=True,
            performance_metrics=performance_metrics
        )
        print("\nLive calculation with session and performance filters:")
        print(f"Recommended max positions: {result_live['recommended_max_positions']}")
        print(f"Session: {result_live.get('session_name', 'N/A')}")
        print(f"Performance rating: {result_live.get('performance_rating', 'N/A')}")
        print(f"Win rate: {result_live.get('win_rate', 'N/A')}")
        print(f"Profit factor: {result_live.get('profit_factor', 'N/A')}")

    except Exception as e:
        print(f"\nLive calculation failed: {e}")

    # Test individual functions
    print("\n--- Testing Session Filters ---")
    from datetime import datetime
    # Test different times
    test_times = [
        datetime(2024, 1, 1, 2, 0, 0),  # Asian session
        datetime(2024, 1, 1, 10, 0, 0), # London session
        datetime(2024, 1, 1, 15, 0, 0), # London/NY overlap
        datetime(2024, 1, 1, 20, 0, 0), # NY session
    ]

    for test_time in test_times:
        session_result = apply_session_filters(10, test_time)
        print(f"{test_time.strftime('%H:%M UTC')}: {session_result['session_name']} - Max positions: {session_result['max_positions_session_limit']}")

    print("\n--- Testing Performance Scaling ---")
    # Test different performance scenarios
    scenarios = [
        {'win_rate': 0.75, 'profit_factor': 2.5, 'drawdown': 0.01, 'name': 'Excellent'},
        {'win_rate': 0.55, 'profit_factor': 1.2, 'drawdown': 0.05, 'name': 'Average'},
        {'win_rate': 0.35, 'profit_factor': 0.8, 'drawdown': 0.12, 'name': 'Poor'},
    ]

    for scenario in scenarios:
        perf_result = apply_performance_scaling(
            20,  # Use higher base for clearer demonstration
            scenario['win_rate'],
            scenario['profit_factor'],
            scenario['drawdown'],
            30
        )
        print(f"{scenario['name']}: Rating {perf_result['performance_rating']} - Multiplier: {perf_result['performance_multiplier']:.2f} - Max positions: {perf_result['max_positions_performance_limit']}")


def get_current_max_positions(
    lot_size: float = 0.1,
    risk_per_trade_pct: float = 0.02,
    trade_history: Optional[List[Dict]] = None,
    apply_session_filters_flag: bool = True,
    apply_performance_scaling_flag: bool = True
) -> Dict:
    """
    Convenience function to get current max positions with all filters applied.
    This is the main function to call from your trading system.

    Args:
        lot_size: Current lot size per position
        risk_per_trade_pct: Risk per trade percentage
        trade_history: Optional trade history for performance calculation
        apply_session_filters_flag: Whether to apply session-based filters
        apply_performance_scaling_flag: Whether to apply performance-based scaling

    Returns:
        Dict with comprehensive max positions analysis
    """

    return calculate_max_positions_live(
        lot_size=lot_size,
        risk_per_trade_pct=risk_per_trade_pct,
        apply_session_filters_flag=apply_session_filters_flag,
        apply_performance_scaling_flag=apply_performance_scaling_flag,
        trade_history=trade_history,
        auto_calculate_performance=True
    )


def get_max_positions_limit(
    lot_size: float = 0.1,
    risk_per_trade_pct: float = 0.02,
    trade_history: Optional[List[Dict]] = None,
    apply_session_filters_flag: bool = True,
    apply_performance_scaling_flag: bool = True
) -> int:
    """
    Get the current maximum positions limit as a simple integer.
    Use this for quick integration with existing position limit checks.

    Args:
        lot_size: Current lot size per position
        risk_per_trade_pct: Risk per trade percentage
        trade_history: Optional trade history for performance calculation
        apply_session_filters_flag: Whether to apply session-based filters
        apply_performance_scaling_flag: Whether to apply performance-based scaling

    Returns:
        Integer value of the recommended max positions
    """

    try:
        result = get_current_max_positions(
            lot_size=lot_size,
            risk_per_trade_pct=risk_per_trade_pct,
            trade_history=trade_history,
            apply_session_filters_flag=apply_session_filters_flag,
            apply_performance_scaling_flag=apply_performance_scaling_flag
        )
        return result.get('recommended_max_positions', config.MAX_OPEN_POSITIONS)
    except Exception as e:
        logging.error(f"Failed to get max positions limit with full calculation: {e}")
        # Fallback: Apply at least session filters to config value
        try:
            if apply_session_filters_flag:
                session_info = apply_session_filters(config.MAX_OPEN_POSITIONS)
                return session_info['max_positions_session_limit']
            else:
                return config.MAX_OPEN_POSITIONS
        except Exception as fallback_error:
            logging.error(f"Failed to apply session filters fallback: {fallback_error}")
            # Last resort: return config value
            return config.MAX_OPEN_POSITIONS