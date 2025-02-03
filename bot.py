import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from db import SessionLocal, init_db
from models import User, Reminder
from config import BOT_TOKEN

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize the database
init_db()

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    username = update.message.from_user.username

    # Save user to the database
    db = SessionLocal()
    user = db.query(User).filter(User.chat_id == chat_id).first()
    if not user:
        user = User(username=username, chat_id=chat_id)
        db.add(user)
        db.commit()
        await update.message.reply_text(f"Привет, {username}! Ты был зарегистрирован.")
    else:
        await update.message.reply_text(f"Привет,давно не виделись, {username}!")
    db.close()

# Help command
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start для регистрации")

# Remind command
async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    text = " ".join(context.args[:-1])  # Reminder text
    time_str = context.args[-1]  # Reminder time (e.g., "2023-10-31 12:00")

    try:
        reminder_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        db = SessionLocal()
        reminder = Reminder(
            user_id=user_id,
            chat_id=chat_id,
            reminder_text=text,
            reminder_time=reminder_time
        )
        db.add(reminder)
        db.commit()
        await update.message.reply_text(f"Напоминание поставлено на: {time_str}!")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")
    finally:
        db.close()

# Main function to run the bot
def main():
    # Build the bot application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("remind", remind))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()