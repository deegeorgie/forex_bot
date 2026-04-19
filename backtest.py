import pandas as pd
import numpy as np
import logging
import psutil
import os
from strategy import compute_indicators, generate_signal, generate_signals
import config

logging.basicConfig(level=logging.INFO)

def check_memory_usage():
    """Check current memory usage and warn if high."""
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    if memory_mb > 500:  # Warn if over 500MB
        logging.warning(f"High memory usage: {memory_mb:.1f} MB")
    return memory_mb

def backtest_strategy(df, initial_balance=10000, risk_per_trade=0.01, use_ml=False, stop_loss_pips=50, take_profit_pips=100):
    """
    Backtest the strategy on historical data with better risk management.
    Returns a dictionary with performance metrics.
    """
    try:
        # Check memory before starting
        initial_memory = check_memory_usage()
        
        df = compute_indicators(df)
        
        # Check memory after computing indicators
        after_indicators_memory = check_memory_usage()
        if after_indicators_memory - initial_memory > 100:
            logging.warning("Significant memory increase after computing indicators")
        
        balance = initial_balance
        trades = []
        position = None
        max_balance = initial_balance

        signal_series = generate_signals(df, use_ml=use_ml)
        spread_pips = config.BACKTEST_SPREAD_PIPS
        slippage_pips = config.BACKTEST_SLIPPAGE_PIPS
        pip_value = 10  # Approximate pip value for major forex pairs

        # Dynamic position sizing based on risk
        for i in range(len(df)):
            row = df.iloc[i]
            signal = signal_series.iloc[i] if i < len(signal_series) else "HOLD"
            
            # Calculate position size based on risk management
            risk_amount = balance * risk_per_trade
            lot_size = max(0.01, risk_amount / (stop_loss_pips * pip_value))
            lot_size = min(lot_size, 1.0)  # Cap at 1 lot
            trade_cost = (spread_pips + slippage_pips) * pip_value * lot_size
            
            if position is None and signal in ["BUY", "SELL"]:
                position = {
                    'type': signal, 
                    'entry_price': row['close'], 
                    'lot': lot_size,
                    'entry_index': i
                }
            elif position is not None:
                # Check stop loss and take profit with tighter controls
                if position['type'] == 'BUY':
                    if row['low'] <= position['entry_price'] - stop_loss_pips * 0.0001:
                        exit_price = position['entry_price'] - stop_loss_pips * 0.0001
                        pnl = (exit_price - position['entry_price']) * position['lot'] * 100000
                        balance += pnl - trade_cost
                        trades.append({'type': 'BUY', 'entry': position['entry_price'], 'exit': exit_price, 'pnl': pnl, 'cost': trade_cost})
                        position = None
                    elif row['high'] >= position['entry_price'] + take_profit_pips * 0.0001:
                        exit_price = position['entry_price'] + take_profit_pips * 0.0001
                        pnl = (exit_price - position['entry_price']) * position['lot'] * 100000
                        balance += pnl - trade_cost
                        trades.append({'type': 'BUY', 'entry': position['entry_price'], 'exit': exit_price, 'pnl': pnl, 'cost': trade_cost})
                        position = None
                    # Close on opposite signal
                    elif signal == "SELL":
                        exit_price = row['close']
                        pnl = (exit_price - position['entry_price']) * position['lot'] * 100000
                        balance += pnl - trade_cost
                        trades.append({'type': 'BUY', 'entry': position['entry_price'], 'exit': exit_price, 'pnl': pnl, 'cost': trade_cost})
                        position = None
                        
                elif position['type'] == 'SELL':
                    if row['high'] >= position['entry_price'] + stop_loss_pips * 0.0001:
                        exit_price = position['entry_price'] + stop_loss_pips * 0.0001
                        pnl = (position['entry_price'] - exit_price) * position['lot'] * 100000
                        balance += pnl - trade_cost
                        trades.append({'type': 'SELL', 'entry': position['entry_price'], 'exit': exit_price, 'pnl': pnl, 'cost': trade_cost})
                        position = None
                    elif row['low'] <= position['entry_price'] - take_profit_pips * 0.0001:
                        exit_price = position['entry_price'] - take_profit_pips * 0.0001
                        pnl = (position['entry_price'] - exit_price) * position['lot'] * 100000
                        balance += pnl - trade_cost
                        trades.append({'type': 'SELL', 'entry': position['entry_price'], 'exit': exit_price, 'pnl': pnl, 'cost': trade_cost})
                        position = None
                    # Close on opposite signal
                    elif signal == "BUY":
                        exit_price = row['close']
                        pnl = (position['entry_price'] - exit_price) * position['lot'] * 100000
                        balance += pnl - trade_cost
                        trades.append({'type': 'SELL', 'entry': position['entry_price'], 'exit': exit_price, 'pnl': pnl, 'cost': trade_cost})
                        position = None
            
            # Track max balance for drawdown calculation
            if balance > max_balance:
                max_balance = balance
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        total_pnl = sum(t['pnl'] - t.get('cost', 0) for t in trades)
        max_drawdown = 0
        peak = initial_balance
        current = initial_balance
        for trade in trades:
            current += trade['pnl']
            if current > peak:
                peak = current
            drawdown = (peak - current) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        logging.info(f"Backtest completed: {total_trades} trades, Win rate: {win_rate:.2%}, Total P&L: ${total_pnl:.2f}, Max DD: {max_drawdown:.2%}")
        
        # Calculate additional metrics
        total_cost = sum(t.get('cost', 0) for t in trades)
        profit_factor = 0
        if total_trades > 0:
            winning_pnl = sum((t['pnl'] - t.get('cost', 0)) for t in trades if t['pnl'] > 0)
            losing_pnl = abs(sum((t['pnl'] - t.get('cost', 0)) for t in trades if t['pnl'] < 0))
            profit_factor = winning_pnl / losing_pnl if losing_pnl > 0 else winning_pnl
        
        avg_trade_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        # Generate equity curve
        equity_curve = [initial_balance]
        current_equity = initial_balance
        for trade in trades:
            net_trade = trade['pnl'] - trade.get('cost', 0)
            current_equity += net_trade
            equity_curve.append(current_equity)
        
        # Calculate Sharpe ratio (simplified - annualized returns / volatility of daily returns)
        sharpe_ratio = 0
        if len(trades) > 1:
            returns = [(t['pnl'] - t.get('cost', 0)) / initial_balance for t in trades]
            mean_return = np.mean(returns) if returns else 0
            std_return = np.std(returns) if returns else 1
            sharpe_ratio = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate * 100,  # Convert to percentage
            'total_pnl': total_pnl,
            'total_cost': total_cost,
            'final_balance': balance,
            'initial_balance': initial_balance,
            'max_drawdown': max_drawdown * 100,  # Convert to percentage
            'profit_factor': profit_factor,
            'avg_trade_pnl': avg_trade_pnl,
            'sharpe_ratio': sharpe_ratio,
            'equity_curve': equity_curve,
            'trades': trades
        }
    except Exception as e:
        logging.error(f"Backtest failed: {e}")
        raise