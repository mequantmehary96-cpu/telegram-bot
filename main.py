import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from flask import Flask
import aiohttp
import threading
import asyncio

# ========================
# CONFIG
# ========================
TOKEN = "8099027155:AAH7HApppZgqHq1uAHgt7HlUNldVl-f8-Rc"
BOT_USERNAME = "@YourBotUsername"  # replace with your bot username
GROUP_LINK = "https://t.me/onlineworksfutur"
ADMIN_ID = 7974169540
PING_URL = "https://replit.com/@mequantmeh/bot"  # can keep for uptime

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ========================
# DATA STORAGE
# ========================
user_data = {}
added_members = {}  # track how many people each user added to the group
balances = {}
withdraw_requests = []

# ========================
# CONSTANTS
# ========================
BROADCAST = range(1)

# ========================
# START COMMAND
# ========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data[user.id] = {"name": user.first_name}
    
    keyboard = [
        [InlineKeyboardButton("🚀 Join Group", url=GROUP_LINK)],
        [InlineKeyboardButton("👥 My Added Members & Balance", callback_data="referrals")],
        [InlineKeyboardButton("💰 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")]
    ]
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 **Welcome {user.first_name}! እንኳን ደህና መጡ!**\n\n"
        f"👉 Add your friends to this group and earn money.\n"
        f"👉 ወዳጆችህን ወደ group ጨምር እና ገንዘብ ያሸምቱ።\n\n"
        f"Share your referral link: {BOT_USERNAME}?start={user.id}"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

# ========================
# BUTTON HANDLER
# ========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "referrals":
        count = added_members.get(user_id, 0)
        balance = balances.get(user_id, 0)
        text = f"👥 Added Members: {count}\n💰 Balance: {balance} birr"
        await query.edit_message_text(text, reply_markup=query.message.reply_markup)

    elif query.data == "withdraw":
        balance = balances.get(user_id, 0)
        if balance >= 100:  # minimum withdrawal
            balances[user_id] -= balance
            withdraw_requests.append((user_id, balance))
            text = f"💵 Withdrawal request sent to admin for {balance} birr."
        else:
            text = f"❌ You need {100 - balance} birr more to withdraw."
        await query.edit_message_text(text, reply_markup=query.message.reply_markup)

    elif query.data == "leaderboard":
        lb = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:5]
        leaderboard_text = "🏆 **Top 5 Users** 🏆\n\n"
        for i, (uid, bal) in enumerate(lb, start=1):
            leaderboard_text += f"{i}. {user_data.get(uid, {}).get('name', 'Unknown')} - {bal} birr\n"
        await query.edit_message_text(leaderboard_text, parse_mode="Markdown", reply_markup=query.message.reply_markup)

    elif query.data == "admin" and user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("📢 Broadcast Message", callback_data="broadcast")],
            [InlineKeyboardButton("📊 View Leaderboard", callback_data="leaderboard")]
        ]
        await query.edit_message_text("🛠 **Admin Panel**", parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))

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
# FLASK SERVER
# ========================
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ========================
# MAIN
# ========================
def main():
    # Start Flask server in another thread
    threading.Thread(target=run_flask).start()

    # Telegram bot
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

    app_bot.run_polling()

if __name__ == "__main__":
    main()
