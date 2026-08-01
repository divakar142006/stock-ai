"""
StockAI Interconnected 1-Second Real-Time Server
===============================================
Flask server with Server-Sent Events (SSE) stream (/api/stream) pushing live
database changes, 1-second price ticks, AI signals, and n8n webhooks every 1.0 second.
"""

import json
import time
import logging
import threading
from flask import Flask, jsonify, request, send_from_directory, Response
from apscheduler.schedulers.background import BackgroundScheduler
import yfinance as yf
import config
from strategy.trader import AutonomousTrader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="dashboard", static_url_path="")

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

# Initialize trader
trader = AutonomousTrader()

# Background scheduler for 5-minute full AI market scans
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=lambda: trader.run_scan_and_trade_cycle(),
    trigger="interval",
    minutes=config.SCAN_INTERVAL_MINUTES,
    id="ai_trading_scan"
)
scheduler.start()

@app.route("/")
def index():
    return send_from_directory("dashboard", "index.html")

@app.route("/api/summary", methods=["GET"])
def get_summary():
    """Get full real-time dashboard summary."""
    data = trader.get_dashboard_summary()
    return jsonify(data)

@app.route("/api/candles/<symbol>", methods=["GET"])
def get_candles(symbol):
    """
    Get OHLCV historical candlestick data formatted for TradingView Lightweight Charts.
    """
    symbol = symbol.upper()
    df = trader.market_data.get_historical_data(symbol, period="6mo", interval="1d")
    
    if df.empty:
        return jsonify([])

    candles = []
    volume_data = []
    
    for idx, row in df.iterrows():
        time_str = idx.strftime("%Y-%m-%d")
        open_price = float(row['Open'])
        high_price = float(row['High'])
        low_price = float(row['Low'])
        close_price = float(row['Close'])
        volume = int(row['Volume'])
        
        candles.append({
            "time": time_str,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2)
        })
        
        color = "#10b981" if close_price >= open_price else "#ef4444"
        volume_data.append({
            "time": time_str,
            "value": volume,
            "color": color
        })

    return jsonify({"candles": candles, "volume": volume_data})

@app.route("/api/stream", methods=["GET"])
def sse_stream():
    """
    Server-Sent Events (SSE) 1-Second Real-Time Data Stream.
    Pushes live 1-second price ticks, AI signals, quotes, and trades every 1.0 second.
    """
    def event_generator():
        while True:
            try:
                summary = trader.get_dashboard_summary()
                payload = json.dumps(summary)
                yield f"data: {payload}\n\n"
            except Exception as e:
                logger.error(f"SSE stream error: {e}")
            time.sleep(1.0) # 1-second streaming frequency

    return Response(event_generator(), mimetype="text/event-stream")

@app.route("/api/scan", methods=["POST"])
def trigger_scan():
    """Manually trigger an immediate AI market scan in background thread."""
    threading.Thread(target=trader.run_scan_and_trade_cycle, kwargs={"force": True}, daemon=True).start()
    return jsonify({"status": "SCAN_TRIGGERED", "message": "Market scan started in background"})

@app.route("/api/control", methods=["POST"])
def control_trader():
    """Start or pause the autonomous trader agent."""
    body = request.get_json() or {}
    action = body.get("action", "").lower()
    
    if action == "pause":
        trader.is_active = False
        logger.info("Trader paused by user.")
    elif action == "resume":
        trader.is_active = True
        logger.info("Trader resumed by user.")

    return jsonify({"is_active": trader.is_active, "status": "ACTIVE" if trader.is_active else "PAUSED"})

@app.route("/api/order", methods=["POST"])
def manual_order():
    """Manual trade override (buy or sell)."""
    body = request.get_json() or {}
    symbol = body.get("symbol", "").upper()
    qty = int(body.get("qty", 1))
    side = body.get("side", "buy").lower()

    if not symbol or qty <= 0:
        return jsonify({"status": "ERROR", "message": "Invalid symbol or quantity"}), 400

    quote = trader.market_data.get_live_quote(symbol)
    price = quote.get("price", 100.0)

    res = trader.broker.submit_order(symbol=symbol, qty=qty, side=side, current_price=price)
    
    log_entry = {
        "timestamp": trader.last_scan_time or "MANUAL",
        "symbol": symbol,
        "action": side.upper(),
        "qty": qty,
        "price": price,
        "reason": "MANUAL OVERRIDE",
        "status": res.get("status", "EXECUTED")
    }
    trader.trade_logs.insert(0, log_entry)
    trader.db.log_trade(symbol, side.upper(), qty, price, "MANUAL OVERRIDE")
    trader.n8n.on_trade_executed(log_entry)

    return jsonify(res)

@app.route("/api/webhook/n8n", methods=["POST"])
def n8n_incoming_webhook():
    """Incoming n8n Automation Webhook endpoint."""
    body = request.get_json() or {}
    action = body.get("action", "").lower()

    logger.info(f"⚡ Received incoming n8n Automation Webhook action: {action}")
    trader.db.log_n8n_event("INCOMING_N8N_WORKFLOW", body, "RECEIVED")

    if action == "scan":
        threading.Thread(target=trader.run_scan_and_trade_cycle, kwargs={"force": True}, daemon=True).start()
        return jsonify({"status": "SUCCESS", "message": "Scan triggered by n8n"})

    elif action == "trade":
        symbol = body.get("symbol", "").upper()
        qty = int(body.get("qty", 1))
        side = body.get("side", "buy").lower()
        if symbol:
            quote = trader.market_data.get_live_quote(symbol)
            price = quote.get("price", 100.0)
            res = trader.broker.submit_order(symbol, qty, side, current_price=price)
            trader.db.log_trade(symbol, side.upper(), qty, price, "N8N_AUTOMATION_TRIGGER")
            return jsonify({"status": "SUCCESS", "order": res})

    elif action == "summary":
        return jsonify(trader.get_dashboard_summary())

    return jsonify({"status": "ERROR", "message": f"Unknown action: {action}"}), 400

@app.route("/api/news", methods=["GET"])
def get_news():
    """Fetch real financial news for major tickers."""
    tickers = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL", "AMZN", "META"]
    news_feed = []
    
    try:
        for ticker in tickers:
            news = yf.Ticker(ticker).news
            if not news:
                continue
            for item in news[:2]:
                content = item.get("content", item)
                title = content.get("title", "No Title")
                
                provider = content.get("provider", {})
                source = provider.get("displayName") if isinstance(provider, dict) else content.get("publisher", "Unknown")
                
                url_info = content.get("clickThroughUrl", {})
                url = url_info.get("url") if isinstance(url_info, dict) else content.get("link", "#")
                
                pub_time = content.get("pubDate") or content.get("providerPublishTime")
                
                news_feed.append({
                    "title": f"{ticker}: {title}",
                    "source": source,
                    "timestamp": str(pub_time),
                    "url": url,
                    "tag": ticker
                })
                
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        
    return jsonify({"news": news_feed})

@app.route("/api/outcomes", methods=["GET"])
def get_outcomes():
    return jsonify({
        "outcomes": trader.self_learning.outcomes,
        "stats": trader.self_learning.get_learning_stats(),
        "n8n_logs": trader.db.get_recent_n8n_logs(10)
    })

if __name__ == "__main__":
    logger.info(f"🚀 StockAI 1-Second Real-Time Server starting on http://{config.DASHBOARD_HOST}:{config.DASHBOARD_PORT}")
    app.run(host=config.DASHBOARD_HOST, port=config.DASHBOARD_PORT, debug=False)
