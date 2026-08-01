import yfinance as yf

symbols = ['AAPL', 'NVDA', 'AMZN', 'MSFT', 'GOOGL', 'TSLA', 'SPY']
print("=================================================================")
print("REAL-WORLD STOCK MARKET DATA VERIFICATION")
print("=================================================================")

for sym in symbols:
    t = yf.Ticker(sym)
    df = t.history(period="5d")
    close_px = float(df['Close'].iloc[-1])
    open_px = float(df['Open'].iloc[-1])
    high_px = float(df['High'].iloc[-1])
    low_px = float(df['Low'].iloc[-1])
    vol = int(df['Volume'].iloc[-1])
    print(f"* {sym:6s} | Live Close: ${close_px:8.2f} | Open: ${open_px:8.2f} | High: ${high_px:8.2f} | Low: ${low_px:8.2f} | Volume: {vol:,}")

print("=================================================================")
