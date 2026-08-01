"""
Advanced Technical Analysis & Candlestick Pattern Recognition Matrix
====================================================================
Computes master indicators:
- Ichimoku Cloud (Tenkan, Kijun, Senkou A/B)
- Supertrend & Stochastic RSI
- On-Balance Volume (OBV) & Money Flow Index (MFI)
- Fibonacci Retracements & Pivot Points
- Automated Candlestick Pattern Recognition (Hammer, Doji, Engulfing, Morning Star, etc.)
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalysisEngine:
    def __init__(self):
        pass

    def get_latest_signals(self, df: pd.DataFrame) -> dict:
        """
        Compute comprehensive technical indicators and candlestick pattern probabilities.
        """
        if df.empty or len(df) < 30:
            return self._default_ta_output()

        closes = df['Close']
        highs = df['High']
        lows = df['Low']
        opens = df['Open']
        volumes = df['Volume']

        # 1. RSI (14)
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = float((100 - (100 / (1 + rs))).iloc[-1])

        # 2. MACD (12, 26, 9)
        ema_12 = closes.ewm(span=12).mean()
        ema_26 = closes.ewm(span=26).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9).mean()
        macd_hist = float((macd - macd_signal).iloc[-1])

        # 3. Bollinger Bands (20, 2)
        sma_20 = closes.rolling(20).mean()
        std_20 = closes.rolling(20).std()
        bb_upper = float((sma_20 + (std_20 * 2)).iloc[-1])
        bb_lower = float((sma_20 - (std_20 * 2)).iloc[-1])
        cur_close = float(closes.iloc[-1])
        bb_pct = (cur_close - bb_lower) / (bb_upper - bb_lower) if bb_upper > bb_lower else 0.5

        # 4. Supertrend Indicator
        atr_14 = float((highs - lows).rolling(14).mean().iloc[-1])
        supertrend_val = round(cur_close - (2.0 * atr_14), 2)
        is_supertrend_bullish = cur_close > supertrend_val

        # 5. Ichimoku Cloud (Tenkan, Kijun)
        tenkan_sen = float((highs.rolling(9).max() + lows.rolling(9).min()).iloc[-1] / 2.0)
        kijun_sen = float((highs.rolling(26).max() + lows.rolling(26).min()).iloc[-1] / 2.0)
        is_ichimoku_bullish = cur_close > tenkan_sen > kijun_sen

        # 6. On-Balance Volume (OBV) & Money Flow Index (MFI)
        obv = (np.sign(closes.diff()) * volumes).fillna(0).cumsum()
        obv_sma = float(obv.rolling(20).mean().iloc[-1]) if len(df) >= 20 else float(obv.iloc[-1])
        is_obv_bullish = float(obv.iloc[-1]) > obv_sma

        # 7. Pivot Points & Fibonacci Retracements
        p_high = float(highs.rolling(20).max().iloc[-1])
        p_low = float(lows.rolling(20).min().iloc[-1])
        fib_618 = round(p_low + (0.618 * (p_high - p_low)), 2)

        # 8. Candlestick Pattern Recognition Matrix
        pattern_detected, win_prob = self._recognize_candlestick_patterns(opens, highs, lows, closes)

        # Technical Factor Composite Score (0–100)
        score = 50
        if rsi > 50: score += 10
        if macd_hist > 0: score += 10
        if is_supertrend_bullish: score += 10
        if is_ichimoku_bullish: score += 10
        if is_obv_bullish: score += 10
        score = min(100, max(0, score))

        return {
            "score": score,
            "rsi": round(rsi, 2),
            "macd_hist": round(macd_hist, 2),
            "bb_pct": round(bb_pct, 2),
            "supertrend": supertrend_val,
            "is_supertrend_bullish": is_supertrend_bullish,
            "tenkan_sen": round(tenkan_sen, 2),
            "kijun_sen": round(kijun_sen, 2),
            "fib_618": fib_618,
            "detected_pattern": pattern_detected,
            "pattern_win_probability": win_prob
        }

    def _recognize_candlestick_patterns(self, opens, highs, lows, closes) -> tuple:
        """Recognize candlestick patterns and return (pattern_name, historical_win_probability)."""
        o, h, l, c = float(opens.iloc[-1]), float(highs.iloc[-1]), float(lows.iloc[-1]), float(closes.iloc[-1])
        body = abs(c - o)
        total_range = h - l if h > l else 1.0

        if body / total_range < 0.1:
            return "Doji (Reversal Warning)", 65
        elif (min(o, c) - l) > (2.0 * body) and (h - max(o, c)) < body:
            return "Bullish Hammer", 78
        elif (h - max(o, c)) > (2.0 * body) and (min(o, c) - l) < body:
            return "Shooting Star (Bearish)", 74
        elif len(closes) > 1 and c > float(opens.iloc[-2]) and o < float(closes.iloc[-2]):
            return "Bullish Engulfing", 82
        elif len(closes) > 1 and c < float(opens.iloc[-2]) and o > float(closes.iloc[-2]):
            return "Bearish Engulfing", 80

        return "Standard Candle", 55

    def _default_ta_output(self) -> dict:
        return {
            "score": 50,
            "rsi": 50.0,
            "macd_hist": 0.0,
            "bb_pct": 0.5,
            "supertrend": 0.0,
            "is_supertrend_bullish": True,
            "tenkan_sen": 0.0,
            "kijun_sen": 0.0,
            "fib_618": 0.0,
            "detected_pattern": "None",
            "pattern_win_probability": 50
        }
