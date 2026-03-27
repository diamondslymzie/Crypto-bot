import sqlite3
from datetime import datetime

DB_NAME = "liquid.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Users Table: Stores API keys and Profile info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            bitget_key TEXT,
            bitget_secret TEXT,
            bitget_passphrase TEXT,
            risk_level TEXT DEFAULT 'Medium',
            join_date TEXT,
            notifications_on INTEGER DEFAULT 1
        )
    ''')

    # 2. Trades Table: Stores every Buy/Sell for P&L tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            symbol TEXT,
            side TEXT, -- 'Long' or 'Short'
            entry_price REAL,
            exit_price REAL,
            amount REAL,
            pnl REAL,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')

    # 3. Bets Table: For the Prediction Market (Polymarket style)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bets (
            bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            market_name TEXT,
            selection TEXT, -- 'YES' or 'NO'
            amount REAL,
            odds REAL,
            status TEXT DEFAULT 'Open', -- 'Open', 'Won', 'Lost'
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully.")

# Run this once to create the file
if __name__ == "__main__":
    init_db()
