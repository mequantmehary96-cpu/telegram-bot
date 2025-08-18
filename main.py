import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from flask import Flask
import os
import aiohttp
import asyncio

# ========================
# CONFIG
# ========================
TOKEN = "8099027155:AAH7HApppZgqHq1uAHgt7HlUNldVl-f8-Rc"
BOT_USERNAME = "@YourBotUsername"
GROUP_LINK = "https://t.me/onlineworksfutur"
ADMIN_ID = 7974169540
PING_URL = "https://replit.com/@mequantmeh/bot"  # Used for keeping alive if needed

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ========================
# DATA STORAGE
# ========================
user_data = {}       # user_id: {"name": name, "referrals": count, "balance": int}
referrals = {}       # user_id: number of users they added
balances = {}        # user_id: balance in birr
withdraw_requests = []  # pending withdraws
milestones = [5, 10, 20]

# ========================
# CONSTANTS
# ========================
BROADCAST = range(1)

# ========================
# FLASK SERVER
# ========================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

# ========================
# START COMMAND
# ========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in user_data:
        user_data[user.id] = {"name": user.first_name, "referrals": 0, "balance": 0}

    # Buttons
    keyboard = [
        [InlineKeyboardButton("🚀 Join Group", url=GROUP_LINK)],
        [InlineKeyboardButton("👥 My Referrals & Balance", callback_data="referrals")],
        [InlineKeyboardButton("💰 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")]
    ]
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Welcome text in English + Amharic
    welcome_text = (
        f"👋 እንኳን ደህና መጡ {user.first_name}!\n"
        "Welcome! Add your friends to this group and earn money!\n\n"
        f"Share this link: {BOT_USERNAME}?start={user.id}\n"
        "እባክዎ ይህን ሊንክ ለጓደኞችዎ አጋራት በዚህ group ተጨማሪ አባላት ያክሉ።"
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# ========================
# BUTTON HANDLER
# ========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "referrals":
        count = user_data.get(user_id, {}).get("referrals", 0)
        balance = user_data.get(user_id, {}).get("balance", 0)
        text = f"👥 Referrals: {count}\n💰 Balance: {balance} birr"
        await query.edit_message_text(text, reply_markup=query.message.reply_markup)

    elif query.data == "withdraw":
        balance = user_data.get(user_id, {}).get("balance", 0)
        if balance >= 100:
            withdraw_requests.append(user_id)
            await query.edit_message_text(f"✅ Withdrawal request sent to admin. Your balance: {balance} birr")
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"💰 Withdrawal request from {user_data[user_id]['name']} ({user_id}). Balance: {balance} birr"
            )
        else:
            await query.edit_message_text(f"❌ Minimum 100 birr required to withdraw. Add {100 - balance} birr more.")

    elif query.data == "leaderboard":
        lb = sorted(user_data.items(), key=lambda x: x[1].get("balance", 0), reverse=True)[:5]
        leaderboard_text = "🏆 Top 5 Users 🏆\n\n"
        for i, (uid, info) in enumerate(lb, start=1):
            leaderboard_text += f"{i}. {info.get('name','Unknown')} - {info.get('balance',0)} birr\n"
        await query.edit_message_text(leaderboard_text, reply_markup=query.message.reply_markup)

    elif query.data == "admin" and user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("📢 Broadcast Message", callback_data="broadcast")],
            [InlineKeyboardButton("📊 View Leaderboard", callback_data="leaderboard")]
        ]
        await query.edit_message_text("🛠 Admin Panel", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "broadcast" and user_id == ADMIN_ID:
        await query.edit_message_text("✍️ Send the message you want to broadcast:")
        return BROADCAST

    else:
        await query.edit_message_text("❌ This option is not available.")

# ========================
# BROADCAST
# ========================
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    count = 0
    for uid in user_data.keys():
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 Broadcast:\n\n{text}")
            count += 1
        except:
            continue
    await update.message.reply_text(f"✅ Message sent to {count} users.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Broadcast canceled.")
    return ConversationHandler.END

# ========================
# SELF PING
# ========================
async def ping_job(context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PING_URL) as resp:
                logging.info(f"Pinged {PING_URL}, status {resp.status}")
        except Exception as e:
            logging.error(f"Ping failed: {e}")

# ========================
# MAIN
# ========================
def main():
    app_bot = Application.builder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="broadcast")],
        states={BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))

    # Ping every 6 minutes
    app_bot.job_queue.run_repeating(ping_job, interval=360, first=10)

    # Run both Flask server and bot
    loop = asyncio.get_event_loop()
    from threading import Thread

    def run_flask():
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

    Thread(target=run_flask).start()
    app_bot.run_polling()

if __name__ == "__main__":
    main()
