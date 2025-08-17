import logging
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== CONFIG =====
TOKEN = "8099027155:AAH7HApppZgqHq1uAHgt7HlUNldVl-f8-Rc"
ADMIN_ID = 7974169540
GROUP_LINK = "https://t.me/onlineworksfutur"

# ===== FLASK SERVER (for Render ping) =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# ===== TELEGRAM BOT LOGIC =====
logging.basicConfig(level=logging.INFO)
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        keyboard = [[InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("👋 Welcome Admin!", reply_markup=reply_markup)
    else:
        keyboard = [
            [InlineKeyboardButton("➕ Add Friends", url=GROUP_LINK)],
            [InlineKeyboardButton("💰 Withdraw", callback_data="withdraw")],
            [InlineKeyboardButton("👥 My Referrals", callback_data="referrals")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "👋 ሰላም! Welcome!\n\n"
            "📢 Add your friends to the group and earn money!\n"
            "💵 You get paid for every member you bring.\n\n"
            "🇬🇧 Invite friends → Earn 100 birr minimum to withdraw.\n"
            "🇪🇹 ጓደኞችህን አክል → ከ100 ብር በላይ ለመሰረጥ ትችላለህ።",
            reply_markup=reply_markup
        )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "withdraw":
        balance = user_data.get(user_id, 0)
        if balance >= 100:
            await context.bot.send_message(
                ADMIN_ID, f"💵 Withdraw request from {user_id}, Balance: {balance} birr"
            )
            await query.edit_message_text("✅ Withdraw request sent to admin.")
        else:
            await query.edit_message_text(
                f"⚠️ You need at least 100 birr to withdraw.\n"
                f"💰 Your balance: {balance} birr"
            )
    elif query.data == "referrals":
        referrals = user_data.get(user_id, 0)
        await query.edit_message_text(f"👥 You have {referrals} referrals.")

# ===== MAIN FUNCTION =====
def run():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == "__main__":
    import threading
    threading.Thread(target=run).start()
    app.run(host="0.0.0.0", port=10000)
