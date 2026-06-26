import pandas as pd
import numpy as np
from silver_deck.engine import calculate_rsi, calculate_macd, get_macro_bias, get_prop_firm_risk_plan

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
    vix = pd.DataFrame({'Close': [20, 18]})
    es = pd.DataFrame({'Close': [6000, 6020]})
    qqq = pd.DataFrame({'Close': [500, 505]})
    tnx = pd.DataFrame({'Close': [4.0, 3.9]})
    bias, reason = get_macro_bias(tnx, vix, es, qqq, dxy)
    assert bias == "BULLISH"
    assert "DXY down" in reason
    assert "VIX down" in reason
    assert "QQQ up" in reason
    assert "10Y Yield down" in reason

def test_get_prop_firm_risk_plan_defaults():
    risk_plan = get_prop_firm_risk_plan(20000, 19950, "LONG")
    assert risk_plan["Account Balance"] == 200000
    assert risk_plan["Max Drawdown"] == 40000
    assert risk_plan["Phase Target"] == 20000
    assert risk_plan["Normal Risk/Trade"] == 2000
    assert risk_plan["Hard Max Risk/Trade"] == 4000
    assert risk_plan["Risk Fits"] is False

if __name__ == "__main__":
    test_calculate_rsi()
    test_calculate_macd()
    test_get_macro_bias()
    test_get_prop_firm_risk_plan_defaults()
    print("All tests passed!")
