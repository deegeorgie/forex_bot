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
        pip_value = symbol_info.point * 10  # Assuming 5-digit broker
        risk_amount = balance * risk_percentage
        lot_size = risk_amount / (stop_loss_pips * pip_value)
        return round(lot_size, 2)
    except Exception as e:
        logging.error(f"Failed to calculate lot size: {e}")
        raise

def place_order(symbol: str, lot: float, order_type: int, stop_loss_pips: Optional[int] = None, take_profit_pips: Optional[int] = None) -> Optional[object]:
    """Place a trade order."""
    try:
        price = get_price(symbol)[0]
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise Exception(f"Symbol info not available for {symbol}")

        sl = None
        tp = None
        if stop_loss_pips:
            if order_type == mt5.ORDER_TYPE_BUY:
                sl = price - stop_loss_pips * symbol_info.point * 10
            else:
                sl = price + stop_loss_pips * symbol_info.point * 10
        if take_profit_pips:
            if order_type == mt5.ORDER_TYPE_BUY:
                tp = price + take_profit_pips * symbol_info.point * 10
            else:
                tp = price - take_profit_pips * symbol_info.point * 10

        # Try different filling modes in order of preference
        filling_modes = [
            mt5.ORDER_FILLING_IOC,      # Immediate or Cancel
            mt5.ORDER_FILLING_FOK,      # Fill or Kill
            mt5.ORDER_FILLING_RETURN    # Return unfilled portion
        ]

        result = None
        for filling_mode in filling_modes:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 10,
                "magic": 123456,
                "comment": "algo_trade",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode,
            }

            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                break  # Success, exit the loop
            elif "Unsupported filling mode" in str(result.comment):
                continue  # Try next filling mode
            else:
                # Different error, don't retry
                break

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise Exception(f"Order failed: {result.comment}")
        logging.info(f"Order placed: {order_type} {lot} lots of {symbol}")
        return result
    except Exception as e:
        logging.error(f"Failed to place order: {e}")
        raise
