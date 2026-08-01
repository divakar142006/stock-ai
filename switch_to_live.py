"""
Interactive Helper: Switch StockAI Agent to LIVE Real-Money Trading Mode
========================================================================
Run this script to enter your Alpaca Live API keys and instantly activate
real-money autonomous trading!
"""

import sys

def enable_live_mode():
    print("=================================================================")
    print("💵 SETUP LIVE REAL-MONEY TRADING FOR STOCKAI AGENT")
    print("=================================================================")
    print("Please enter your Alpaca LIVE API Credentials:")
    
    live_key = input("Enter Alpaca Live API Key ID: ").strip()
    live_secret = input("Enter Alpaca Live Secret Key: ").strip()

    if not live_key or not live_secret:
        print("\n❌ Error: Live API Key ID and Secret Key cannot be empty!")
        sys.exit(1)

    config_path = "config.py"
    with open(config_path, "r") as f:
        content = f.read()

    content = content.replace('TRADING_MODE = os.getenv("TRADING_MODE", "PAPER")', 'TRADING_MODE = "LIVE"')
    content = content.replace('ALPACA_LIVE_API_KEY = os.getenv("ALPACA_LIVE_API_KEY", "")', f'ALPACA_LIVE_API_KEY = "{live_key}"')
    content = content.replace('ALPACA_LIVE_SECRET_KEY = os.getenv("ALPACA_LIVE_SECRET_KEY", "")', f'ALPACA_LIVE_SECRET_KEY = "{live_secret}"')

    with open(config_path, "w") as f:
        f.write(content)

    print("\n=================================================================")
    print("🟢 SUCCESS! StockAI Agent is now configured for LIVE REAL-MONEY TRADING!")
    print("=================================================================")
    print("Please restart your server by running: python app.py")
    print("=================================================================")

if __name__ == "__main__":
    enable_live_mode()
