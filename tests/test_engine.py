import pandas as pd
import numpy as np
from silver_deck.engine import calculate_rsi, calculate_macd, get_macro_bias

def test_calculate_rsi():
    prices = pd.Series([10, 11, 12, 11, 10, 9, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    rsi = calculate_rsi(prices, period=14)
    assert not rsi.empty
    assert 0 <= rsi.iloc[-1] <= 100

def test_calculate_macd():
    prices = pd.Series(np.random.random(100))
    macd, signal, hist = calculate_macd(prices)
    assert len(macd) == 100
    assert len(signal) == 100
    assert len(hist) == 100

def test_get_macro_bias():
    dxy = pd.DataFrame({'Close': [100, 99]})
    gc = pd.DataFrame({'Close': [2000, 2010]})
    tnx = pd.DataFrame({'Close': [4.0, 3.9]})
    bias, reason = get_macro_bias(dxy, gc, tnx)
    assert bias == "BULLISH"
    assert "DXY down" in reason
    assert "Gold up" in reason
    assert "10Y Yield down" in reason

if __name__ == "__main__":
    test_calculate_rsi()
    test_calculate_macd()
    test_get_macro_bias()
    print("All tests passed!")
