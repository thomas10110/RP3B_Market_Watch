import finnhub
import requests
import yfinance as yf
from config import FINNHUB_API_KEY, MARKETSTACK_API_KEY

# Initialize Finnhub client
finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

def _get_price_finnhub(symbol):
    """Internal function to get price from Finnhub."""
    try:
        # Finnhub is best for crypto, try crypto exchanges first
        if '-' in symbol:
             # Try common crypto exchanges like Binance
            for exchange in ["BINANCE", "COINBASE"]:
                try:
                    price = finnhub_client.crypto_candles(symbol.replace('-', ''), 'D', _from=0, to=9999999999, exchange=exchange)['c'][0]
                    if price: return price
                except Exception:
                    continue

        # Standard quote for stocks/ETFs
        quote = finnhub_client.quote(symbol)
        if quote.get('c'):
            return quote['c']
        return None
    except Exception:
        return None

def _get_price_marketstack(symbol):
    """Internal function to get price from Marketstack."""
    try:
        params = {'access_key': MARKETSTACK_API_KEY, 'symbols': symbol, 'limit': 1}
        response = requests.get('http://api.marketstack.com/v1/eod', params=params)
        data = response.json()
        if data.get('data') and len(data['data']) > 0:
            return data['data'][0]['close']
        return None
    except Exception:
        return None

def _validate_with_yfinance(symbol_variations):
    """Uses yfinance to see if any symbol variation is valid."""
    for symbol in symbol_variations:
        try:
            ticker = yf.Ticker(symbol)
            # Check for a valid price attribute
            if ticker.info.get('regularMarketPrice') or ticker.info.get('currentPrice'):
                return symbol  # Return the valid symbol
        except Exception:
            continue
    return None

def get_price(symbol):
    """
    Gets the current price for a stock, ETF, or crypto by trying multiple APIs and formats.
    """
    symbol = symbol.upper()

    # --- Symbol Variations to try ---
    variations = [
        symbol,
        f"{symbol}.DE",  # For German ETFs like IS3S
        f"{symbol}-USD", # For crypto like BTC-USD
    ]

    # Try getting a price with each variation
    for s in variations:
        # Prioritize Finnhub for crypto
        if '-' in s:
            price = _get_price_finnhub(s)
            if price: return price

        # Try Marketstack first for others (good for ETFs)
        price = _get_price_marketstack(s)
        if price: return price

        # Fallback to Finnhub for stocks
        price = _get_price_finnhub(s)
        if price: return price

    return None

def validate_symbol(symbol):
    """
    Validates a symbol by checking if a price can be fetched from any source.
    Returns the valid symbol format if found, otherwise None.
    """
    symbol = symbol.upper()

    variations = [
        symbol,
        f"{symbol}.DE",
        f"{symbol}-USD",
    ]

    # First, try to get a price directly, as it's the most reliable validation
    if get_price(symbol) is not None:
        # Find which variation worked, if any.
        for s in variations:
             if _get_price_marketstack(s) or _get_price_finnhub(s):
                 return s # Return the format that worked
        return symbol # Fallback to the original

    # If APIs fail, fallback to yfinance for a final check
    valid_format = _validate_with_yfinance(variations)
    if valid_format:
        return valid_format

    return None
