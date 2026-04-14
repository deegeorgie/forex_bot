import pytest
from unittest.mock import patch, MagicMock
from mt5_connector import connect, get_price, calculate_lot_size, place_order, get_account_balance

@patch('mt5_connector.mt5.initialize')
def test_connect_success(mock_initialize):
    mock_initialize.return_value = True
    connect()  # Should not raise

@patch('mt5_connector.mt5.initialize')
def test_connect_failure(mock_initialize):
    mock_initialize.return_value = False
    with pytest.raises(Exception, match="MT5 initialization failed"):
        connect()

@patch('mt5_connector.mt5.symbol_info_tick')
def test_get_price(mock_symbol_info_tick):
    mock_tick = MagicMock()
    mock_tick.ask = 1.1000
    mock_tick.bid = 1.0995
    mock_symbol_info_tick.return_value = mock_tick
    
    ask, bid = get_price("EURUSD")
    assert ask == 1.1000
    assert bid == 1.0995

@patch('mt5_connector.mt5.symbol_info_tick')
def test_get_price_failure(mock_symbol_info_tick):
    mock_symbol_info_tick.return_value = None
    with pytest.raises(Exception, match="Failed to get tick"):
        get_price("EURUSD")

@patch('mt5_connector.mt5.account_info')
def test_get_account_balance(mock_account_info):
    mock_account = MagicMock()
    mock_account.balance = 10000.0
    mock_account_info.return_value = mock_account
    
    balance = get_account_balance()
    assert balance == 10000.0

@patch('mt5_connector.mt5.symbol_info')
@patch('mt5_connector.mt5.account_info')
def test_calculate_lot_size(mock_account_info, mock_symbol_info):
    mock_account = MagicMock()
    mock_account.balance = 10000.0
    mock_account_info.return_value = mock_account
    
    mock_symbol = MagicMock()
    mock_symbol.point = 0.00001
    mock_symbol_info.return_value = mock_symbol
    
    lot = calculate_lot_size(10000.0, 0.02, 50, "EURUSD")
    expected = (10000 * 0.02) / (50 * 0.00001 * 10)
    assert lot == round(expected, 2)

@patch('mt5_connector.mt5.symbol_info')
@patch('mt5_connector.mt5.symbol_info_tick')
@patch('mt5_connector.mt5.order_send')
def test_place_order(mock_order_send, mock_symbol_info_tick, mock_symbol_info):
    mock_tick = MagicMock()
    mock_tick.ask = 1.1000
    mock_symbol_info_tick.return_value = mock_tick
    
    mock_symbol = MagicMock()
    mock_symbol.point = 0.00001
    mock_symbol_info.return_value = mock_symbol
    
    mock_result = MagicMock()
    mock_result.retcode = 10009  # TRADE_RETCODE_DONE
    mock_order_send.return_value = mock_result
    
    result = place_order("EURUSD", 0.1, 0, 50, 100)  # ORDER_TYPE_BUY = 0
    assert result == mock_result