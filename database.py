import sqlite3
import os

DATABASE_PATH = 'market_watch.db'

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Creates the necessary tables in the database if they don't exist."""
    conn = get_db_connection()
    c = conn.cursor()

    # Emails table remains the same
    c.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL
        )
    ''')

    # Watchlist table remains the same
    c.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY,
            symbol TEXT UNIQUE NOT NULL,
            initial_price REAL,
            last_price REAL,
            last_updated TEXT
        )
    ''')

    # Redesigned price_targets table for multiple targets
    c.execute('''
        CREATE TABLE IF NOT EXISTS price_targets (
            id INTEGER PRIMARY KEY,
            watchlist_id INTEGER NOT NULL,
            target_type TEXT NOT NULL, -- 'gain' or 'dip'
            percentage REAL NOT NULL,
            FOREIGN KEY (watchlist_id) REFERENCES watchlist (id) ON DELETE CASCADE
        )
    ''')

    # New table for many-to-many relationship between watchlist and emails
    c.execute('''
        CREATE TABLE IF NOT EXISTS notification_preferences (
            watchlist_id INTEGER NOT NULL,
            email_id INTEGER NOT NULL,
            PRIMARY KEY (watchlist_id, email_id),
            FOREIGN KEY (watchlist_id) REFERENCES watchlist (id) ON DELETE CASCADE,
            FOREIGN KEY (email_id) REFERENCES emails (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

# --- CRUD for Emails ---
def add_email(email):
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO emails (email) VALUES (?)', (email,))
        conn.commit()
    finally:
        conn.close()

def delete_email(email_id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM emails WHERE id = ?', (email_id,))
        conn.commit()
    finally:
        conn.close()

def get_emails():
    conn = get_db_connection()
    try:
        return conn.execute('SELECT id, email FROM emails ORDER BY email').fetchall()
    finally:
        conn.close()

# --- CRUD for Watchlist ---
def add_to_watchlist(symbol, price):
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO watchlist (symbol, initial_price, last_price, last_updated) VALUES (?, ?, ?, datetime("now"))',
            (symbol, price, price)
        )
        conn.commit()
    finally:
        conn.close()

def remove_from_watchlist(symbol_id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM watchlist WHERE id = ?', (symbol_id,))
        conn.commit()
    finally:
        conn.close()

def get_watchlist():
    conn = get_db_connection()
    try:
        return conn.execute('SELECT id, symbol, initial_price, last_price, last_updated FROM watchlist ORDER BY symbol').fetchall()
    finally:
        conn.close()

def update_price(symbol_id, last_price):
    conn = get_db_connection()
    try:
        conn.execute(
            'UPDATE watchlist SET last_price = ?, last_updated = datetime("now") WHERE id = ?',
            (last_price, symbol_id)
        )
        conn.commit()
    finally:
        conn.close()

# --- CRUD for Price Targets ---
def add_price_target(watchlist_id, target_type, percentage):
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO price_targets (watchlist_id, target_type, percentage) VALUES (?, ?, ?)',
            (watchlist_id, target_type, percentage)
        )
        conn.commit()
        # Return the newly created target
        return conn.execute('SELECT * FROM price_targets WHERE id = last_insert_rowid()').fetchone()
    finally:
        conn.close()

def delete_price_target(target_id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM price_targets WHERE id = ?', (target_id,))
        conn.commit()
    finally:
        conn.close()

def get_price_targets_for_stock(watchlist_id):
    conn = get_db_connection()
    try:
        return conn.execute('SELECT id, target_type, percentage FROM price_targets WHERE watchlist_id = ?', (watchlist_id,)).fetchall()
    finally:
        conn.close()

# --- CRUD for Notification Preferences ---
def update_notification_preferences(watchlist_id, email_ids):
    conn = get_db_connection()
    try:
        # Start a transaction
        with conn:
            # Delete old preferences for this stock
            conn.execute('DELETE FROM notification_preferences WHERE watchlist_id = ?', (watchlist_id,))
            # Insert new ones
            if email_ids:
                for email_id in email_ids:
                    conn.execute(
                        'INSERT INTO notification_preferences (watchlist_id, email_id) VALUES (?, ?)',
                        (watchlist_id, email_id)
                    )
    finally:
        conn.close()

def get_subscribed_email_ids_for_stock(watchlist_id):
    conn = get_db_connection()
    try:
        rows = conn.execute('SELECT email_id FROM notification_preferences WHERE watchlist_id = ?', (watchlist_id,)).fetchall()
        return [row['email_id'] for row in rows]
    finally:
        conn.close()

def get_subscribed_emails_for_stock(watchlist_id):
    conn = get_db_connection()
    try:
        return conn.execute("""
            SELECT e.email FROM emails e
            JOIN notification_preferences np ON e.id = np.email_id
            WHERE np.watchlist_id = ?
        """, (watchlist_id,)).fetchall()
    finally:
        conn.close()

# --- Complex Queries for Notification Worker ---
def get_full_watchlist_details():
    conn = get_db_connection()
    try:
        return conn.execute('SELECT id, symbol, initial_price FROM watchlist').fetchall()
    finally:
        conn.close()

# Initialize the database and tables
create_tables()
