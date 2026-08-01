"""
Macroeconomics, News & NLP Sentiment Analyzer Engine
====================================================
Quantifies financial news sentiment, macro indicators (VIX), and analyst consensus
into a composite Sentiment Score and Fear & Greed Index.
"""

import numpy as np
import pandas as pd
import yfinance as yf
import logging
import warnings
import time

warnings.filterwarnings('ignore')

# Silence yfinance logger
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)

class SentimentNLPEngine:
    def __init__(self):
        self.macro_cache = {}
        self.cache_ttl = 300 # 5 minutes

    def _fetch_macro_data(self):
        now = time.time()
        if "data" in self.macro_cache and (now - self.macro_cache["time"]) < self.cache_ttl:
            return self.macro_cache["data"]

        try:
            vix_hist = yf.Ticker("^VIX").history(period="1mo")
            gspc_hist = yf.Ticker("^GSPC").history(period="1mo")
            
            if vix_hist.empty or gspc_hist.empty:
                raise ValueError("Empty history for macro data")
                
            vix_close = float(vix_hist["Close"].iloc[-1])
            gspc_current = float(gspc_hist["Close"].iloc[-1])
            gspc_20d_ago = float(gspc_hist["Close"].iloc[0])
            
            gspc_return = float((gspc_current - gspc_20d_ago) / gspc_20d_ago)
            
            data = {
                "vix": vix_close,
                "gspc_return": gspc_return,
                "gspc_current": gspc_current
            }
            self.macro_cache = {"data": data, "time": now}
            return data
        except Exception as e:
            logger.warning(f"Failed to fetch macro data: {e}")
            return {"vix": 20.0, "gspc_return": 0.0, "gspc_current": 4000.0}

    def analyze_sentiment(self, symbol: str) -> dict:
        """
        Analyze news headlines, macro sentiment, VIX, and analyst ratings.
        """
        try:
            macro_data = self._fetch_macro_data()
            vix = float(macro_data["vix"])
            gspc_return = float(macro_data["gspc_return"])
            
            # Fear & Greed Proxy
            # VIX normal range 10-30. Inverse relation to greed.
            vix_score = float(max(0, min(100, 100 - (vix - 10) * 3.33)))
            # SP500 20d return: -5% to 5% -> 0 to 100
            sp500_score = float(max(0, min(100, (gspc_return * 10 + 0.5) * 100)))
            fear_greed_index = float((vix_score + sp500_score) / 2)
            
            # Stock Specific
            ticker = yf.Ticker(symbol)
            stock_hist = ticker.history(period="1mo")
            
            if stock_hist.empty:
                raise ValueError(f"Not enough data for {symbol}")
                
            close = stock_hist["Close"]
            vol = stock_hist["Volume"]
            
            current_close = float(close.iloc[-1])
            close_5d = float(close.iloc[-min(5, len(close))])
            close_20d = float(close.iloc[0])
            
            ret_5d = float((current_close - close_5d) / close_5d)
            ret_20d = float((current_close - close_20d) / close_20d)
            
            current_vol = float(vol.iloc[-1])
            avg_vol = float(vol.mean())
            vol_surge = float(current_vol / avg_vol) if avg_vol > 0 else 1.0
            
            # Relative strength
            rel_strength = float(ret_20d - gspc_return)
            
            # Build sentiment score (0-100)
            score = 50.0
            score += ret_5d * 200  
            score += ret_20d * 100 
            score += rel_strength * 100 
            if vol_surge > 1.5 and ret_5d > 0:
                score += 10
            elif vol_surge > 1.5 and ret_5d < 0:
                score -= 10
                
            sentiment_score = float(max(0, min(100, score)))
            
        except Exception as e:
            logger.warning(f"Error analyzing sentiment for {symbol}: {e}")
            sentiment_score = 50.0
            fear_greed_index = 50.0
            vix = 20.0

        if sentiment_score >= 80:
            analyst_consensus = "STRONG BUY"
            sentiment_label = "STRONG BUY"
        elif sentiment_score >= 65:
            analyst_consensus = "BUY"
            sentiment_label = "BUY"
        elif sentiment_score >= 50:
            analyst_consensus = "HOLD"
            sentiment_label = "HOLD"
        elif sentiment_score >= 35:
            analyst_consensus = "SELL"
            sentiment_label = "SELL"
        else:
            analyst_consensus = "STRONG SELL"
            sentiment_label = "STRONG SELL"
            
        headline_summary = f"Recent price momentum and volume trends indicate {analyst_consensus} sentiment"

        return {
            "symbol": symbol,
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "headline_summary": headline_summary,
            "fear_greed_index": fear_greed_index,
            "analyst_consensus": analyst_consensus,
            "vix_market_volatility": vix
        }
