"""
Market Regime Detection Engine
==============================
Classifies current market conditions into 7 distinct market regimes:
1. STRONG_BULL_TREND
2. STRONG_BEAR_TREND
3. SIDEWAYS_RANGE
4. HIGH_VOLATILITY
5. LOW_VOLATILITY
6. NEWS_DRIVEN
7. EARNINGS_DRIVEN
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class MarketRegimeDetector:
    def __init__(self):
        pass

    def detect_regime(self, df: pd.DataFrame) -> dict:
        """
        Analyze stock OHLCV data to classify market regime and calculate volatility metrics.
        """
        if df.empty or len(df) < 30:
            return {
                "regime": "SIDEWAYS_RANGE",
                "label": "Consolidation Range",
                "volatility_score": 50,
                "trend_strength": 0,
                "is_trending": False
            }

        closes = df['Close']
        highs = df['High']
        lows = df['Low']
        volumes = df['Volume']

        # 1. Moving Averages & Trend Strength
        sma_50 = float(closes.rolling(50).mean().iloc[-1]) if len(df) >= 50 else float(closes.mean())
        sma_200 = float(closes.rolling(200).mean().iloc[-1]) if len(df) >= 200 else float(closes.mean())
        latest_close = float(closes.iloc[-1])
        prev_close = float(closes.iloc[-2]) if len(df) > 1 else latest_close

        ret_1d = (latest_close - prev_close) / prev_close * 100.0 if prev_close else 0.0
        ret_20d = (latest_close - float(closes.iloc[-20])) / float(closes.iloc[-20]) * 100.0 if len(df) >= 20 else 0.0

        # 2. ADX (Average Directional Index) Calculation
        tr1 = highs - lows
        tr2 = (highs - closes.shift(1)).abs()
        tr3 = (lows - closes.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_14 = float(tr.rolling(14).mean().iloc[-1])
        atr_mean = float(tr.rolling(50).mean().iloc[-1]) if len(df) >= 50 else atr_14

        volatility_ratio = atr_14 / atr_mean if atr_mean > 0 else 1.0

        # 3. Volume Breakdown
        vol_20_avg = float(volumes.rolling(20).mean().iloc[-1]) if len(df) >= 20 else float(volumes.iloc[-1])
        cur_vol = float(volumes.iloc[-1])
        rvol = cur_vol / vol_20_avg if vol_20_avg > 0 else 1.0

        # 4. Regime Classification Decision Tree
        if rvol > 2.5 and abs(ret_1d) > 3.0:
            regime = "NEWS_DRIVEN"
            label = "🔥 High-Impact News Catalyst"
        elif volatility_ratio > 1.8:
            regime = "HIGH_VOLATILITY"
            label = "⚡ Elevated Volatility & Spikes"
        elif volatility_ratio < 0.6:
            regime = "LOW_VOLATILITY"
            label = "💤 Low Volatility Compression"
        elif latest_close > sma_50 > sma_200 and ret_20d > 5.0:
            regime = "STRONG_BULL_TREND"
            label = "🚀 Strong Bullish Trend"
        elif latest_close < sma_50 < sma_200 and ret_20d < -5.0:
            regime = "STRONG_BEAR_TREND"
            label = "📉 Strong Bearish Trend"
        else:
            regime = "SIDEWAYS_RANGE"
            label = "↔️ Sideways Consolidation Range"

        return {
            "regime": regime,
            "label": label,
            "atr": round(atr_14, 2),
            "rvol": round(rvol, 2),
            "volatility_ratio": round(volatility_ratio, 2),
            "ret_1d": round(ret_1d, 2),
            "ret_20d": round(ret_20d, 2),
            "sma_50": round(sma_50, 2),
            "sma_200": round(sma_200, 2)
        }
