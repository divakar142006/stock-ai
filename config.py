import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Dashboard Host & Port Config
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
DASHBOARD_PORT = int(os.getenv("PORT", os.getenv("DASHBOARD_PORT", 5050)))

# System Trading Mode ("PAPER" or "LIVE" or "BACKTEST")
TRADING_MODE = os.getenv("TRADING_MODE", "LIVE")

# User Alpaca Credentials (Paper Trading Endpoint)
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "YOUR_ALPACA_KEY_HERE")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "YOUR_ALPACA_SECRET_HERE")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# Alpaca Live Real-Money Credentials
ALPACA_LIVE_API_KEY = os.getenv("ALPACA_LIVE_API_KEY", "YOUR_ALPACA_LIVE_KEY_HERE")
ALPACA_LIVE_SECRET_KEY = os.getenv("ALPACA_LIVE_SECRET_KEY", "YOUR_ALPACA_LIVE_SECRET_HERE")
ALPACA_LIVE_BASE_URL = "https://api.alpaca.markets"

# 70+ Universal Stock Market Watchlist
WATCHLIST = [
    # Mega-Cap Tech Leaders
    "AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA",
    # Semiconductors & Hardware
    "AMD", "AVGO", "INTC", "QCOM", "ARM", "MU", "TXN",
    # Financial Services & Banks
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "V", "MA",
    # Healthcare & Biotech
    "LLY", "UNH", "JNJ", "PFE", "ABBV", "MRK", "AMGN", "BMY",
    # Energy, Defense & Industrials
    "XOM", "CVX", "COP", "CAT", "GE", "LMT", "RTX", "BA",
    # Consumer & Retail
    "WMT", "COST", "TGT", "HD", "PG", "KO", "PEP", "NKE",
    # Major Market Indices & Sector ETFs
    "SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLV", "XLE", "XLY",
    # High-Growth Tech & Crypto Proxies
    "COIN", "MARA", "RIOT", "MSTR", "PLTR", "SNOW", "NET", "CRWD", "DDOG"
]

# AI Risk Management & Execution Thresholds
QUALITY_GATE_CONFIDENCE_MIN = 85  # Minimum 85% confidence required for auto trade execution
RISK_REWARD_MIN = 2.0             # Minimum 1:2 Risk-to-Reward ratio
STOP_LOSS_PCT = 0.05              # 5% default stop loss
TAKE_PROFIT_PCT = 0.15            # 15% default take profit
RISK_PER_TRADE_PCT = 0.01         # Max 1.0% account risk per trade
MAX_DAILY_LOSS_PCT = 0.02         # Max 2.0% daily loss limit (Emergency Halt)
MAX_POSITION_PCT = 0.10           # Maximum position limit
MAX_POSITIONS = 5                 # Maximum concurrent positions allowed
SCAN_INTERVAL_MINUTES = 5         # Automated scanning frequency (minutes)
STREAM_INTERVAL_SECONDS = 1       # 1-second real-time streaming interval
