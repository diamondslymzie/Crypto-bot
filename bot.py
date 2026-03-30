import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes
# This pulls the saving tool we made in database.py
from database import save_new_user

# 1. Get your Bot Token from BotFather (stored in Railway Variables)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 2. The /start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # --- THIS SAVES YOU IN SUPABASE ---
    try:
        save_new_user(user.id, user.username)
    except Exception as e:
        print(f"Database error: {e}")
    # ----------------------------------

    # The visual menu buttons
    keyboard = [
        [
            InlineKeyboardButton("💼 Portfolio", callback_data='portfolio'),
            InlineKeyboardButton("⚡ Trade", callback_data='trade')
        ],
        [
            InlineKeyboardButton("📊 Prices", callback_data='prices'),
            InlineKeyboardButton("🤖 Auto", callback_data='auto')
        ],
        [
            InlineKeyboardButton("📡 Signal", callback_data='signal'),
            InlineKeyboardButton("🎯 Market", callback_data='market')
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data='settings')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 Welcome back, @{user.username}!\n\n"
        f"This is **LIQUID LEVERAGE** — Your premium AI-powered trading assistant.\n\n"
        f"Use the buttons below to control your bot or open the mini app!"
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

# 3. The /help Command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 **Liquid Leverage Bot Commands**\n\n"
        "/start — Open main menu\n"
        "/portfolio — Live Bitget balance\n"
        "/analyze BTC — AI analysis\n"
        "/buy BTC 5 — Manual market buy\n"
        "/sell BTC 0.001 — Manual market sell\n"
        "/setamount 10 — Change auto-trade amount\n"
        "/alerts — View active price alerts\n"
        "/status — Bot system status"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# 4. Starting the Bot
def main():
    # Build the app with your token
    application = Application.builder().token(TOKEN).build()

    # Add the commands the bot listens for
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Run the bot forever on Railway
    print("Bot is starting up...")
    application.run_polling()

if __name__ == '__main__':
    main()
