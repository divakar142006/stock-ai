"""
StockAI Agent Entry Point
=========================
Run this script to start the autonomous AI stock trading agent in paper or live mode.
"""

import sys
import time
import logging
import warnings

warnings.filterwarnings('ignore')

import config
from strategy.trader import AutonomousTrader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

def main():
    print("=" * 65)
    print("🤖 StockAI Autonomous Trading Agent — Real Market Engine")
    print("=" * 65)
    print(f"• Mode:               {config.TRADING_MODE} TRADING")
    print(f"• Watchlist Size:     {len(config.WATCHLIST)} stocks/ETFs")
    print(f"• Scan Interval:      Every {config.SCAN_INTERVAL_MINUTES} minutes")
    print(f"• Max Positions:      {config.MAX_POSITIONS}")
    print(f"• Stop Loss / Profit: -{int(config.STOP_LOSS_PCT*100)}% / +{int(config.TAKE_PROFIT_PCT*100)}%")
    print("=" * 65)

    trader = AutonomousTrader()

    logger.info("Executing initial market scan & AI analysis...")
    res = trader.run_scan_and_trade_cycle(force=True)
    
    print("\n--- Initial Scan Results ---")
    print(f"Scan Status:     {res.get('status')}")
    print(f"Trades Executed: {len(res.get('executed_trades', []))}")
    print("\nTop AI Stock Recommendations:")
    for rep in res.get('ai_reports', [])[:5]:
        print(f"  [{rep['signal']:^11}] {rep['symbol']:<6} Score: {rep['composite_score']}/100 | ${rep.get('current_price', 0):.2f} | {rep['reasoning']}")
    
    print("\nStarting 15-minute continuous autonomous trading loop. Press Ctrl+C to exit.\n")
    try:
        while True:
            time.sleep(config.SCAN_INTERVAL_MINUTES * 60)
            logger.info("Running scheduled 15-minute market scan...")
            trader.run_scan_and_trade_cycle()
    except KeyboardInterrupt:
        logger.info("Agent stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
