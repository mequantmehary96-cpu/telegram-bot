# ========================
# main.py
# ========================

# Monkey-patch imghdr for Python 3.13
try:
    import imghdr
except ModuleNotFoundError:
    from PIL import Image
    class FakeImghdr:
        @staticmethod
        def what(filename):
            try:
                with Image.open(filename) as img:
                    return img.format.lower()
            except Exception:
                return None
    import sys
    sys.modules['imghdr'] = FakeImghdr

# ========================
# IMPORTS
# ========================
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import aiohttp

# ========================
# CONFIG
# ========================
TOKEN = "8099027155:AAH7HApppZgqHq1uAHgt7HlUNldVl-f8-Rc"
BOT_USERNAME = "@YourBotUsername"
GROUP_LINK = "https://t.me/onlineworksfutur"
ADMIN_ID = 7974169540
PING_URL = "https://replit.com/@mequantmeh/bot"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ========================
# DATA STORAGE
# ========================
user_data = {}
added_members = {}
balances = {}
withdraw_requests = []
milestones = [5, 10, 20]

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
        [InlineKeyboardButton("👥 My Added Members & Balance", callback_data="members")],
        [InlineKeyboardButton("💰 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")]
    ]
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 እንኳን ደህና መጡ {user.first_name}!\n\n"
        f"👉 Add your friends to this group and earn money!\n"
        f"👉 Share your referral link: {BOT_USERNAME}?start={user.id}"
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# ========================
# BUTTON HANDLER
# ========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "members":
        count = added_members.get(user_id, 0)
        balance = balances.get(user_id, 0)
        text = f"👥 Members Added: {count}\n💰 Balance: {balance} birr"
        await query.edit_message_text(text, reply_markup=query.message.reply_markup)

    elif query.data == "withdraw":
        balance = balances.get(user_id, 0)
        if balance >= 100:  # Changed from 200 to 100
            text = f"💵 Withdrawal request sent to admin for {balance} birr."
            withdraw_requests.append({"user_id": user_id, "amount": balance})
            await query.edit_message_text(text)
            # Optionally notify admin here
        else:
            text = f"❌ You need {100 - balance} more birr to withdraw."
            await query.edit_message_text(text)

    elif query.data == "leaderboard":
        lb = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:5]
        leaderboard_text = "🏆 Top 5 Users 🏆\n\n"
        for i, (uid, bal) in enumerate(lb, start=1):
            leaderboard_text += f"{i}. {user_data.get(uid, {}).get('name','Unknown')} - {bal} birr\n"
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
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="broadcast")],
        states={BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))

    app.job_queue.run_repeating(ping_job, interval=360, first=10)
    app.run_polling()

if __name__ == "__main__":
    main()
