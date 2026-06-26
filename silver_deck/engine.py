import pandas as pd
import numpy as np
import os
from datetime import datetime, time
import pytz
from typing import Dict, Any, Optional, Tuple

MNQ_POINT_VALUE_USD = 2.0
NQ_POINT_VALUE_USD = 20.0

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
    """Classifies NASDAQ futures session quality based on UTC time."""
    now_utc = datetime.now(pytz.utc).time()
    # RTH: 13:30 - 20:00 UTC during US daylight saving time.
    # Daily futures break: 21:00 - 22:00 UTC.
    if time(21, 0) <= now_utc < time(22, 0):
        return "CLOSED"
    if time(13, 30) <= now_utc <= time(20, 0):
        return "RTH"
    elif time(10, 0) <= now_utc < time(13, 30):
        return "PRE-MARKET"
    else:
        return "ETH-GLOBEX"

def get_macro_bias(tnx_df: pd.DataFrame, vix_df: pd.DataFrame, es_df: pd.DataFrame, qqq_df: pd.DataFrame, dxy_df: pd.DataFrame) -> Tuple[str, str]:
    if tnx_df.empty or vix_df.empty or es_df.empty or qqq_df.empty:
        return "NEUTRAL", "Insufficient macro data."
    
    tnx_change = tnx_df['Close'].iloc[-1] - tnx_df['Close'].iloc[-2] if len(tnx_df) > 1 else 0
    vix_change = vix_df['Close'].iloc[-1] - vix_df['Close'].iloc[-2] if len(vix_df) > 1 else 0
    es_change = es_df['Close'].iloc[-1] - es_df['Close'].iloc[-2] if len(es_df) > 1 else 0
    qqq_change = qqq_df['Close'].iloc[-1] - qqq_df['Close'].iloc[-2] if len(qqq_df) > 1 else 0
    dxy_change = dxy_df['Close'].iloc[-1] - dxy_df['Close'].iloc[-2] if len(dxy_df) > 1 else 0
    
    bullish_factors = 0
    bearish_factors = 0
    
    if tnx_change < 0: bullish_factors += 1
    elif tnx_change > 0: bearish_factors += 1

    if vix_change < 0: bullish_factors += 1
    elif vix_change > 0: bearish_factors += 1

    if es_change > 0: bullish_factors += 1
    elif es_change < 0: bearish_factors += 1

    if qqq_change > 0: bullish_factors += 1
    elif qqq_change < 0: bearish_factors += 1

    if dxy_change < 0: bullish_factors += 0.5
    elif dxy_change > 0: bearish_factors += 0.5
    
    reasoning = (
        f"10Y Yield {'up' if tnx_change > 0 else 'down'}, "
        f"VIX {'up' if vix_change > 0 else 'down'}, "
        f"ES {'up' if es_change > 0 else 'down'}, "
        f"QQQ {'up' if qqq_change > 0 else 'down'}, "
        f"DXY {'up' if dxy_change > 0 else 'down'}."
    )
    
    if bullish_factors > bearish_factors:
        return "BULLISH", reasoning
    elif bearish_factors > bullish_factors:
        return "BEARISH", reasoning
    else:
        return "NEUTRAL", reasoning

def get_regime(nq_1h: pd.DataFrame, nq_15m: pd.DataFrame) -> str:
    if nq_1h.empty or len(nq_1h) < 20 or nq_15m.empty:
        return "CHOPPY"
    
    last_closes = nq_1h['Close'].iloc[-5:]
    if all(last_closes.diff().dropna() > 0):
        return "TREND UP"
    elif all(last_closes.diff().dropna() < 0):
        return "TREND DOWN"

    recent_high = nq_1h['High'].iloc[-20:-1].max()
    recent_low = nq_1h['Low'].iloc[-20:-1].min()
    last_close = nq_1h['Close'].iloc[-1]

    if last_close > recent_high:
        return "BREAKOUT"
    if last_close < recent_low:
        return "BREAKDOWN"
    
    std = nq_1h['Close'].iloc[-20:].std()
    mean = nq_1h['Close'].iloc[-20:].mean()
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

def _env_float(name: str, default: Optional[float] = None) -> Optional[float]:
    value = os.environ.get(name)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except ValueError:
        return default

def get_prop_firm_risk_plan(entry: float, stop: float, action: str) -> Dict[str, Any]:
    account_balance = _env_float("ACCOUNT_BALANCE_NGN", 200000.0)
    max_drawdown_pct = _env_float("MAX_DRAWDOWN_PCT", 20.0)
    profit_target_pct = _env_float("PROFIT_TARGET_PCT", 10.0)
    phase_count = int(_env_float("PHASE_COUNT", 2.0) or 2)
    usd_ngn_rate = _env_float("USD_NGN_RATE")

    max_drawdown = account_balance * max_drawdown_pct / 100
    phase_target = account_balance * profit_target_pct / 100
    normal_risk = min(account_balance * 0.01, max_drawdown * 0.10)
    hard_max_risk = min(account_balance * 0.02, max_drawdown * 0.10)
    daily_stop = min(account_balance * 0.02, max_drawdown * 0.10)
    stop_distance = abs(entry - stop) if action != "WAIT" else 0.0

    contract = "MNQ"
    estimated_risk_usd = stop_distance * MNQ_POINT_VALUE_USD if stop_distance else 0.0
    estimated_risk_ngn = estimated_risk_usd * usd_ngn_rate if usd_ngn_rate and stop_distance else None
    risk_fits = action == "WAIT" or (estimated_risk_ngn is not None and estimated_risk_ngn <= hard_max_risk)

    return {
        "Account Balance": account_balance,
        "Max Drawdown": max_drawdown,
        "Phase Target": phase_target,
        "Total Evaluation Target": phase_target * phase_count,
        "Normal Risk/Trade": normal_risk,
        "Hard Max Risk/Trade": hard_max_risk,
        "Daily Stop": daily_stop,
        "Contract": contract,
        "Stop Distance": stop_distance,
        "Estimated Risk USD": estimated_risk_usd,
        "Estimated Risk NGN": estimated_risk_ngn,
        "USD/NGN Rate": usd_ngn_rate,
        "Risk Fits": risk_fits,
    }

class Signal:
    def __init__(self, action: str, market: str, price: float, session: str, regime: str, setup: str, confidence: str, entry: float, stop: float, targets: Tuple[float, float], rr: float, levels: Dict[str, float], scores: Dict[str, Tuple[str, str]], news: str, risk_plan: Dict[str, Any]):
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
        self.risk_plan = risk_plan

def generate_signal(data: Dict[str, pd.DataFrame]) -> Signal:
    nq_15m = data["nq_15m"]
    nq_1h = data["nq_1h"]
    nq_1d = data["nq_1d"]
    
    price = nq_15m['Close'].iloc[-1] if not nq_15m.empty else 0.0
    session = get_session_quality()
    macro_bias, macro_reason = get_macro_bias(data["tnx_1d"], data["vix_1d"], data["es_1d"], data["qqq_1d"], data["dxy_1d"])
    regime = get_regime(nq_1h, nq_15m)
    mom_score, mom_reason = get_momentum_score(nq_15m)
    tech_score, tech_reason = get_technical_score(nq_15m)
    conf_score, conf_reason = get_confirmation_score(nq_15m)
    event_risk, event_reason = get_event_risk()
    
    # Logic for ACTION
    action = "WAIT"
    setup = "WAIT"
    confidence = "LOW"
    
    if macro_bias == "BULLISH" and regime in ["TREND UP", "BREAKOUT"] and mom_score == "PASS" and event_risk == "SAFE":
        action = "LONG"
        setup = "BREAKOUT" if regime == "BREAKOUT" else "PULLBACK"
        confidence = "HIGH" if session == "RTH" else "MEDIUM"
    elif macro_bias == "BEARISH" and regime in ["TREND DOWN", "BREAKDOWN"] and mom_score == "FAIL" and event_risk == "SAFE":
        action = "SHORT"
        setup = "BREAKOUT" if regime == "BREAKDOWN" else "PULLBACK"
        confidence = "HIGH" if session == "RTH" else "MEDIUM"
    
    atr = calculate_atr(nq_15m).iloc[-1] if not nq_15m.empty else 0.5
    entry = price
    stop = price - (2 * atr) if action == "LONG" else price + (2 * atr)
    target1 = price + (4 * atr) if action == "LONG" else price - (4 * atr)
    target2 = price + (8 * atr) if action == "LONG" else price - (8 * atr)
    risk_plan = get_prop_firm_risk_plan(entry, stop, action)

    if not risk_plan["Risk Fits"]:
        action = "WAIT"
        setup = "WAIT"
        confidence = "LOW"

    if action == "WAIT":
        stop = price
        target1 = price
        target2 = price
        risk_plan = get_prop_firm_risk_plan(entry, stop, action)
    
    levels = {
        "Overnight High": nq_1h['High'].max(),
        "Overnight Low": nq_1h['Low'].min(),
        "Prior Day High": nq_1d['High'].iloc[-2] if len(nq_1d) > 1 else 0.0,
        "Prior Day Low": nq_1d['Low'].iloc[-2] if len(nq_1d) > 1 else 0.0,
        "Prior Day Close": nq_1d['Close'].iloc[-2] if len(nq_1d) > 1 else 0.0,
        "VWAP": calculate_vwap(nq_15m).iloc[-1] if not nq_15m.empty else 0.0,
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
        market=risk_plan["Contract"],
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
        news=news,
        risk_plan=risk_plan
    )
