from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from apscheduler.schedulers.background import BackgroundScheduler
import database as db
import fetcher
import notifier
import atexit

app = Flask(__name__)
# Use a secret key for session management (required for SocketIO)
app.config['SECRET_KEY'] = 'secret!'
# Initialize SocketIO, running in a separate thread
socketio = SocketIO(app, async_mode='threading')

# --- Helper Functions ---
def serialize_row(row):
    """Converts a sqlite3.Row object to a dictionary."""
    return dict(row) if row else None

# --- Main Route ---
@app.route('/')
def index():
    """Renders the main page of the application."""
    return render_template('index.html')

# --- API for Emails ---
@app.route('/api/emails', methods=['GET'])
def get_emails_route():
    emails = db.get_emails()
    return jsonify([serialize_row(e) for e in emails])

@app.route('/api/emails', methods=['POST'])
def add_email_route():
    data = request.get_json()
    if not data or not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    try:
        db.add_email(data['email'])
        return jsonify({'message': 'Email added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emails/<int:email_id>', methods=['DELETE'])
def delete_email_route(email_id):
    try:
        db.delete_email(email_id)
        return jsonify({'message': 'Email deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API for Watchlist ---
@app.route('/api/watchlist', methods=['GET'])
def get_watchlist_route():
    try:
        watchlist_items = db.get_watchlist()

        response_data = []
        for item in watchlist_items:
            item_dict = serialize_row(item)
            item_dict['targets'] = [serialize_row(t) for t in db.get_price_targets_for_stock(item['id'])]
            item_dict['subscribed_emails'] = [email_id for email_id in db.get_subscribed_email_ids_for_stock(item['id'])]
            response_data.append(item_dict)

        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watchlist', methods=['POST'])
def add_to_watchlist_route():
    data = request.get_json()
    symbol = data.get('symbol')
    if not symbol:
        return jsonify({'error': 'Symbol is required'}), 400

    validated_symbol = fetcher.validate_symbol(symbol)
    if not validated_symbol:
        return jsonify({'error': f'Symbol "{symbol}" is invalid or not supported'}), 400

    price = fetcher.get_price(validated_symbol)
    if price is None:
        return jsonify({'error': 'Could not fetch price for symbol'}), 500

    try:
        db.add_to_watchlist(validated_symbol, price)
        return jsonify({'message': f'{validated_symbol} added to watchlist'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watchlist/<int:symbol_id>', methods=['DELETE'])
def remove_from_watchlist_route(symbol_id):
    try:
        db.remove_from_watchlist(symbol_id)
        return jsonify({'message': 'Symbol removed from watchlist'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API for Price Targets ---
@app.route('/api/price_targets', methods=['POST'])
def add_price_target_route():
    data = request.get_json()
    watchlist_id = data.get('watchlist_id')
    target_type = data.get('target_type')
    percentage = data.get('percentage')

    if not all([watchlist_id, target_type, percentage]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        new_target = db.add_price_target(watchlist_id, target_type, percentage)
        return jsonify(serialize_row(new_target)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/price_targets/<int:target_id>', methods=['DELETE'])
def delete_price_target_route(target_id):
    try:
        db.delete_price_target(target_id)
        return jsonify({'message': 'Price target deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API for Notification Preferences ---
@app.route('/api/notification_preferences/<int:watchlist_id>', methods=['GET'])
def get_notification_preferences_route(watchlist_id):
    try:
        email_ids = db.get_subscribed_email_ids_for_stock(watchlist_id)
        return jsonify(email_ids)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notification_preferences/<int:watchlist_id>', methods=['PUT'])
def update_notification_preferences_route(watchlist_id):
    data = request.get_json()
    email_ids = data.get('email_ids')
    if email_ids is None:
        return jsonify({'error': 'Missing email_ids list'}), 400

    try:
        db.update_notification_preferences(watchlist_id, email_ids)
        return jsonify({'message': 'Preferences updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API for Historical Data ---
@app.route('/api/history/<symbol>')
def get_historical_data(symbol):
    try:
        # yfinance is great for historical data
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo") # Get 1 month of data
        if hist.empty:
            return jsonify({'error': 'Could not fetch historical data'}), 404

        # Format data for Chart.js
        labels = hist.index.strftime('%Y-%m-%d').tolist()
        data = hist['Close'].tolist()

        return jsonify({'labels': labels, 'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Background Price Checker ---
def check_prices():
    """Background job to check prices, send notifications, and emit updates."""
    with app.app_context():
        print("--- Running background price check ---")
        watchlist = db.get_full_watchlist_details()
        for item in watchlist:
            current_price = fetcher.get_price(item['symbol'])
            if current_price is None:
                continue

            db.update_price(item['id'], current_price)

            # Emit price update to all clients
            socketio.emit('price_update', {
                'id': item['id'],
                'last_price': current_price,
                'last_updated': datetime.now().isoformat()
            })

            targets = db.get_price_targets_for_stock(item['id'])
            for target in targets:
                initial_price = item['initial_price']

                if target['target_type'] == 'gain':
                    target_price = initial_price * (1 + target['percentage'] / 100)
                    if current_price >= target_price:
                        emails_to_notify = db.get_subscribed_emails_for_stock(item['id'])
                        subject = f"Price Gain Alert: {item['symbol']}"
                        body = f"{item['symbol']} has reached a price of {current_price:.2f}, exceeding your {target['percentage']}% gain target."
                        for email in emails_to_notify:
                            notifier.send_email(email['email'], subject, body)
                        db.delete_price_target(target['id'])

                elif target['target_type'] == 'dip':
                    target_price = initial_price * (1 - target['percentage'] / 100)
                    if current_price <= target_price:
                        emails_to_notify = db.get_subscribed_emails_for_stock(item['id'])
                        subject = f"Price Dip Alert: {item['symbol']}"
                        body = f"{item['symbol']} has dropped to a price of {current_price:.2f}, exceeding your {target['percentage']}% dip target."
                        for email in emails_to_notify:
                            notifier.send_email(email['email'], subject, body)
                        db.delete_price_target(target['id'])

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_prices, trigger="interval", seconds=300)
    scheduler.start()
    # Ensure scheduler is shutdown correctly
    atexit.register(lambda: scheduler.shutdown())
    # Run with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000)
