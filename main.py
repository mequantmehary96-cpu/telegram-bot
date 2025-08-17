import logging
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import threading

# ================= CONFIG =================
TOKEN = "8099027155:AAH7HApppZgqHq1uAHgt7HlUNldVl-f8-Rc"
ADMIN_ID = 7974169540
GROUP_LINK = "https://t.me/onlineworksfutur"

# ================= DATA STORAGE =================
user_balances = {}   # user_id -> balance (birr)
user_referrals = {}  # user_id -> referral count

# ================= FLASK SERVER =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# ================= TELEGRAM BOT =================
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Admin view
    if user_id == ADMIN_ID:
        keyboard = [[InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("👋 Welcome Admin! Use your panel below:", reply_markup=reply_markup)

    else:
        keyboard = [
            [InlineKeyboardButton("➕ Add Friends", url=GROUP_LINK)],
            [InlineKeyboardButton("💰 Withdraw", callback_data="withdraw")],
            [InlineKeyboardButton("👥 My Referrals", callback_data="referrals")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send welcome text only
        await update.message.reply_text(
            "👋 ሰላም! Welcome!\n\n"
            "📢 Add your friends to the group and earn money!\n"
            "💵 You get paid for every member you bring.\n\n"
            "🇬🇧 Invite friends → Earn 100 birr minimum to withdraw.\n"
            "🇪🇹 ጓደኞችህን አክል → ከ100 ብር በላይ ለመሰረጥ ትችላለህ።",
            reply_markup=reply_markup
        )

        # Initialize user balances if new
        if user_id not in user_balances:
            user_balances[user_id] = 0
        if user_id not in user_referrals:
            user_referrals[user_id] = 0

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Withdraw button
    if query.data == "withdraw":
        balance = user_balances.get(user_id, 0)
        if balance >= 100:
            await context.bot.send_message(
                ADMIN_ID, f"💵 Withdraw request from {user_id}, Balance: {balance} birr"
            )
            await query.edit_message_text("✅ Withdraw request sent to admin.")
        else:
            needed = 100 - balance
            await query.edit_message_text(
                f"⚠️ You need at least 100 birr to withdraw.\n"
                f"💰 Your balance: {balance} birr\n"
                f"➕ You need {needed} more birr to withdraw."
            )

    # Referral button
    elif query.data == "referrals":
        count = user_referrals.get(user_id, 0)
        await query.edit_message_text(f"👥 You have {count} referrals.")

    # Admin broadcast
    elif query.data == "broadcast" and user_id == ADMIN_ID:
        await update.callback_query.message.reply_text("✍️ Send the message you want to broadcast:")
        return "BROADCAST"

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    count = 0
    for uid in user_balances.keys():
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 Broadcast:\n\n{text}")
            count += 1
        except:
            continue
    await update.message.reply_text(f"✅ Message sent to {count} users.")
    return -1

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Broadcast canceled.")
    return -1

# ================= MAIN FUNCTION =================
def run_bot():
    app_bot = Application.builder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.run_polling()

# ================= RUN BOTH BOT AND FLASK =================
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)
