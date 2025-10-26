import finnhub
import requests
import yfinance as yf
import config

# Initialize Finnhub client
finnhub_client = finnhub.Client(api_key=config.FINNHUB_API_KEY)

def get_price_finnhub(symbol):
    """Gets the current price of a symbol from Finnhub."""
    try:
        quote = finnhub_client.quote(symbol)
        return quote['c']
    except Exception as e:
        print(f"Error fetching from Finnhub: {e}")
        return None

def get_price_marketstack(symbol):
    """Gets the current price of a symbol from Marketstack."""
    params = {
        'access_key': config.MARKETSTACK_API_KEY,
        'symbols': symbol
    }
    try:
        response = requests.get('http://api.marketstack.com/v1/eod/latest', params=params)
        data = response.json()
        if 'data' in data and data['data']:
            return data['data'][0]['close']
        return None
    except Exception as e:
        print(f"Error fetching from Marketstack: {e}")
        return None

def get_price(symbol):
    """Gets the current price, trying Finnhub first and then Marketstack."""
    price = get_price_finnhub(symbol)
    if price is None:
        price = get_price_marketstack(symbol)
    return price

def validate_symbol(symbol):
    """Validates if a ticker symbol is valid using yfinance."""
    ticker = yf.Ticker(symbol)
    try:
        # A more reliable check is to see if info contains a market price
        return 'regularMarketPrice' in ticker.info or 'currentPrice' in ticker.info
    except Exception:
        return False
