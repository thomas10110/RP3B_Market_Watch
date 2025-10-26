from app import app, socketio

if __name__ == "__main__":
    # Use eventlet or gevent for production WebSocket server
    # Example: gunicorn --worker-class eventlet -w 1 wsgi:app
    socketio.run(app, host='0.0.0.0', port=5000)
