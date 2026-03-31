import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 1. CONFIGURATION ---
# Railway automatically assigns a PORT. If it can't find one, it defaults to 8080.
PORT = int(os.environ.get("PORT", 8080))
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") # Make sure this is in your Railway Variables!

if not BOT_TOKEN:
    raise ValueError("ERROR: TELEGRAM_BOT_TOKEN environment variable is missing!")

# --- 2. TELEGRAM BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers the /start command in chat."""
    await update.message.reply_text("⚡ Liquid Leverage Bot is active and listening!")

# --- 3. WEB APP LOGIC (For your Mini App Buttons) ---
async def handle_webview_trade(request):
    """Catches the link click from your index.html 'Buy BTC' button."""
    try:
        # Extract variables from the URL (?action=buy&amount=0.01&price=64250.00)
        action = request.query.get('action', 'N/A')
        amount = request.query.get('amount', 'N/A')
        price = request.query.get('price', 'N/A')
        
        print(f"📥 [WEBHOOK] Received trade execution signal!")
        print(f"   👉 Action: {action.upper()} | Amount: {amount} | Price: {price}")

        # 🎯 THIS IS WHERE YOUR BITGET CODE GOES!
        # You would call your Bitget order function here.
        # Example: await execute_bitget_trade(action, amount, price)

        # Send a success response back to the browser/phone
        return web.Response(
            text=f"Trade triggered successfully! {action.upper()} {amount} BTC at {price}", 
            status=200
        )
        
    except Exception as e:
        print(f"❌ Error handling web trade: {e}")
        return web.Response(text="Internal Server Error", status=500)

# --- 4. MAIN RUNNER (Combines Bot and Web Server) ---
async def main():
    # Setup the Telegram Bot Application
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    
    # Setup the Web Server
    web_app = web.Application()
    web_app.router.add_get('/api/trade', handle_webview_trade)
    
    # Initialize the bot (but don't start polling yet)
    await bot_app.initialize()
    await bot_app.start()
    
    # Start Web Server on the Railway Port
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    print(f"🟢 Web server listening on port {PORT}")
    print("🟢 Telegram bot background tasks started")

    # This keeps the script running forever handling both tasks
    try:
        # Run Telegram's update listener in the background
        # (We use continuous polling here so you don't have to register SSL certificates manually)
        await bot_app.updater.start_polling()
        
        while True:
            await asyncio.sleep(3600) # Keep the loop alive
            
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down...")
    finally:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
        await runner.cleanup()

if __name__ == '__main__':
    # Fixes occasional "Event loop is closed" errors on restart
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
