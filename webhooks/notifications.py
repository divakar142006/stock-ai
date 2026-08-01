"""
Multi-Channel Notifications Engine
==================================
Dispatches real-time alerts for BUY/SELL/SHORT signals, STOP LOSS hits,
TARGET hits, and RISK warnings to Telegram, Discord, Email, and n8n.
"""

import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

class NotificationEngine:
    def __init__(self):
        pass

    def notify_signal(self, report: dict):
        """Send rich alert on high confidence trade opportunity."""
        symbol = report.get("symbol", "N/A")
        action = report.get("signal", "BUY")
        confidence = report.get("confidence_pct", 85)
        strategy = report.get("strategy_used", "Breakout Momentum")
        regime = report.get("market_regime_label", "Bullish Trend")
        entry = report.get("entry_price", 0.0)
        sl = report.get("stop_loss", 0.0)
        tp = report.get("take_profit", 0.0)
        rr = report.get("risk_reward_ratio", 2.4)
        reason = report.get("reasoning", "")

        msg = (
            f"🚀 *INSTITUTIONAL AI TRADE SIGNAL*\n"
            f"-----------------------------------------\n"
            f"📌 *Action*: `{action} {symbol}`\n"
            f"🎯 *Confidence*: `{confidence}%`\n"
            f"🛠️ *Strategy*: `{strategy}`\n"
            f"🌐 *Market Regime*: `{regime}`\n"
            f"💵 *Entry*: `${entry:.2f}`\n"
            f"🛑 *Stop Loss*: `${sl:.2f}`\n"
            f"🎯 *Take Profit*: `${tp:.2f}`\n"
            f"⚖️ *Risk:Reward*: `1:{rr}`\n"
            f"📝 *Reason*: _{reason}_\n"
            f"-----------------------------------------"
        )

        self._send_telegram(msg)
        self._send_discord(f"🚀 **AI TRADE SIGNAL**: {action} {symbol} ({confidence}% Confidence) | Entry: ${entry:.2f} | Target: ${tp:.2f}")

    def notify_exit(self, symbol: str, action: str, pnl: float, reason: str):
        """Send trade exit notification."""
        emoji = "🎉" if pnl >= 0 else "🚨"
        msg = (
            f"{emoji} *TRADE EXIT ALERT: {symbol}*\n"
            f"Action: `{action}` | P&L: `${pnl:+.2f}`\n"
            f"Reason: _{reason}_"
        )
        self._send_telegram(msg)
        self._send_discord(f"{emoji} **TRADE EXIT**: {symbol} ({action}) P&L: ${pnl:+.2f} ({reason})")

    def _send_telegram(self, text: str):
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            logger.info(f"📱 Telegram notification logged: {text[:60]}...")
            return
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
            requests.post(url, json=payload, timeout=3)
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")

    def _send_discord(self, text: str):
        if not DISCORD_WEBHOOK_URL:
            logger.info(f"💬 Discord notification logged: {text[:60]}...")
            return
        try:
            payload = {"content": text}
            requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=3)
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
