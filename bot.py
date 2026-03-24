import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from trader import Trader
from ai_strategy import AIStrategy

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))

trader = Trader()
ai = AIStrategy()

def auth(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
            await update.message.reply_text("⛔ Unauthorized access.")
            return
        return await func(update, context)
    return wrapper

@auth
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💼 Portfolio", callback_data="portfolio"),
         InlineKeyboardButton("🤖 AI Analysis", callback_data="ai_analysis")],
        [InlineKeyboardButton("📈 Buy", callback_data="buy_menu"),
         InlineKeyboardButton("📉 Sell", callback_data="sell_menu")],
        [InlineKeyboardButton("🔄 Auto-Trade ON/OFF", callback_data="toggle_auto")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 *Crypto AI Trading Bot*\n\nSelect an action below:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

@auth
async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Fetching portfolio...")
    try:
        report = trader.get_portfolio()
        await update.message.reply_text(report, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

@auth
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = context.args[0].upper() if context.args else "BTCUSDT"
    await update.message.reply_text(f"🧠 Running AI analysis on *{symbol}*...", parse_mode="Markdown")
    try:
        analysis = ai.analyze(symbol)
        await update.message.reply_text(analysis, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

@auth
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/buy <SYMBOL> <USDT_AMOUNT>`\nExample: `/buy BTC 50`", parse_mode="Markdown")
        return
    symbol = context.args[0].upper() + "USDT"
    amount = float(context.args[1])
    await update.message.reply_text(f"⏳ Placing buy order for ${amount} of {symbol}...")
    try:
        result = trader.market_buy(symbol, amount)
        await update.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

@auth
async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/sell <SYMBOL> <QUANTITY>`\nExample: `/sell BTC 0.001`", parse_mode="Markdown")
        return
    symbol = context.args[0].upper() + "USDT"
    quantity = float(context.args[1])
    await update.message.reply_text(f"⏳ Placing sell order for {quantity} {symbol}...")
    try:
        result = trader.market_sell(symbol, quantity)
        await update.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

@auth
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auto = context.bot_data.get("auto_trade", False)
    symbol = context.bot_data.get("auto_symbol", "BTCUSDT")
    await update.message.reply_text(
        f"🤖 *Bot Status*\n\n"
        f"Auto-trade: {'✅ ON' if auto else '❌ OFF'}\n"
        f"Symbol: `{symbol}`",
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "portfolio":
        try:
            report = trader.get_portfolio()
            await query.edit_message_text(report, parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {e}")

    elif data == "ai_analysis":
        await query.edit_message_text("🧠 Analyzing BTC market...")
        try:
            analysis = ai.analyze("BTCUSDT")
            await query.edit_message_text(analysis, parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {e}")

    elif data == "buy_menu":
        await query.edit_message_text(
            "📈 *Buy Crypto*\n\nUse the command:\n`/buy <SYMBOL> <USDT_AMOUNT>`\n\nExample: `/buy BTC 50`",
            parse_mode="Markdown"
        )

    elif data == "sell_menu":
        await query.edit_message_text(
            "📉 *Sell Crypto*\n\nUse the command:\n`/sell <SYMBOL> <QUANTITY>`\n\nExample: `/sell BTC 0.001`",
            parse_mode="Markdown"
        )

    elif data == "toggle_auto":
        current = context.bot_data.get("auto_trade", False)
        context.bot_data["auto_trade"] = not current
        state = "✅ ON" if not current else "❌ OFF"
        await query.edit_message_text(
            f"🔄 Auto-trading is now *{state}*",
            parse_mode="Markdown"
        )

async def auto_trade_job(context: ContextTypes.DEFAULT_TYPE):
    if not context.bot_data.get("auto_trade", False):
        return
    symbol = context.bot_data.get("auto_symbol", "BTCUSDT")
    chat_id = context.job.chat_id
    try:
        signal = ai.get_signal(symbol)
        await context.bot.send_message(chat_id, f"🤖 *Auto-Trade Check — {symbol}*\n\n{signal}", parse_mode="Markdown")
        action = ai.get_action(symbol)
        if action == "BUY":
            result = trader.market_buy(symbol, amount_usdt=20)
            await context.bot.send_message(chat_id, f"📈 *Auto-Buy Executed*\n\n{result}", parse_mode="Markdown")
        elif action == "SELL":
            result = trader.auto_sell(symbol)
            await context.bot.send_message(chat_id, f"📉 *Auto-Sell Executed*\n\n{result}", parse_mode="Markdown")
    except Exception as e:
        await context.bot.send_message(chat_id, f"⚠️ Auto-trade error: {e}")

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN environment variable not set!")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(button_handler))
    job_queue = app.job_queue
    job_queue.run_repeating(
        auto_trade_job,
        interval=3600,
        first=60,
        chat_id=ALLOWED_USER_ID,
        name="auto_trade"
    )
    logger.info("🤖 Bot started. Polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
