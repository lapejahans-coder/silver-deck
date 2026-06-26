import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional

# Tickers
NASDAQ_FUTURES = "NQ=F"
S_AND_P_FUTURES = "ES=F"
NASDAQ_ETF = "QQQ"
VIX_INDEX = "^VIX"
DXY_INDEX = "DX-Y.NYB"
TEN_YEAR_YIELD = "^TNX"

def fetch_ticker_data(ticker: str, period: str = "5d", interval: str = "15m") -> pd.DataFrame:
    """Fetches historical data for a given ticker."""
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval)
    return df

def get_market_data() -> Dict[str, Any]:
    """Fetches all necessary market data for the analysis."""
    # Front-month NASDAQ futures
    nq_15m = fetch_ticker_data(NASDAQ_FUTURES, period="5d", interval="15m")
    nq_1h = fetch_ticker_data(NASDAQ_FUTURES, period="1mo", interval="1h")
    nq_1d = fetch_ticker_data(NASDAQ_FUTURES, period="1mo", interval="1d")
    
    # Macro drivers
    es_1d = fetch_ticker_data(S_AND_P_FUTURES, period="5d", interval="1d")
    qqq_1d = fetch_ticker_data(NASDAQ_ETF, period="5d", interval="1d")
    vix_1d = fetch_ticker_data(VIX_INDEX, period="5d", interval="1d")
    dxy_1d = fetch_ticker_data(DXY_INDEX, period="5d", interval="1d")
    tnx_1d = fetch_ticker_data(TEN_YEAR_YIELD, period="5d", interval="1d")
    
    return {
        "nq_15m": nq_15m,
        "nq_1h": nq_1h,
        "nq_1d": nq_1d,
        "es_1d": es_1d,
        "qqq_1d": qqq_1d,
        "vix_1d": vix_1d,
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
