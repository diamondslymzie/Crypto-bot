import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import ccxt

# --- 1. CONFIGURATION ---
PORT = int(os.environ.get("PORT", 8080))
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Bitget API credentials pulled securely from Railway Variables
BG_API_KEY = os.environ.get("BITGET_API_KEY")
BG_SECRET = os.environ.get("BITGET_SECRET_KEY")
BG_PASSPHRASE = os.environ.get("BITGET_PASSPHRASE")

if not BOT_TOKEN:
    raise ValueError("ERROR: TELEGRAM_BOT_TOKEN environment variable is missing!")

# --- 2. BITGET TRADING LOGIC ---
def get_bitget_client():
    """Initializes the Bitget connection using CCXT."""
    if not all([BG_API_KEY, BG_SECRET, BG_PASSPHRASE]):
        print("⚠️ Warning: Bitget API keys are missing in Railway variables!")
        return None
        
    return ccxt.bitget({
        'apiKey': BG_API_KEY,
        'secret': BG_SECRET,
        'password': BG_PASSPHRASE,
        'enableRateLimit': True,
    })

async def execute_bitget_trade(action, amount, price):
    """Executes a live market or limit order on Bitget."""
    exchange = get_bitget_client()
    if not exchange:
        return "Failed: Bitget API keys are not configured in Railway."

    symbol = 'BTC/USDT'
    
    try:
        # We use a standard market order for instant execution from the button
        print(f"🔄 Sending {action.upper()} order to Bitget for {amount} BTC...")
        
        # CCXT requires operations to be synchronous or wrapped properly
        # We run it in an executor so it doesn't freeze the bot
        loop = asyncio.get_event_loop()
        
        if action.lower() == 'buy':
            order = await loop.run_in_executor(
                None, 
                lambda: exchange.create_market_buy_order(symbol, float(amount))
            )
        elif action.lower() == 'sell':
            order = await loop.run_in_executor(
                None, 
                lambda: exchange.create_market_sell_order(symbol, float(amount))
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
    """Answers the /start command in chat."""
    await update.message.reply_text("⚡ Liquid Leverage Bot is active and listening!")

# --- 4. WEB APP LOGIC (Catches your Mini App Button) ---
async def handle_webview_trade(request):
    """Catches the link click from your index.html 'Buy BTC' button."""
    try:
        action = request.query.get('action', 'buy')
        amount = request.query.get('amount', '0.01')
        price = request.query.get('price', '64250.00')
        
        print(f"📥 [WEBHOOK] Received signal: {action.upper()} {amount} BTC")

        # 🎯 Trigger the Bitget trade live!
        trade_result = await execute_bitget_trade(action, amount, price)

        # Return the actual success/failure message from Bitget to your screen!
        return web.Response(
            text=f"Trade Status: {trade_result}\n\nProcessed: {action.upper()} {amount} BTC at approx market price.", 
            status=200
        )
        
    except Exception as e:
        print(f"❌ Error handling web trade: {e}")
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
