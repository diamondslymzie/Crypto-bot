import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import ccxt

# --- 1. CONFIGURATION ---
PORT = int(os.environ.get("PORT", 8080))
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

BG_API_KEY = os.environ.get("BITGET_API_KEY")
BG_SECRET = os.environ.get("BITGET_SECRET_KEY")
BG_PASSPHRASE = os.environ.get("BITGET_PASSPHRASE")

if not BOT_TOKEN:
    raise ValueError("ERROR: TELEGRAM_BOT_TOKEN environment variable is missing!")

# --- 2. BITGET TRADING LOGIC ---
def get_bitget_client():
    if not all([BG_API_KEY, BG_SECRET, BG_PASSPHRASE]):
        print("⚠️ Warning: Bitget API keys are missing in Railway variables!")
        return None
        
    return ccxt.bitget({
        'apiKey': BG_API_KEY,
        'secret': BG_SECRET,
        'password': BG_PASSPHRASE,
        'enableRateLimit': True,
    })

async def execute_bitget_trade(action):
    """Executes a simple $10 USDT market buy to avoid size calculation errors."""
    exchange = get_bitget_client()
    if not exchange:
        return "Failed: API keys are not configured."

    symbol = 'BTC/USDT'
    
    try:
        loop = asyncio.get_event_loop()
        
        if action.lower() == 'buy':
            # 🚀 Hardcoded to spend exactly 10 USDT to safely clear Bitget's $5 minimum limit.
            usdt_to_spend = 10.0 
            print(f"🔄 Firing market buy for ${usdt_to_spend} USDT...")
            
            # Using custom params to force Bitget to accept quote currency amount (USDT)
            order = await loop.run_in_executor(
                None, 
                lambda: exchange.create_order(
                    symbol, 'market', 'buy', None, None, {'quoteOrderQty': usdt_to_spend}
                )
            )
            
        elif action.lower() == 'sell':
            # For testing sells, we'll try to sell a tiny fraction (0.0002 BTC is about $12)
            btc_to_sell = 0.0002
            print(f"🔄 Firing market sell for {btc_to_sell} BTC...")
            
            order = await loop.run_in_executor(
                None, 
                lambda: exchange.create_market_sell_order(symbol, btc_to_sell)
            )
        else:
            return f"Failed: Invalid action '{action}'"

        print(f"✅ Bitget Order Success! ID: {order['id']}")
        return f"Success! Bitget Order ID: {order['id']}"

    except Exception as e:
        print(f"❌ Bitget API Error: {e}")
        return f"Failed: {str(e)}"

# --- 3. TELEGRAM BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚡ Liquid Leverage Bot is active and listening!")

# --- 4. WEB APP LOGIC ---
async def handle_webview_trade(request):
    try:
        action = request.query.get('action', 'buy')
        print(f"📥 [WEBHOOK] Received signal to {action.upper()}")

        # Trigger the trade!
        trade_result = await execute_bitget_trade(action)

        return web.Response(
            text=f"Trade Status: {trade_result}", 
            status=200
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return web.Response(text=f"Internal Server Error: {str(e)}", status=500)

# --- 5. MAIN RUNNER ---
async def main():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    
    web_app = web.Application()
    web_app.router.add_get('/api/trade', handle_webview_trade)
    
    await bot_app.initialize()
    await bot_app.start()
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    print(f"🟢 Web server listening on port {PORT}")
    
    try:
        await bot_app.updater.start_polling()
        while True:
            await asyncio.sleep(3600)
            
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down...")
    finally:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
        await runner.cleanup()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
