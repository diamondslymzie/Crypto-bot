import os
import threading
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from trader import Trader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
trader = Trader()

@app.route('/portfolio')
def portfolio():
    try:
        balance = trader.exchange.fetch_balance()
        assets = []
        total_usdt = 0.0
        for asset, data in balance['total'].items():
            if data > 0:
                usdt_value = 0.0
                price = 0.0
                change = 0.0
                if asset == 'USDT':
                    usdt_value = data
                    price = 1.0
                else:
                    try:
                        ticker = trader.exchange.fetch_ticker(f"{asset}/USDT")
                        price = ticker['last']
                        usdt_value = data * price
                        change = ticker.get('percentage', 0) or 0
                    except Exception:
                        pass
                if usdt_value > 0.01:
                    total_usdt += usdt_value
                    assets.append({
                        'asset': asset,
                        'quantity': data,
                        'price': price,
                        'usdt_value': round(usdt_value, 2),
                        'change_24h': round(change, 2)
                    })
        return jsonify({
            'success': True,
            'total_usdt': round(total_usdt, 2),
            'assets': assets
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/price/<symbol>')
def price(symbol):
    try:
        ticker = trader.exchange.fetch_ticker(f"{symbol}/USDT")
        return jsonify({
            'success': True,
            'symbol': symbol,
            'price': ticker['last'],
            'change_24h': ticker.get('percentage', 0) or 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'online', 'bot': 'Liquid Leverage'})

def run_bot():
    try:
        import asyncio
        from bot import main
        logger.info("Starting Telegram bot...")
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting API on port {port}")
    app.run(host='0.0.0.0', port=port)
