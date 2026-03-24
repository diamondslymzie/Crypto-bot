import os
import logging
from datetime import datetime
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
PRICE_ALERTS = {}  # {symbol: target_price}
TRADE_LOG = []     # list of all trades for P&L summary

BOT_NAME = "⚡ LEVERAGE LIQUID"
DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━"

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


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💼 Portfolio", callback_data="portfolio"),
         InlineKeyboardButton("🤖 AI Analysis", callback_data="ai_analysis")],
        [InlineKeyboardButton("📈 Buy", callback_data="buy_menu"),
         InlineKeyboardButton("📉 Sell", callback_data="sell_menu")],
        [InlineKeyboardButton("🔔 Price Alerts", callback_data="alerts_menu"),
         InlineKeyboardButton("📊 P&L Summary", callback_data="pnl_summary")],
        [InlineKeyboardButton("🔄 Auto-Trade ON/OFF", callback_data="toggle_auto"),
         InlineKeyboardButton("❓ Help", callback_data="help")],
    ])


@auth
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "Trader"
    welcome = (
        f"{BOT_NAME}\n"
        f"{DIVIDER}\n\n"
        f"Welcome back, *{name}*.\n\n"
        f"Your AI-powered crypto trading assistant is online and ready.\n\n"
        f"📡 Tracking *{len(SYMBOLS)} coins* in real-time\n"
        f"🧠 Powered by *Claude AI*\n"
        f"⚙️ Exchange: *Bitget*\n\n"
        f"{DIVIDER}\n"
        f"Select an option below to get started:"
    )
    await update.message.reply_text(
        welcome,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )


@auth
async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Fetching your portfolio...")
    try:
        report = trader.get_portfolio()
        await update.message.reply_text(report, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


@auth
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = context.args[0].upper() + "/USDT" if context.args else "BTC/USDT"
    await update.message.reply_text(
        f"🧠 *Analyzing {symbol}...*\nPlease wait.",
        parse_mode="Markdown"
    )
    try:
        analysis = ai.analyze(symbol)
        await update.message.reply_text(analysis, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


@auth
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            f"{BOT_NAME}\n{DIVIDER}\n\n"
            "📈 *Manual Buy*\n\n"
            "Usage: `/buy <SYMBOL> <USDT_AMOUNT>`\n"
            "Example: `/buy BTC 5`",
            parse_mode="Markdown"
        )
        return
    symbol = context.args[0].upper() + "/USDT"
    amount = float(context.args[1])
    await update.message.reply_text(f"⏳ Executing buy order for *${amount}* of *{symbol}*...", parse_mode="Markdown")
    try:
        result = trader.market_buy(symbol, amount)
        TRADE_LOG.append({
            "type": "BUY",
            "symbol": symbol,
            "amount": amount,
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        })
        await update.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


@auth
async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            f"{BOT_NAME}\n{DIVIDER}\n\n"
            "📉 *Manual Sell*\n\n"
            "Usage: `/sell <SYMBOL> <QUANTITY>`\n"
            "Example: `/sell BTC 0.001`",
            parse_mode="Markdown"
        )
        return
    symbol = context.args[0].upper() + "/USDT"
    quantity = float(context.args[1])
    await update.message.reply_text(f"⏳ Executing sell order for *{quantity}* of *{symbol}*...", parse_mode="Markdown")
    try:
        result = trader.market_sell(symbol, quantity)
        TRADE_LOG.append({
            "type": "SELL",
            "symbol": symbol,
            "quantity": quantity,
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        })
        await update.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


@auth
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auto = context.bot_data.get("auto_trade", False)
    await update.message.reply_text(
        f"{BOT_NAME}\n{DIVIDER}\n\n"
        f"🤖 *System Status*\n\n"
        f"Auto-Trade: {'✅ ACTIVE' if auto else '❌ INACTIVE'}\n"
        f"Trade Amount: *${AUTO_TRADE_AMOUNT} USDT*\n"
        f"Coins Tracked: *{len(SYMBOLS)}*\n"
        f"Price Alerts Set: *{len(PRICE_ALERTS)}*\n"
        f"Trades Logged: *{len(TRADE_LOG)}*\n\n"
        f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        parse_mode="Markdown"
    )


@auth
async def set_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_TRADE_AMOUNT
    if not context.args:
        await update.message.reply_text(
            f"💵 Current auto-trade amount: *${AUTO_TRADE_AMOUNT} USDT*\n\n"
            "To change: `/setamount 10`",
            parse_mode="Markdown"
        )
        return
    try:
        new_amount = float(context.args[0])
        if new_amount < 1:
            await update.message.reply_text("⚠️ Minimum amount is $1 USDT.")
            return
        AUTO_TRADE_AMOUNT = new_amount
        await update.message.reply_text(
            f"✅ Auto-trade amount updated to *${AUTO_TRADE_AMOUNT} USDT*",
            parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("⚠️ Invalid amount. Example: `/setamount 10`", parse_mode="Markdown")


@auth
async def set_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /alert BTC 95000"""
    if len(context.args) < 2:
        await update.message.reply_text(
            f"{BOT_NAME}\n{DIVIDER}\n\n"
            "🔔 *Price Alert Setup*\n\n"
            "Usage: `/alert <SYMBOL> <TARGET_PRICE>`\n"
            "Example: `/alert BTC 95000`\n\n"
            "You will be notified when the price hits your target.",
            parse_mode="Markdown"
        )
        return
    symbol = context.args[0].upper() + "/USDT"
    target = float(context.args[1])
    PRICE_ALERTS[symbol] = target
    await update.message.reply_text(
        f"🔔 *Alert Set*\n\n"
        f"Symbol: *{symbol}*\n"
        f"Target Price: *${target:,.2f}*\n\n"
        f"You will be notified when the price is reached.",
        parse_mode="Markdown"
    )


@auth
async def list_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not PRICE_ALERTS:
        await update.message.reply_text("🔔 No price alerts set.\n\nUse `/alert BTC 95000` to set one.", parse_mode="Markdown")
        return
    lines = [f"{BOT_NAME}\n{DIVIDER}\n\n🔔 *Active Price Alerts*\n"]
    for symbol, target in PRICE_ALERTS.items():
        try:
            current = trader.get_price(symbol)
            diff = ((target - current) / current) * 100
            direction = "⬆️" if target > current else "⬇️"
            lines.append(f"{direction} *{symbol}*\n   Target: ${target:,.2f} | Now: ${current:,.2f} ({diff:+.1f}%)\n")
        except Exception:
            lines.append(f"• *{symbol}* → ${target:,.2f}\n")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@auth
async def pnl_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not TRADE_LOG:
        await update.message.reply_text(
            f"{BOT_NAME}\n{DIVIDER}\n\n"
            "📊 *P&L Summary*\n\n"
            "No trades recorded yet.\n"
            "Trades will appear here once you start buying and selling.",
            parse_mode="Markdown"
        )
        return
    buys = [t for t in TRADE_LOG if t["type"] == "BUY"]
    sells = [t for t in TRADE_LOG if t["type"] == "SELL"]
    total_bought = sum(t.get("amount", 0) for t in buys)
    lines = [
        f"{BOT_NAME}\n{DIVIDER}\n\n"
        f"📊 *Trading Summary*\n\n"
        f"Total Trades: *{len(TRADE_LOG)}*\n"
        f"Buy Orders: *{len(buys)}*\n"
        f"Sell Orders: *{len(sells)}*\n"
        f"Total Deployed: *${total_bought:.2f} USDT*\n\n"
        f"*Recent Trades:*"
    ]
    for trade in TRADE_LOG[-5:]:
        emoji = "📈" if trade["type"] == "BUY" else "📉"
        lines.append(f"{emoji} {trade['type']} {trade['symbol']} — {trade['time']}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@auth
async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        f"{BOT_NAME}\n{DIVIDER}\n\n"
        "❓ *Command Reference*\n\n"
        "🔹 `/start` — Main menu\n"
        "🔹 `/portfolio` — View all balances\n"
        "🔹 `/analyze BTC` — AI analysis of any coin\n"
        "🔹 `/buy BTC 5` — Buy $5 worth of BTC\n"
        "🔹 `/sell BTC 0.001` — Sell 0.001 BTC\n"
        "🔹 `/setamount 10` — Set auto-trade amount\n"
        "🔹 `/alert BTC 95000` — Set a price alert\n"
        "🔹 `/alerts` — View all active alerts\n"
        "🔹 `/pnl` — View trade summary\n"
        "🔹 `/status` — Bot status\n\n"
        f"{DIVIDER}\n"
        "💡 _Auto-trade checks all coins every 60 minutes and only acts on high confidence AI signals._"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


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
        await query.edit_message_text("🧠 *Analyzing BTC/USDT...*\nPlease wait.", parse_mode="Markdown")
        try:
            analysis = ai.analyze("BTC/USDT")
            await query.edit_message_text(analysis, parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {e}")

    elif data == "buy_menu":
        await query.edit_message_text(
            f"{BOT_NAME}\n{DIVIDER}\n\n"
            "📈 *Manual Buy*\n\n"
            "Use the command:\n`/buy <SYMBOL> <USDT_AMOUNT>`\n\n"
            "Example: `/buy BTC 5`",
            parse_mode="Markdown"
        )

    elif data == "sell_menu":
        await query.edit_message_text(
            f"{BOT_NAME}\n{DIVIDER}\n\n"
            "📉 *Manual Sell*\n\n"
            "Use the command:\n`/sell <SYMBOL> <QUANTITY>`\n\n"
            "Example: `/sell BTC 0.001`",
            parse_mode="Markdown"
        )

    elif data == "alerts_menu":
        if not PRICE_ALERTS:
            await query.edit_message_text(
                f"{BOT_NAME}\n{DIVIDER}\n\n"
                "🔔 *Price Alerts*\n\n"
                "No alerts set yet.\n\n"
                "Use `/alert BTC 95000` to set one.",
                parse_mode="Markdown"
            )
        else:
            lines = [f"{BOT_NAME}\n{DIVIDER}\n\n🔔 *Active Alerts*\n"]
            for symbol, target in PRICE_ALERTS.items():
                lines.append(f"• *{symbol}* → ${target:,.2f}")
            await query.edit_message_text("\n".join(lines), parse_mode="Markdown")

    elif data == "pnl_summary":
        if not TRADE_LOG:
            await query.edit_message_text(
                f"{BOT_NAME}\n{DIVIDER}\n\n"
                "📊 *P&L Summary*\n\n"
                "No trades recorded yet.",
                parse_mode="Markdown"
            )
        else:
            buys = [t for t in TRADE_LOG if t["type"] == "BUY"]
            sells = [t for t in TRADE_LOG if t["type"] == "SELL"]
            total_bought = sum(t.get("amount", 0) for t in buys)
            lines = [
                f"{BOT_NAME}\n{DIVIDER}\n\n"
                f"📊 *Trading Summary*\n\n"
                f"Total Trades: *{len(TRADE_LOG)}*\n"
                f"Buys: *{len(buys)}* | Sells: *{len(sells)}*\n"
                f"Total Deployed: *${total_bought:.2f} USDT*"
            ]
            await query.edit_message_text("\n".join(lines), parse_mode="Markdown")

    elif data == "help":
        help_text = (
            f"{BOT_NAME}\n{DIVIDER}\n\n"
            "❓ *Command Reference*\n\n"
            "🔹 `/start` — Main menu\n"
            "🔹 `/portfolio` — View balances\n"
            "🔹 `/analyze BTC` — AI analysis\n"
            "🔹 `/buy BTC 5` — Buy crypto\n"
            "🔹 `/sell BTC 0.001` — Sell crypto\n"
            "🔹 `/setamount 10` — Set trade amount\n"
            "🔹 `/alert BTC 95000` — Price alert\n"
            "🔹 `/alerts` — View alerts\n"
            "🔹 `/pnl` — Trade summary\n"
            "🔹 `/status` — Bot status"
        )
        await query.edit_message_text(help_text, parse_mode="Markdown")

    elif data == "toggle_auto":
        current = context.bot_data.get("auto_trade", False)
        context.bot_data["auto_trade"] = not current
        state = "✅ ACTIVE" if not current else "❌ INACTIVE"
        await query.edit_message_text(
            f"{BOT_NAME}\n{DIVIDER}\n\n"
            f"🔄 *Auto-Trading: {state}*\n\n"
            f"Tracking: *{len(SYMBOLS)} coins*\n"
            f"Amount per trade: *${AUTO_TRADE_AMOUNT} USDT*\n"
            f"Frequency: *Every 60 minutes*\n"
            f"Strategy: *High confidence AI signals only*",
            parse_mode="Markdown"
        )


async def price_alert_job(context: ContextTypes.DEFAULT_TYPE):
    """Check price alerts every 5 minutes."""
    if not PRICE_ALERTS:
        return
    chat_id = context.job.chat_id
    triggered = []
    for symbol, target in list(PRICE_ALERTS.items()):
        try:
            current = trader.get_price(symbol)
            if current >= target:
                await context.bot.send_message(
                    chat_id,
                    f"{BOT_NAME}\n{DIVIDER}\n\n"
                    f"🔔 *Price Alert Triggered!*\n\n"
                    f"Symbol: *{symbol}*\n"
                    f"Target: *${target:,.2f}*\n"
                    f"Current: *${current:,.2f}*\n\n"
                    f"Your target price has been reached.",
                    parse_mode="Markdown"
                )
                triggered.append(symbol)
        except Exception as e:
            logger.error(f"Alert check error for {symbol}: {e}")
    for symbol in triggered:
        del PRICE_ALERTS[symbol]


async def daily_summary_job(context: ContextTypes.DEFAULT_TYPE):
    """Send daily P&L summary every 24 hours."""
    chat_id = context.job.chat_id
    try:
        portfolio = trader.get_portfolio()
        buys = [t for t in TRADE_LOG if t["type"] == "BUY"]
        sells = [t for t in TRADE_LOG if t["type"] == "SELL"]
        total_bought = sum(t.get("amount", 0) for t in buys)
        await context.bot.send_message(
            chat_id,
            f"{BOT_NAME}\n{DIVIDER}\n\n"
            f"📊 *Daily Summary — {datetime.utcnow().strftime('%Y-%m-%d')}*\n\n"
            f"Trades Today: *{len(TRADE_LOG)}*\n"
            f"Buys: *{len(buys)}* | Sells: *{len(sells)}*\n"
            f"Capital Deployed: *${total_bought:.2f} USDT*\n\n"
            f"{DIVIDER}\n\n{portfolio}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Daily summary error: {e}")


async def auto_trade_job(context: ContextTypes.DEFAULT_TYPE):
    if not context.bot_data.get("auto_trade", False):
        return
    chat_id = context.job.chat_id
    await context.bot.send_message(
        chat_id,
        f"{BOT_NAME}\n{DIVIDER}\n\n"
        f"🔍 *Auto-Trade Scan Initiated*\n"
        f"Analyzing {len(SYMBOLS)} coins...\n"
        f"🕐 {datetime.utcnow().strftime('%H:%M UTC')}",
        parse_mode="Markdown"
    )
    trades_made = 0
    for symbol in SYMBOLS:
        try:
            action = ai.get_action(symbol)
            if action == "BUY":
                result = trader.market_buy(symbol, amount_usdt=AUTO_TRADE_AMOUNT)
                signal = ai.get_signal(symbol)
                TRADE_LOG.append({
                    "type": "BUY",
                    "symbol": symbol,
                    "amount": AUTO_TRADE_AMOUNT,
                    "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
                })
                await context.bot.send_message(
                    chat_id,
                    f"📈 *Auto-Buy Executed — {symbol}*\n\n{signal}\n\n{result}",
                    parse_mode="Markdown"
                )
                trades_made += 1
            elif action == "SELL":
                result = trader.auto_sell(symbol)
                signal = ai.get_signal(symbol)
                TRADE_LOG.append({
                    "type": "SELL",
                    "symbol": symbol,
                    "quantity": 0,
                    "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
                })
                await context.bot.send_message(
                    chat_id,
                    f"📉 *Auto-Sell Executed — {symbol}*\n\n{signal}\n\n{result}",
                    parse_mode="Markdown"
                )
                trades_made += 1
        except Exception as e:
            logger.error(f"Auto-trade error for {symbol}: {e}")

    await context.bot.send_message(
        chat_id,
        f"{BOT_NAME}\n{DIVIDER}\n\n"
        f"✅ *Scan Complete*\n\n"
        f"Coins Analyzed: *{len(SYMBOLS)}*\n"
        f"Trades Executed: *{trades_made}*\n"
        f"Next Scan: *60 minutes*",
        parse_mode="Markdown"
    )


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN not set!")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("setamount", set_amount))
    app.add_handler(CommandHandler("alert", set_alert))
    app.add_handler(CommandHandler("alerts", list_alerts))
    app.add_handler(CommandHandler("pnl", pnl_summary))
    app.add_handler(CommandHandler("help", help_menu))
    app.add_handler(CallbackQueryHandler(button_handler))

    jq = app.job_queue
    jq.run_repeating(auto_trade_job, interval=3600, first=60,
                     chat_id=ALLOWED_USER_ID, name="auto_trade")
    jq.run_repeating(price_alert_job, interval=300, first=30,
                     chat_id=ALLOWED_USER_ID, name="price_alerts")
    jq.run_repeating(daily_summary_job, interval=86400, first=86400,
                     chat_id=ALLOWED_USER_ID, name="daily_summary")

    logger.info("⚡ LEVERAGE LIQUID — Online")
    app.run_polling()


if __name__ == "__main__":
    main()
