"""
SQLite Database Manager
=======================
Persistent database engine storing portfolio state, trade logs, AI signals,
and n8n automation logs in a local SQLite database.
"""

import os
import sqlite3
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "database_data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "stockai_trading.db")

class DatabaseManager:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Trades Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT UNIQUE,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    qty INTEGER NOT NULL,
                    price REAL NOT NULL,
                    reason TEXT,
                    status TEXT,
                    timestamp TEXT NOT NULL
                )
            """)

            # Portfolio Positions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    symbol TEXT PRIMARY KEY,
                    qty INTEGER NOT NULL,
                    avg_entry_price REAL NOT NULL,
                    current_price REAL NOT NULL,
                    market_value REAL NOT NULL,
                    unrealized_pl REAL NOT NULL,
                    unrealized_plpc REAL NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # AI Signals History Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    composite_score INTEGER NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reasoning TEXT,
                    current_price REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # n8n Automation Log Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS n8n_automations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)

            conn.commit()
            logger.info("🗄️ SQLite Database initialized successfully.")

    def log_trade(self, symbol: str, action: str, qty: int, price: float, reason: str, status: str = "EXECUTED") -> str:
        trade_id = f"{symbol}_{action}_{int(datetime.now().timestamp())}"
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.cursor().execute("""
                INSERT OR REPLACE INTO trades (trade_id, symbol, action, qty, price, reason, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (trade_id, symbol, action, qty, price, reason, status, now))
            conn.commit()
        return trade_id

    def update_positions(self, positions_list: list):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM positions")
            for pos in positions_list:
                cursor.execute("""
                    INSERT INTO positions (symbol, qty, avg_entry_price, current_price, market_value, unrealized_pl, unrealized_plpc, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pos['symbol'], pos['qty'], pos['avg_entry_price'], pos['current_price'],
                    pos['market_value'], pos['unrealized_pl'], pos['unrealized_plpc'], now
                ))
            conn.commit()

    def log_ai_signal(self, symbol: str, signal: str, composite_score: int, confidence: float, reasoning: str, current_price: float = 0.0):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.cursor().execute("""
                INSERT INTO ai_signals (symbol, composite_score, signal, confidence, reasoning, current_price, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (symbol, composite_score, signal, confidence, reasoning, current_price, now))
            conn.commit()

    def log_n8n_event(self, event_type: str, payload: dict, status: str = "DELIVERED"):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.cursor().execute("""
                INSERT INTO n8n_automations (event_type, payload, status, timestamp)
                VALUES (?, ?, ?, ?)
            """, (event_type, json.dumps(payload), status, now))
            conn.commit()

    def get_recent_trades(self, limit: int = 20) -> list:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_ai_signals(self, limit: int = 10) -> list:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_signals ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_active_positions(self) -> list:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM positions ORDER BY unrealized_pl DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_n8n_logs(self, limit: int = 10) -> list:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM n8n_automations ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
