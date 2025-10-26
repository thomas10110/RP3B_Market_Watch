from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import database as db
import fetcher
import notifier

app = Flask(__name__)

@app.route('/')
def index():
    """Renders the main page of the application."""
    return render_template('index.html')

@app.route('/api/emails', methods=['GET'])
def get_emails():
    """API endpoint to get all emails."""
    emails = db.get_emails()
    return jsonify(emails)

@app.route('/api/emails', methods=['POST'])
def add_email():
    """API endpoint to add a new email."""
    data = request.get_json()
    email = data.get('email')
    if email:
        try:
            db.add_email(email)
            return jsonify({'message': 'Email added successfully'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Email is required'}), 400

@app.route('/api/emails', methods=['DELETE'])
def delete_email():
    """API endpoint to delete an email."""
    data = request.get_json()
    email = data.get('email')
    if email:
        try:
            db.delete_email(email)
            return jsonify({'message': 'Email deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Email is required'}), 400

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """API endpoint to get the watchlist."""
    watchlist = db.get_watchlist()
    return jsonify([dict(row) for row in watchlist])

@app.route('/api/watchlist', methods=['POST'])
def add_to_watchlist():
    """API endpoint to add a symbol to the watchlist."""
    data = request.get_json()
    symbol = data.get('symbol')
    if symbol:
        if fetcher.validate_symbol(symbol):
            current_price = fetcher.get_price(symbol)
            if current_price is not None:
                try:
                    db.add_to_watchlist(symbol, current_price)
                    return jsonify({'message': f'{symbol} added to watchlist'}), 201
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            else:
                return jsonify({'error': 'Could not fetch price'}), 500
        else:
            return jsonify({'error': 'Invalid symbol'}), 400
    return jsonify({'error': 'Symbol is required'}), 400

@app.route('/api/watchlist', methods=['DELETE'])
def remove_from_watchlist():
    """API endpoint to remove a symbol from the watchlist."""
    data = request.get_json()
    symbol = data.get('symbol')
    if symbol:
        try:
            db.remove_from_watchlist(symbol)
            return jsonify({'message': f'{symbol} removed from watchlist'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Symbol is required'}), 400

@app.route('/api/price_targets', methods=['POST'])
def add_price_target():
    """API endpoint to add a price target."""
    data = request.get_json()
    watchlist_id = data.get('watchlist_id')
    gain_target = data.get('gain_target')
    dip_target = data.get('dip_target')
    if watchlist_id and gain_target and dip_target:
        try:
            db.add_price_target(watchlist_id, gain_target, dip_target)
            return jsonify({'message': 'Price target added successfully'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'All fields are required'}), 400

def check_prices():
    """Checks prices and sends notifications if targets are met."""
    try:
        watchlist = db.get_watchlist()
        emails = db.get_emails()

        for item in watchlist:
            current_price = fetcher.get_price(item['symbol'])
            if current_price is not None:
                db.update_price(item['symbol'], current_price)
                targets = db.get_price_targets(item['id'])
                for target in targets:
                    gain_target_price = item['initial_price'] * (1 + target['gain_target'] / 100)
                    dip_target_price = item['initial_price'] * (1 - target['dip_target'] / 100)

                    if current_price >= gain_target_price:
                        subject = f"Price Alert: {item['symbol']} has reached a new high!"
                        body = f"{item['symbol']} is now at {current_price}, which is above your target of {gain_target_price}."
                        for email in emails:
                            notifier.send_email(email, subject, body)

                    if current_price <= dip_target_price:
                        subject = f"Price Alert: {item['symbol']} has dropped!"
                        body = f"{item['symbol']} is now at {current_price}, which is below your target of {dip_target_price}."
                        for email in emails:
                            notifier.send_email(email, subject, body)
    except Exception as e:
        notifier.send_admin_notification("Error in check_prices", str(e))

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_prices, trigger="interval", seconds=300)
    scheduler.start()
    # Running without debug mode to prevent import issues with the reloader.
    app.run(debug=False, host='0.0.0.0')
