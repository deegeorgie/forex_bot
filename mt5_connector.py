import MetaTrader5 as mt5

def connect():
    if not mt5.initialize():
        raise Exception("MT5 initialization failed")

def shutdown():
    mt5.shutdown()

def get_price(symbol):
    tick = mt5.symbol_info_tick(symbol)
    return tick.ask, tick.bid

def place_order(symbol, lot, order_type):
    price = get_price(symbol)[0]

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "deviation": 10,
        "magic": 123456,
        "comment": "algo_trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    return mt5.order_send(request)
