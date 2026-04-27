import MetaTrader5 as mt5
import logging
from typing import Tuple, Optional
import config

logging.basicConfig(level=logging.INFO)

def connect() -> None:
    """Connect to MetaTrader 5."""
    try:
        # Initialize MT5
        if not mt5.initialize():
            raise Exception("MT5 initialization failed")

        # Login to trading account if credentials are provided
        if config.MT5_LOGIN and config.MT5_PASSWORD and config.MT5_SERVER:
            if not mt5.login(config.MT5_LOGIN, config.MT5_PASSWORD, config.MT5_SERVER):
                raise Exception(f"MT5 login failed. Login: {config.MT5_LOGIN}, Server: {config.MT5_SERVER}")

        logging.info("MT5 connected successfully")
    except Exception as e:
        logging.error(f"Failed to connect to MT5: {e}")
        raise

def shutdown() -> None:
    """Shutdown MetaTrader 5 connection."""
    try:
        mt5.shutdown()
        logging.info("MT5 shutdown successfully")
    except Exception as e:
        logging.error(f"Failed to shutdown MT5: {e}")

def get_price(symbol: str) -> Tuple[float, float]:
    """Get ask and bid price for a symbol."""
    try:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise Exception(f"Failed to get tick for {symbol}")
        return tick.ask, tick.bid
    except Exception as e:
        logging.error(f"Failed to get price for {symbol}: {e}")
        raise

def get_account_balance() -> float:
    """Get account balance."""
    try:
        account = mt5.account_info()
        if account is None:
            raise Exception("Failed to get account info")
        return account.balance
    except Exception as e:
        logging.error(f"Failed to get account balance: {e}")
        raise


def get_available_symbols() -> list:
    """Return a sorted list of forex-related MT5 symbols available in the terminal."""
    try:
        symbols = mt5.symbols_get()
        if symbols is None:
            return []

        forex_currencies = {"AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "USD"}

        def is_forex_symbol(symbol_obj):
            name = getattr(symbol_obj, 'name', '')
            path = getattr(symbol_obj, 'path', '') or getattr(symbol_obj, 'group', '') or ''
            if not isinstance(name, str):
                return False

            if isinstance(path, str) and 'forex' in path.lower():
                return True

            if len(name) == 6:
                base = name[:3]
                quote = name[3:]
                return base in forex_currencies and quote in forex_currencies

            return False

        filtered = sorted({
            symbol.name
            for symbol in symbols
            if is_forex_symbol(symbol)
        })
        return filtered
    except Exception as e:
        logging.error(f"Failed to get available symbols: {e}")
        return []


def is_algorithmic_trading_enabled() -> bool:
    """Check if algorithmic trading is enabled in MT5 terminal."""
    try:
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            return False
        return terminal_info.trade_allowed
    except Exception as e:
        logging.error(f"Failed to check algorithmic trading status: {e}")
        return False

def get_account_equity() -> float:
    """Get account equity."""
    try:
        account = mt5.account_info()
        if account is None:
            raise Exception("Failed to get account info")
        return account.equity
    except Exception as e:
        logging.error(f"Failed to get account equity: {e}")
        raise

def calculate_lot_size(balance: float, risk_percentage: float, stop_loss_pips: int, symbol: str) -> float:
    """Calculate lot size based on risk management."""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise Exception(f"Symbol info not available for {symbol}")
        pip_value = 10 ** (1 - symbol_info.digits)  # Correct pip value based on symbol digits
        risk_amount = balance * risk_percentage
        lot_size = risk_amount / (stop_loss_pips * pip_value)
        return round(lot_size, 2)
    except Exception as e:
        logging.error(f"Failed to calculate lot size: {e}")
        raise

def place_order(symbol: str, lot: float, order_type: int, stop_loss_pips: Optional[int] = None, take_profit_pips: Optional[int] = None) -> Optional[object]:
    """Place a trade order."""
    try:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise Exception(f"Failed to get tick for {symbol}")

        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise Exception(f"Symbol info not available for {symbol}")

        pip_value = 10 ** (1 - symbol_info.digits)  # Correct pip value based on symbol digits
        price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid

        spread = tick.ask - tick.bid
        if spread > config.MAX_SPREAD_PIPS * pip_value:
            raise Exception(f"Spread too high for {symbol}: {spread:.8f}")

        sl = None
        tp = None
        min_stop_distance = symbol_info.trade_stops_level * symbol_info.point  # Minimum stop distance in price units
        if stop_loss_pips:
            sl_distance = stop_loss_pips * pip_value
            if sl_distance < min_stop_distance:
                raise Exception(f"Stop loss distance ({sl_distance}) is below minimum allowed ({min_stop_distance})")
            if order_type == mt5.ORDER_TYPE_BUY:
                sl = price - sl_distance
            else:
                sl = price + sl_distance
        if take_profit_pips:
            tp_distance = take_profit_pips * pip_value
            if tp_distance < min_stop_distance:
                raise Exception(f"Take profit distance ({tp_distance}) is below minimum allowed ({min_stop_distance})")
            if order_type == mt5.ORDER_TYPE_BUY:
                tp = price + tp_distance
            else:
                tp = price - tp_distance

        # Create base request without filling mode (most brokers prefer this for market orders)
        deviation = max(1, int(config.MAX_SLIPPAGE_PIPS / symbol_info.point))
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": deviation,
            "magic": 123456,
            "comment": "algo_trade",
            "type_time": mt5.ORDER_TIME_GTC,
        }

        # Try basic order first
        result = mt5.order_send(request)
        
        # If basic order fails, try with different filling modes
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            filling_modes_to_try = [
                mt5.ORDER_FILLING_RETURN,  # Most brokers support this
                mt5.ORDER_FILLING_IOC,     # Immediate or Cancel
                mt5.ORDER_FILLING_FOK      # Fill or Kill
            ]
            
            for filling_mode in filling_modes_to_try:
                request_with_filling = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": lot,
                    "type": order_type,
                    "price": price,
                    "sl": sl,
                    "tp": tp,
                    "deviation": deviation,
                    "magic": 123456,
                    "comment": "algo_trade",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": filling_mode,
                }
                
                result = mt5.order_send(request_with_filling)
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logging.info(f"Order successful with filling mode: {filling_mode}")
                    break
                else:
                    logging.warning(f"Filling mode {filling_mode} failed for {symbol}: {result.comment}")

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise Exception(f"Order failed: {result.comment}")
        logging.info(f"Order placed: {order_type} {lot} lots of {symbol}")
        return result
    except Exception as e:
        logging.error(f"Failed to place order: {e}")
        raise


def get_open_positions(symbol: Optional[str] = None):
    """Return a list of open MT5 positions for the specified symbol or all symbols."""
    try:
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        if positions is None:
            return []
        return list(positions)
    except Exception as e:
        logging.error(f"Failed to get open positions: {e}")
        raise


def get_account_margin_info() -> dict:
    """Return margin information for the connected account."""
    try:
        account = mt5.account_info()
        if account is None:
            raise Exception("Failed to get account info")
        return {
            'margin': account.margin,
            'free_margin': account.margin_free,
            'margin_level': account.margin_level,
        }
    except Exception as e:
        logging.error(f"Failed to get account margin info: {e}")
        raise


def check_pnl_constraint(max_pnl_percent: float = 0.75) -> dict:
    """
    Check if current Open P/L exceeds the maximum allowed percentage of Free Margin.
    
    Args:
        max_pnl_percent: Maximum allowed P/L as a percentage of Free Margin (default 0.75 = 75%)
    
    Returns:
        dict with:
            - 'within_limits': bool - whether current P/L is within limits
            - 'current_pnl': float - current unrealized P/L
            - 'free_margin': float - current free margin
            - 'max_allowed_pnl': float - maximum allowed P/L
            - 'utilization_percent': float - percentage of limit being used
    """
    try:
        positions = get_open_positions()
        margin_info = get_account_margin_info()
        
        current_pnl = sum(position.profit for position in positions) if positions else 0.0
        free_margin = margin_info['free_margin']
        max_allowed_pnl = free_margin * max_pnl_percent
        
        # Check if we're exceeding limits (considering negative P/L)
        # We need to check both the absolute value and the actual loss
        within_limits = abs(current_pnl) <= max_allowed_pnl
        
        utilization_percent = (abs(current_pnl) / max_allowed_pnl * 100) if max_allowed_pnl > 0 else 0
        
        return {
            'within_limits': within_limits,
            'current_pnl': current_pnl,
            'free_margin': free_margin,
            'max_allowed_pnl': max_allowed_pnl,
            'utilization_percent': utilization_percent,
            'exceeded_by': max(0, abs(current_pnl) - max_allowed_pnl)
        }
    except Exception as e:
        logging.error(f"Failed to check P/L constraint: {e}")
        raise


def can_place_order(estimated_loss: float, max_pnl_percent: float = 0.75) -> dict:
    """
    Check if a new order can be placed without violating P/L constraints.
    
    Args:
        estimated_loss: Estimated maximum loss for the new position
        max_pnl_percent: Maximum allowed P/L as a percentage of Free Margin (default 0.75 = 75%)
    
    Returns:
        dict with:
            - 'can_place': bool - whether order can be placed
            - 'current_utilization': float - current P/L utilization percentage
            - 'projected_utilization': float - projected P/L utilization if order placed
            - 'reason': str - reason if order cannot be placed
    """
    try:
        from risk_management import get_max_positions_limit
        
        positions = get_open_positions()
        max_positions = get_max_positions_limit()
        if len(positions) >= max_positions:
            return {
                'can_place': False,
                'current_utilization': 100,
                'projected_utilization': 100,
                'reason': f'Max open positions reached ({len(positions)} >= {max_positions})'
            }

        constraint = check_pnl_constraint(max_pnl_percent)
        
        if constraint['free_margin'] <= 0:
            return {
                'can_place': False,
                'current_utilization': constraint['utilization_percent'],
                'projected_utilization': 100,
                'reason': 'Free margin is zero or negative. Account may be in margin call.'
            }
        
        current_pnl = constraint['current_pnl']
        max_allowed_pnl = constraint['max_allowed_pnl']
        projected_pnl = abs(current_pnl) + estimated_loss
        projected_utilization = (projected_pnl / max_allowed_pnl * 100) if max_allowed_pnl > 0 else 100
        
        can_place = projected_pnl <= max_allowed_pnl
        
        reason = ""
        if not can_place:
            reason = f"Placing this order would exceed P/L limit. Current P/L: ${current_pnl:.2f}, " \
                     f"Estimated new loss: ${estimated_loss:.2f}, " \
                     f"Max allowed: ${max_allowed_pnl:.2f}"
        
        return {
            'can_place': can_place,
            'current_utilization': constraint['utilization_percent'],
            'projected_utilization': projected_utilization,
            'reason': reason
        }
    except Exception as e:
        logging.error(f"Failed to check if order can be placed: {e}")
        return {
            'can_place': False,
            'current_utilization': 0,
            'projected_utilization': 0,
            'reason': f"Error checking order constraints: {e}"
        }


def close_position(position, deviation: int = 20):
    """Close an open position using the current market price."""
    try:
        # Check MT5 connection
        if not mt5.initialize():
            raise Exception("MT5 not initialized")
        
        symbol = position.symbol
        volume = position.volume
        ticket = position.ticket
        
        # Determine opposite order type to close the position
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        
        # Get current market price
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise Exception(f"Failed to get tick for {symbol}. Symbol might not exist or be tradeable.")
        
        # Select correct price: bid for sell, ask for buy
        price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
        
        # Ensure symbol is selected for trading
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise Exception(f"Symbol {symbol} not found in broker's symbol list")
        
        if not symbol_info.visible:
            logging.warning(f"Symbol {symbol} not visible, attempting to select...")
            if not mt5.symbol_select(symbol, True):
                logging.warning(f"Could not select {symbol}, continuing anyway...")
        
        # Create close request
        # NOTE: For closing orders, we DON'T use type_time or type_filling
        # The broker decides the filling mode based on their settings
        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': volume,
            'type': order_type,
            'position': ticket,
            'price': price,
            'deviation': deviation,
            'comment': 'position_close',
        }
        
        logging.info(f"Sending close request: ticket={ticket}, symbol={symbol}, type={'SELL' if order_type == mt5.ORDER_TYPE_SELL else 'BUY'}, volume={volume}, price={price}")
        
        # Send the close order
        result = mt5.order_send(request)
        
        if result is None:
            raise Exception("order_send returned None - MT5 connection might be lost")
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logging.info(f"✅ Position closed successfully: ticket {ticket}, symbol {symbol}, volume {volume}")
            return result
        
        # If failed, log detailed error and try market order with highest deviation
        logging.warning(f"Close attempt failed with retcode {result.retcode}: {result.comment}")
        
        # Try again with higher deviation (more aggressive fill)
        if result.retcode in [mt5.TRADE_RETCODE_PRICE_OFF, mt5.TRADE_RETCODE_REQUOTE]:
            logging.info(f"Retrying with higher deviation (50)...")
            request['deviation'] = 50
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logging.info(f"✅ Position closed on retry: ticket {ticket}")
                return result
            else:
                raise Exception(f"Close failed even with high deviation: {result.comment} (retcode: {result.retcode})")
        else:
            raise Exception(f"Close failed: {result.comment} (retcode: {result.retcode})")
    
    except Exception as e:
        logging.error(f"❌ Failed to close position {position.ticket}: {e}")
        raise
