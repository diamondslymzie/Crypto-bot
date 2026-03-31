import os
import json
from http.server import BaseHTTPRequestHandler
import ccxt

class handler(BaseHTTPRequestHandler):
    def handle_request(self):
        # 1. Pull keys securely from Vercel environment variables
        api_key = os.environ.get("BITGET_API_KEY")
        secret = os.environ.get("BITGET_SECRET_KEY")
        passphrase = os.environ.get("BITGET_PASSPHRASE")

        # 2. Setup Bitget via CCXT
        exchange = ccxt.bitget({
            'apiKey': api_key,
            'secret': secret,
            'password': passphrase,
            'enableRateLimit': True,
        })

        try:
            # 3. Trigger a $1 USDT Market Buy Order
            # Forcing Bitget to accept quote currency amount (USDT)
            symbol = 'BTC/USDT'
            usdt_to_spend = 1.0
            
            order = exchange.create_order(
                symbol, 'market', 'buy', None, None, {'quoteOrderQty': usdt_to_spend}
            )
            
            message = f"Success! Bitget Order ID: {order['id']}"
            status_code = 200

        except Exception as e:
            message = f"Failed to place Bitget trade: {str(e)}"
            status_code = 500

        # 4. Send the response back to your Telegram Mini App
        self.send_response(status_code)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        self.wfile.write(message.encode('utf-8'))
        return

    # 🛠️ THIS FIXES THE 405 ERROR!
    # No matter if the app sends a GET or a POST, we handle it the same way.
    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()
