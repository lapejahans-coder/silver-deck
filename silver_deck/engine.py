import pandas as pd
import numpy as np
from datetime import datetime, time
import pytz
from typing import Dict, Any, Tuple

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    exp1 = series.ewm(span=12, adjust=False).mean()
    exp2 = series.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    v = df['Volume'].values
    tp = (df['High'] + df['Low'] + df['Close']).values / 3
    return pd.Series((tp * v).cumsum() / v.cumsum(), index=df.index)

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['High']
    low = df['Low']
    close = df['Close'].shift(1)
    tr = pd.concat([high - low, (high - close).abs(), (low - close).abs()], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def get_session_quality() -> str:
    """Classifies session quality based on UTC time."""
    now_utc = datetime.now(pytz.utc).time()
    # London: 08:00 - 16:00 UTC
    # US: 13:30 - 20:00 UTC
    if time(13, 30) <= now_utc <= time(20, 0):
        return "HIGH"
    elif (time(8, 0) <= now_utc <= time(16, 0)) or (time(20, 0) <= now_utc <= time(22, 0)):
        return "MEDIUM"
    else:
        return "LOW"

def get_macro_bias(dxy_df: pd.DataFrame, gc_df: pd.DataFrame, tnx_df: pd.DataFrame) -> Tuple[str, str]:
    if dxy_df.empty or gc_df.empty or tnx_df.empty:
        return "NEUTRAL", "Insufficient macro data."
    
    dxy_change = dxy_df['Close'].iloc[-1] - dxy_df['Close'].iloc[-2] if len(dxy_df) > 1 else 0
    gc_change = gc_df['Close'].iloc[-1] - gc_df['Close'].iloc[-2] if len(gc_df) > 1 else 0
    tnx_change = tnx_df['Close'].iloc[-1] - tnx_df['Close'].iloc[-2] if len(tnx_df) > 1 else 0
    
    bullish_factors = 0
    bearish_factors = 0
    
    if dxy_change < 0: bullish_factors += 1
    elif dxy_change > 0: bearish_factors += 1
    
    if gc_change > 0: bullish_factors += 1
    elif gc_change < 0: bearish_factors += 1
    
    if tnx_change < 0: bullish_factors += 1
    elif tnx_change > 0: bearish_factors += 1
    
    reasoning = f"DXY {'up' if dxy_change > 0 else 'down'}, Gold {'up' if gc_change > 0 else 'down'}, 10Y Yield {'up' if tnx_change > 0 else 'down'}."
    
    if bullish_factors > bearish_factors:
        return "BULLISH", reasoning
    elif bearish_factors > bullish_factors:
        return "BEARISH", reasoning
    else:
        return "NEUTRAL", reasoning

def get_regime(si_1h: pd.DataFrame, si_15m: pd.DataFrame) -> str:
    if si_1h.empty or len(si_1h) < 5:
        return "CHOPPY"
    
    # Simple higher high / lower low logic
    last_closes = si_1h['Close'].iloc[-5:]
    if all(last_closes.diff().dropna() > 0):
        return "TREND UP"
    elif all(last_closes.diff().dropna() < 0):
        return "TREND DOWN"
    
    # Check for range/choppy
    std = si_1h['Close'].iloc[-20:].std()
    mean = si_1h['Close'].iloc[-20:].mean()
    if std / mean < 0.005:
        return "RANGE"
    
    return "CHOPPY"

def get_momentum_score(df: pd.DataFrame) -> Tuple[str, str]:
    if df.empty or len(df) < 30:
        return "NEUTRAL", "Insufficient data for momentum."
    
    macd, signal, hist = calculate_macd(df['Close'])
    
    last_macd = macd.iloc[-1]
    last_signal = signal.iloc[-1]
    last_hist = hist.iloc[-1]
    prev_hist = hist.iloc[-2]
    
    if last_macd > last_signal and last_hist > prev_hist:
        return "PASS", "MACD bullish crossover with expanding histogram."
    elif last_macd < last_signal and last_hist < prev_hist:
        return "FAIL", "MACD bearish crossover with expanding histogram."
    else:
        return "NEUTRAL", "MACD and signal lines are converged or histogram is contracting."

def get_technical_score(df: pd.DataFrame) -> Tuple[str, str]:
    if df.empty or len(df) < 20:
        return "NEUTRAL", "Insufficient data for technicals."
    
    rsi = calculate_rsi(df['Close']).iloc[-1]
    vwap = calculate_vwap(df).iloc[-1]
    price = df['Close'].iloc[-1]
    
    if rsi > 70 and price > vwap:
        return "FAIL", f"RSI Overbought ({rsi:.2f}) and extended above VWAP."
    elif rsi < 30 and price < vwap:
        return "PASS", f"RSI Oversold ({rsi:.2f}) and extended below VWAP."
    else:
        return "NEUTRAL", f"RSI at {rsi:.2f}, price near VWAP."

def get_confirmation_score(df: pd.DataFrame) -> Tuple[str, str]:
    if df.empty or len(df) < 2:
        return "NEUTRAL", "Insufficient data for confirmation."
    
    last_vol = df['Volume'].iloc[-1]
    avg_vol = df['Volume'].iloc[-20:].mean()
    
    if last_vol > avg_vol * 1.5:
        return "PASS", "Strong volume expansion on latest candle."
    else:
        return "NEUTRAL", "Volume within normal range."

def get_event_risk() -> Tuple[str, str]:
    # Placeholder: In a real app, this would check an economic calendar.
    return "SAFE", "No major high-impact events detected in the immediate window."

class Signal:
    def __init__(self, action: str, market: str, price: float, session: str, regime: str, setup: str, confidence: str, entry: float, stop: float, targets: Tuple[float, float], rr: float, levels: Dict[str, float], scores: Dict[str, Tuple[str, str]], news: str):
        self.action = action
        self.market = market
        self.price = price
        self.session = session
        self.regime = regime
        self.setup = setup
        self.confidence = confidence
        self.entry = entry
        self.stop = stop
        self.targets = targets
        self.rr = rr
        self.levels = levels
        self.scores = scores
        self.news = news

def generate_signal(data: Dict[str, pd.DataFrame]) -> Signal:
    si_15m = data["si_15m"]
    si_1h = data["si_1h"]
    si_1d = data["si_1d"]
    
    price = si_15m['Close'].iloc[-1] if not si_15m.empty else 0.0
    session = get_session_quality()
    macro_bias, macro_reason = get_macro_bias(data["dxy_1d"], data["gc_1d"], data["tnx_1d"])
    regime = get_regime(si_1h, si_15m)
    mom_score, mom_reason = get_momentum_score(si_15m)
    tech_score, tech_reason = get_technical_score(si_15m)
    conf_score, conf_reason = get_confirmation_score(si_15m)
    event_risk, event_reason = get_event_risk()
    
    # Logic for ACTION
    action = "WAIT"
    setup = "WAIT"
    confidence = "LOW"
    
    if macro_bias == "BULLISH" and regime in ["TREND UP", "BREAKOUT"] and mom_score == "PASS" and event_risk == "SAFE":
        action = "LONG"
        setup = "BREAKOUT" if regime == "BREAKOUT" else "PULLBACK"
        confidence = "HIGH" if session == "HIGH" else "MEDIUM"
    elif macro_bias == "BEARISH" and regime in ["TREND DOWN", "BREAKDOWN"] and mom_score == "FAIL" and event_risk == "SAFE":
        action = "SHORT"
        setup = "BREAKOUT" if regime == "BREAKDOWN" else "PULLBACK"
        confidence = "HIGH" if session == "HIGH" else "MEDIUM"
    
    # Placeholder for levels and entry plan
    atr = calculate_atr(si_15m).iloc[-1] if not si_15m.empty else 0.5
    entry = price
    stop = price - (2 * atr) if action == "LONG" else price + (2 * atr)
    target1 = price + (4 * atr) if action == "LONG" else price - (4 * atr)
    target2 = price + (8 * atr) if action == "LONG" else price - (8 * atr)
    
    levels = {
        "Overnight High": si_1h['High'].max(),
        "Overnight Low": si_1h['Low'].min(),
        "Prior Day High": si_1d['High'].iloc[-2] if len(si_1d) > 1 else 0.0,
        "Prior Day Low": si_1d['Low'].iloc[-2] if len(si_1d) > 1 else 0.0,
        "Prior Day Close": si_1d['Close'].iloc[-2] if len(si_1d) > 1 else 0.0,
        "VWAP": calculate_vwap(si_15m).iloc[-1] if not si_15m.empty else 0.0,
    }
    
    scores = {
        "Macro Filter": (macro_bias, macro_reason),
        "Momentum": (mom_score, mom_reason),
        "RSI + VWAP + ATR": (tech_score, tech_reason),
        "Price / Volume Confirmation": (conf_score, conf_reason),
        "Event Risk": (event_risk, event_reason)
    }
    
    news = f"Focus remains on {macro_reason.split(',')[0]}."
    
    return Signal(
        action=action,
        market="SI",
        price=price,
        session=session,
        regime=regime,
        setup=setup,
        confidence=confidence,
        entry=entry,
        stop=stop,
        targets=(target1, target2),
        rr=2.0,
        levels=levels,
        scores=scores,
        news=news
    )
