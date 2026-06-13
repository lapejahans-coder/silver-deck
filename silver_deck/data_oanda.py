import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import pandas as pd
import yfinance as yf
from typing import Dict, Any, Optional

class OandaData:
    def __init__(self, api_key: str, account_id: str, environment: str = "practice"):
        self.client = oandapyV20.API(access_token=api_key, environment=environment)
        self.account_id = account_id

    def fetch_candles(self, instrument: str, count: int = 100, granularity: str = "M15") -> pd.DataFrame:
        params = {
            "count": count,
            "granularity": granularity
        }
        r = instruments.InstrumentsCandles(instrument=instrument, params=params)
        self.client.request(r)
        
        candles = []
        for candle in r.response.get('candles'):
            if candle.get('complete'):
                candles.append({
                    'Time': candle.get('time'),
                    'Open': float(candle['mid']['o']),
                    'High': float(candle['mid']['h']),
                    'Low': float(candle['mid']['l']),
                    'Close': float(candle['mid']['c']),
                    'Volume': int(candle['volume'])
                })
        
        df = pd.DataFrame(candles)
        df['Time'] = pd.to_datetime(df['Time'])
        df.set_index('Time', inplace=True)
        return df

def get_oanda_market_data(api_key: str, account_id: str) -> Dict[str, Any]:
    oanda = OandaData(api_key, account_id)
    
    # Silver: XAG_USD from OANDA
    si_15m = oanda.fetch_candles("XAG_USD", granularity="M15", count=100)
    si_1h = oanda.fetch_candles("XAG_USD", granularity="H1", count=100)
    si_1d = oanda.fetch_candles("XAG_USD", granularity="D", count=30)
    
    # Macro analysis (Gold, DXY, Yields) from yfinance
    # GC=F (Gold), DX-Y.NYB (DXY), ^TNX (10Y Yield)
    gc_1d = yf.Ticker("GC=F").history(period="5d", interval="1d")
    dxy_1d = yf.Ticker("DX-Y.NYB").history(period="5d", interval="1d")
    tnx_1d = yf.Ticker("^TNX").history(period="5d", interval="1d")
    
    return {
        "si_15m": si_15m,
        "si_1h": si_1h,
        "si_1d": si_1d,
        "gc_1d": gc_1d,
        "dxy_1d": dxy_1d,
        "tnx_1d": tnx_1d
    }
