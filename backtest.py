import pandas as pd
import numpy as np
from strategy import compute_indicators, generate_signal
import logging

logging.basicConfig(level=logging.INFO)

def backtest_strategy(df, initial_balance=10000, risk_per_trade=0.01, use_ml=False, stop_loss_pips=50, take_profit_pips=100):
    """
    Backtest the strategy on historical data with better risk management.
    Returns a dictionary with performance metrics.
    """
    try:
        df = compute_indicators(df)
        balance = initial_balance
        trades = []
        position = None
        max_balance = initial_balance
        
        # Dynamic position sizing based on risk
        for i in range(len(df)):
            row = df.iloc[i]
            signal = generate_signal(df.iloc[:i+1], use_ml=use_ml)
            
            # Calculate position size based on risk management
            risk_amount = balance * risk_per_trade
            tick_value = 10000  # Assume 1 pip = 10 units of currency
            lot_size = max(0.01, risk_amount / (stop_loss_pips * tick_value))
            lot_size = min(lot_size, 1.0)  # Cap at 1 lot
            
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
                        balance += pnl
                        trades.append({'type': 'BUY', 'entry': position['entry_price'], 'exit': exit_price, 'pnl': pnl})
                        position = None
                    elif row['high'] >= position['entry_price'] + take_profit_pips * 0.0001:
                        exit_price = position['entry_price'] + take_profit_pips * 0.0001
                        pnl = (exit_price - position['entry_price']) * position['lot'] * 100000
                        balance += pnl
                        trades.append({'type': 'BUY', 'entry': position['entry_price'], 'exit': exit_price, 'pnl': pnl})
                        position = None
                    # Close on opposite signal
                    elif signal == "SELL":
                        exit_price = row['close']
                        pnl = (exit_price - position['entry_price']) * position['lot'] * 100000
                        balance += pnl
                        trades.append({'type': 'BUY', 'entry': position['entry_price'], 'exit': exit_price, 'pnl': pnl})
                        position = None
                        
                elif position['type'] == 'SELL':
                    if row['high'] >= position['entry_price'] + stop_loss_pips * 0.0001:
                        exit_price = position['entry_price'] + stop_loss_pips * 0.0001
                        pnl = (position['entry_price'] - exit_price) * position['lot'] * 100000
                        balance += pnl
                        trades.append({'type': 'SELL', 'entry': position['entry_price'], 'exit': exit_price, 'pnl': pnl})
                        position = None
                    elif row['low'] <= position['entry_price'] - take_profit_pips * 0.0001:
                        exit_price = position['entry_price'] - take_profit_pips * 0.0001
                        pnl = (position['entry_price'] - exit_price) * position['lot'] * 100000
                        balance += pnl
                        trades.append({'type': 'SELL', 'entry': position['entry_price'], 'exit': exit_price, 'pnl': pnl})
                        position = None
                    # Close on opposite signal
                    elif signal == "BUY":
                        exit_price = row['close']
                        pnl = (position['entry_price'] - exit_price) * position['lot'] * 100000
                        balance += pnl
                        trades.append({'type': 'SELL', 'entry': position['entry_price'], 'exit': exit_price, 'pnl': pnl})
                        position = None
            
            # Track max balance for drawdown calculation
            if balance > max_balance:
                max_balance = balance
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        total_pnl = sum(t['pnl'] for t in trades)
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
        profit_factor = 0
        if total_trades > 0:
            winning_pnl = sum(t['pnl'] for t in trades if t['pnl'] > 0)
            losing_pnl = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
            profit_factor = winning_pnl / losing_pnl if losing_pnl > 0 else winning_pnl
        
        avg_trade_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        # Generate equity curve
        equity_curve = [initial_balance]
        current_equity = initial_balance
        for trade in trades:
            current_equity += trade['pnl']
            equity_curve.append(current_equity)
        
        # Calculate Sharpe ratio (simplified - annualized returns / volatility of daily returns)
        sharpe_ratio = 0
        if len(trades) > 1:
            returns = [t['pnl'] / initial_balance for t in trades]
            mean_return = np.mean(returns) if returns else 0
            std_return = np.std(returns) if returns else 1
            sharpe_ratio = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate * 100,  # Convert to percentage
            'total_pnl': total_pnl,
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