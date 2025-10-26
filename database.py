import sqlite3
import os

DATABASE_PATH = 'market_watch.db'

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Creates the necessary tables in the database if they don't exist."""
    conn = get_db_connection()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY,
            symbol TEXT UNIQUE NOT NULL,
            initial_price REAL,
            last_price REAL,
            last_updated TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS price_targets (
            id INTEGER PRIMARY KEY,
            watchlist_id INTEGER,
            gain_target REAL,
            dip_target REAL,
            FOREIGN KEY (watchlist_id) REFERENCES watchlist (id)
        )
    ''')

    conn.commit()
    conn.close()

def add_email(email):
    """Adds a new email to the database."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO emails (email) VALUES (?)', (email,))
    conn.commit()
    conn.close()

def delete_email(email):
    """Deletes an email from the database."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM emails WHERE email = ?', (email,))
    conn.commit()
    conn.close()

def get_emails():
    """Retrieves all emails from the database."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT email FROM emails')
    emails = [row['email'] for row in c.fetchall()]
    conn.close()
    return emails

def add_to_watchlist(symbol, last_price):
    """Adds a new symbol to the watchlist."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO watchlist (symbol, initial_price, last_price, last_updated) VALUES (?, ?, ?, datetime("now"))', (symbol, last_price, last_price))
    conn.commit()
    conn.close()

def remove_from_watchlist(symbol):
    """Removes a symbol from the watchlist."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM watchlist WHERE symbol = ?', (symbol,))
    conn.commit()
    conn.close()

def get_watchlist():
    """Retrieves all items from the watchlist."""
    conn = get_db_connection()
    watchlist = conn.execute('SELECT * FROM watchlist').fetchall()
    conn.close()
    return watchlist

def update_price(symbol, last_price):
    """Updates the last price of a symbol in the watchlist."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE watchlist SET last_price = ?, last_updated = datetime("now") WHERE symbol = ?', (last_price, symbol))
    conn.commit()
    conn.close()

def add_price_target(watchlist_id, gain_target, dip_target):
    """Adds a price target for a watchlist item."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO price_targets (watchlist_id, gain_target, dip_target) VALUES (?, ?, ?)', (watchlist_id, gain_target, dip_target))
    conn.commit()
    conn.close()

def get_price_targets(watchlist_id):
    """Retrieves all price targets for a watchlist item."""
    conn = get_db_connection()
    targets = conn.execute('SELECT * FROM price_targets WHERE watchlist_id = ?', (watchlist_id,)).fetchall()
    conn.close()
    return targets

def get_all_price_targets():
    """Retrieves all price targets."""
    conn = get_db_connection()
    targets = conn.execute('SELECT w.symbol, pt.gain_target, pt.dip_target FROM watchlist w JOIN price_targets pt ON w.id = pt.watchlist_id').fetchall()
    conn.close()
    return targets

# Initialize the database and tables when the module is first imported
if not os.path.exists(DATABASE_PATH):
    create_tables()
