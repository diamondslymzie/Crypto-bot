import os
import json
import ccxt

def handler(request):
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

    # 4. Return the clean response to Vercel
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'text/plain',
            'Access-Control-Allow-Origin': '*' 
        },
        'body': message
    }
