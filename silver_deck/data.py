import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional

# Tickers
SILVER_FUTURES = "SI=F"
GOLD_FUTURES = "GC=F"
DXY_INDEX = "DX-Y.NYB"
TEN_YEAR_YIELD = "^TNX"

def fetch_ticker_data(ticker: str, period: str = "5d", interval: str = "15m") -> pd.DataFrame:
    """Fetches historical data for a given ticker."""
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval)
    return df

def get_market_data() -> Dict[str, Any]:
    """Fetches all necessary market data for the analysis."""
    # Front-month Silver
    si_15m = fetch_ticker_data(SILVER_FUTURES, period="5d", interval="15m")
    si_1h = fetch_ticker_data(SILVER_FUTURES, period="1mo", interval="1h")
    si_1d = fetch_ticker_data(SILVER_FUTURES, period="1mo", interval="1d")
    
    # Macro drivers
    gc_1d = fetch_ticker_data(GOLD_FUTURES, period="5d", interval="1d")
    dxy_1d = fetch_ticker_data(DXY_INDEX, period="5d", interval="1d")
    tnx_1d = fetch_ticker_data(TEN_YEAR_YIELD, period="5d", interval="1d")
    
    return {
        "si_15m": si_15m,
        "si_1h": si_1h,
        "si_1d": si_1d,
        "gc_1d": gc_1d,
        "dxy_1d": dxy_1d,
        "tnx_1d": tnx_1d
    }

def get_latest_price(df: pd.DataFrame) -> Optional[float]:
    if df.empty:
        return None
    return float(df['Close'].iloc[-1])

def get_ohlc_summary(df: pd.DataFrame) -> Dict[str, float]:
    """Returns High, Low, Close of the latest complete session."""
    if df.empty:
        return {}
    latest = df.iloc[-1]
    return {
        "high": float(latest['High']),
        "low": float(latest['Low']),
        "close": float(latest['Close'])
    }
