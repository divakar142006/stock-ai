"""
Real Market Data Fetcher & 1-Second Live Tick Generator
======================================================
Fetches live and historical market data using yfinance and generates
1-second high-frequency price tick fluctuations for 70+ market products.
"""

import time
import random
import logging
import warnings
import pandas as pd
import numpy as np

warnings.filterwarnings('ignore')
logging.getLogger('yfinance').setLevel(logging.ERROR)

import yfinance as yf

logger = logging.getLogger(__name__)

class MarketDataEngine:
    def __init__(self, cache_duration_secs=300):
        self.cache_duration = cache_duration_secs
        self._history_cache = {}
        self._quote_cache = {}
        self._live_ticks = {}

    def get_historical_data(self, symbol: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
        cache_key = f"{symbol}_{period}_{interval}"
        now = time.time()
        
        if cache_key in self._history_cache:
            df, timestamp = self._history_cache[cache_key]
            if now - timestamp < self.cache_duration:
                return df.copy()

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)
            if df.empty:
                return pd.DataFrame()
            
            df = df.dropna()
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            self._history_cache[cache_key] = (df, now)
            return df.copy()
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()

    def get_live_quote(self, symbol: str) -> dict:
        now = time.time()
        
        # If quote cached recently, apply 1-second micro-tick fluctuation for continuous live motion
        if symbol in self._quote_cache:
            base_quote, timestamp = self._quote_cache[symbol]
            if now - timestamp < 30: # 30s base quote refresh
                # Generate 1-second micro price tick fluctuation (±0.08%)
                cur_price = self._live_ticks.get(symbol, base_quote['price'])
                delta = (random.random() - 0.49) * 0.0016 * cur_price
                new_price = round(max(0.01, cur_price + delta), 2)
                self._live_ticks[symbol] = new_price
                
                prev_close = base_quote['previous_close']
                change = new_price - prev_close if prev_close else 0.0
                change_pct = (change / prev_close * 100.0) if prev_close else 0.0

                return {
                    "symbol": symbol,
                    "price": new_price,
                    "previous_close": prev_close,
                    "change": round(float(change), 2),
                    "change_pct": round(float(change_pct), 2),
                    "high": max(new_price, base_quote['high']),
                    "low": min(new_price, base_quote['low']),
                    "volume": base_quote['volume'],
                    "timestamp": now
                }

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ticker = yf.Ticker(symbol)
                fast_info = ticker.fast_info
                
                current_price = float(fast_info.last_price) if fast_info.last_price is not None else None
                prev_close = float(fast_info.previous_close) if fast_info.previous_close is not None else None
            
            if current_price is None or np.isnan(current_price):
                df = self.get_historical_data(symbol, period="5d", interval="1m")
                if not df.empty:
                    current_price = float(df['Close'].iloc[-1])
                    prev_close = float(df['Close'].iloc[-2]) if len(df) > 1 else current_price

            change = current_price - prev_close if prev_close else 0.0
            change_pct = (change / prev_close * 100.0) if prev_close else 0.0

            quote = {
                "symbol": symbol,
                "price": round(float(current_price), 2),
                "previous_close": round(float(prev_close), 2),
                "change": round(float(change), 2),
                "change_pct": round(float(change_pct), 2),
                "high": round(float(fast_info.day_high or current_price), 2),
                "low": round(float(fast_info.day_low or current_price), 2),
                "volume": int(fast_info.last_volume or 0),
                "timestamp": now
            }
            self._quote_cache[symbol] = (quote, now)
            self._live_ticks[symbol] = quote['price']
            return quote
        except Exception as e:
            logger.error(f"Error fetching live quote for {symbol}: {e}")
            return {
                "symbol": symbol,
                "price": 100.0,
                "previous_close": 100.0,
                "change": 0.0,
                "change_pct": 0.0,
                "high": 100.0,
                "low": 100.0,
                "volume": 0,
                "timestamp": now
            }

    def get_batch_quotes(self, symbols: list) -> dict:
        quotes = {}
        for sym in symbols:
            quotes[sym] = self.get_live_quote(sym)
        return quotes
