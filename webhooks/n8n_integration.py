"""
n8n Automation & Webhook Integration Engine
===========================================
Emits live webhooks to n8n workflows when trades execute, AI signals trigger,
or risk limits are hit. Also accepts incoming n8n automation triggers.
"""

import os
import logging
import requests
import threading

logger = logging.getLogger(__name__)

# Default n8n webhook URL (can be customized via environment variable)
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/stockai-trader")

class N8nAutomationEngine:
    def __init__(self, db_manager=None):
        self.webhook_url = N8N_WEBHOOK_URL
        self.db = db_manager
        self.enabled = True

    def dispatch_event(self, event_type: str, data: dict):
        """
        Dispatches an event payload asynchronously to n8n workflow engine.
        """
        if not self.enabled:
            return

        def _send():
            payload = {
                "event": event_type,
                "data": data,
                "source": "StockAI_Trader_Engine"
            }
            try:
                res = requests.post(self.webhook_url, json=payload, timeout=3)
                status = "SUCCESS" if res.status_code in (200, 201) else f"STATUS_{res.status_code}"
                logger.info(f"⚡ n8n Webhook [{event_type}] dispatched -> {status}")
                if self.db:
                    self.db.log_n8n_event(event_type, payload, status)
            except Exception as e:
                # Log locally without crashing trader
                if self.db:
                    self.db.log_n8n_event(event_type, payload, f"DISPATCH_OFFLINE: {str(e)[:50]}")

        threading.Thread(target=_send, daemon=True).start()

    def on_trade_executed(self, trade_data: dict):
        """Triggered on BUY / SELL trade execution."""
        self.dispatch_event("TRADE_EXECUTED", trade_data)

    def on_high_confidence_signal(self, signal_data: dict):
        """Triggered when AI detects a STRONG BUY or STRONG SELL setup."""
        self.dispatch_event("AI_SIGNAL_DETECTED", signal_data)

    def on_risk_alert(self, alert_data: dict):
        """Triggered when Stop-Loss, Take-Profit, or Daily Drawdown triggers."""
        self.dispatch_event("RISK_ALERT_TRIGGERED", alert_data)
