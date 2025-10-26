import os

# --- API Keys ---
# It's highly recommended to use environment variables for sensitive data
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY', 'your_finnhub_api_key')
MARKETSTACK_API_KEY = os.environ.get('MARKETSTACK_API_KEY', 'your_marketstack_api_key')

# --- Email Settings ---
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.example.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'your_email@example.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'your_email_password')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'your_email@example.com')

# --- Admin Notification ---
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
