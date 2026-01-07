import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_file="trading_bot.db"):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_file)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Settings & Balance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Initialize default balance if not exists
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('balance', '10.0')")
        
        # Scanned Tokens (Feed)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scanned_tokens (
                address TEXT PRIMARY KEY,
                symbol TEXT,
                icon TEXT,
                liquidity REAL,
                score INTEGER,
                strength TEXT,
                scanned_at TIMESTAMP
            )
        ''')
        
        # Active Positions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                address TEXT PRIMARY KEY,
                symbol TEXT,
                avg_entry_price REAL,
                quantity REAL,
                current_price REAL,
                pnl REAL,
                pnl_pct REAL,
                entry_time TIMESTAMP
            )
        ''')
        
        # Trade History
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                address TEXT,
                entry_price REAL,
                exit_price REAL,
                quantity REAL,
                pnl REAL,
                pnl_pct REAL,
                reason TEXT,
                entry_time TIMESTAMP,
                exit_time TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    # --- Balance Methods ---
    def get_balance(self):
        conn = self.get_connection()
        val = conn.execute("SELECT value FROM settings WHERE key='balance'").fetchone()
        conn.close()
        return float(val[0]) if val else 0.0

    def update_balance(self, amount):
        """Adds (or subtracts) amount from current balance."""
        current = self.get_balance()
        new_bal = current + amount
        conn = self.get_connection()
        conn.execute("UPDATE settings SET value=? WHERE key='balance'", (str(new_bal),))
        conn.commit()
        conn.close()
        return new_bal

    # --- Position Methods ---
    def add_position(self, pos_data):
        conn = self.get_connection()
        conn.execute('''
            INSERT INTO positions (address, symbol, avg_entry_price, quantity, current_price, pnl, pnl_pct, entry_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pos_data['address'], pos_data['symbol'], pos_data['entry_price'], 
            pos_data['amount'], pos_data['current_price'], 0.0, 0.0, pos_data['entry_time']
        ))
        conn.commit()
        conn.close()

    def get_positions(self):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM positions").fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def remove_position(self, address):
        conn = self.get_connection()
        conn.execute("DELETE FROM positions WHERE address=?", (address,))
        conn.commit()
        conn.close()
        
    def update_position_stats(self, address, current_price, pnl, pnl_pct):
        conn = self.get_connection()
        conn.execute('''
            UPDATE positions 
            SET current_price=?, pnl=?, pnl_pct=?
            WHERE address=?
        ''', (current_price, pnl, pnl_pct, address))
        conn.commit()
        conn.close()

    # --- History Methods ---
    def add_trade_history(self, trade_data):
        conn = self.get_connection()
        conn.execute('''
            INSERT INTO trades (symbol, address, entry_price, exit_price, quantity, pnl, pnl_pct, reason, entry_time, exit_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data['symbol'], trade_data['address'], trade_data['entry_price'],
            trade_data['exit_price'], trade_data['amount'], trade_data['pnl'],
            trade_data['pnl_pct'], trade_data['reason'], trade_data['entry_time'], trade_data['exit_time']
        ))
        conn.commit()
        conn.close()

    def get_history(self):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM trades ORDER BY exit_time DESC LIMIT 50").fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # --- Scan Feed Methods ---
    def log_scan(self, token_data):
        # We only keep the latest scan for an address to avoid duplicates in feed, 
        # or we could insert all. For a feed, 'INSERT OR REPLACE' acts like an update.
        conn = self.get_connection()
        conn.execute('''
            INSERT OR REPLACE INTO scanned_tokens (address, symbol, icon, liquidity, score, strength, scanned_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            token_data['address'], token_data['symbol'], token_data['icon'],
            token_data['liquidity'], token_data['score'], token_data['strength'],
            token_data['time']
        ))
        conn.commit()
        conn.close()

    def get_recent_scans(self, limit=20):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM scanned_tokens ORDER BY scanned_at DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        # Convert to list of dicts matching the UI expectation (which expects 'time' key, handled in app or here)
        result = []
        for row in rows:
            d = dict(row)
            d['time'] = d['scanned_at'] # alias for UI
            result.append(d)
        return result
