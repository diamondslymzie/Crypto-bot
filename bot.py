import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
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

SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT",
    "BNB/USDT", "ADA/USDT", "DOGE/USDT", "TRX/USDT",
    "AVAX/USDT", "MATIC/USDT", "LTC/USDT", "DOT/USDT"
]

AUTO_TRADE_AMOUNT = 5

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
    symbol = context.args[0].upper() + "/USDT" if context.args else "BTC/USDT"
    await update.message.reply_text(f"🧠 Running AI analysis on *{symbol}*...", parse_mode="Markdown")
    try:
        analysis = ai.analyze(symbol)
        await update.message.reply_text(analysis, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

@auth
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/buy <SYMBOL> <USDT_AMOUNT>`\nExample: `/buy BTC 5`", parse_mode="Markdown")
        return
    symbol = context.args[0].upper() + "/USDT"
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
    symbol = context.args[0].upper() + "/USDT"
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
    await update.message.reply_text(
        f"🤖 *Bot Status*\n\n"
        f"Auto-trade: {'✅ ON' if auto else '❌ OFF'}\n"
        f"Amount per trade: ${AUTO_TRADE_AMOUNT}\n"
        f"Tracking: {len(SYMBOLS)} coins",
        parse_mode="Markdown"
    )

@auth
async def set_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADE_AMOUNT
    if not context.args:
        await update.message.reply_text(
            f"💵 Current auto-trade amount: *${AUTO_TRADE_AMOUNT}*\n\n"
            f"To change it use:\n`/setamount 10`",
            parse_mode="Markdown"
        )
        return
    try:
        new_amount = float(context.args[0])
        if new_amount < 1:
            await update.message.reply_text("⚠️ Minimum amount is $1")
            return
        AUTO_TRADE_AMOUNT = new_amount
        await update.message.reply_text(
            f"✅ Auto-trade amount updated to *${AUTO_TRADE_AMOUNT}*",
            parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid number\nExample: `/setamount 10`", parse_mode="Markdown")

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
        await query.edit_message_text("🧠 Analyzing BTC/USDT market...")
        try:
            analysis = ai.analyze("BTC/USDT")
            await query.edit_message_text(analysis, parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {e}")

    elif data == "buy_menu":
        await query.edit_message_text(
            "📈 *Buy Crypto*\n\nUse the command:\n`/buy <SYMBOL> <USDT_AMOUNT>`\n\nExample: `/buy BTC 5`",
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
            f"🔄 Auto-trading is now *{state}*\n\n"
            f"Tracking {len(SYMBOLS)} coins\n"
            f"Amount per trade: ${AUTO_TRADE_AMOUNT}\n"
            f"Checks every 60 minutes",
            parse_mode="Markdown"
        )

async def auto_trade_job(context: ContextTypes.DEFAULT_TYPE):
    if not context.bot_data.get("auto_trade", False):
        return

    chat_id = context.job.chat_id
    await context.bot.send_message(chat_id, "🔍 *Auto-Trade Scan Starting...*\nChecking all coins...", parse_mode="Markdown")

    for symbol in SYMBOLS:
        try:
            action = ai.get_action(symbol)
            signal = ai.get_signal(symbol)
            if action == "BUY":
                result = trader.market_buy(symbol, amount_usdt=AUTO_TRADE_AMOUNT)
                await context.bot.send_message(
                    chat_id,
                    f"📈 *Auto-Buy — {symbol}*\n\n{signal}\n\n{result}",
                    parse_mode="Markdown"
                )
            elif action == "SELL":
                result = trader.auto_sell(symbol)
                await context.bot.send_message(
                    chat_id,
                    f"📉 *Auto-Sell — {symbol}*\n\n{signal}\n\n{result}",
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Auto-trade error for {symbol}: {e}")

    await context.bot.send_message(chat_id, "✅ *Scan Complete!* Next check in 60 minutes.", parse_mode="Markdown")

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
    app.add_handler(CommandHandler("setamount", set_amount))
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
