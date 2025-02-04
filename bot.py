import logging
from datetime import datetime
from telegram import Update, BotCommand
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

# Define the menu commands
COMMANDS = [
    BotCommand("start", "Start the bot and register"),
    BotCommand("help", "Get help and usage instructions"),
    BotCommand("remind", "Set a reminder (e.g., /remind Buy milk 2023-10-31 12:00)"),
]

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
        await update.message.reply_text(f"Welcome, {username}! You have been registered.")
    else:
        await update.message.reply_text(f"Welcome back, {username}!")
    db.close()

# Help command
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = "Available commands:\n"
    for command in COMMANDS:
        help_text += f"/{command.command} - {command.description}\n"
    await update.message.reply_text(help_text)

# Remind command
async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user provided enough arguments
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /remind <text> <time>\n"
            "Example: /remind Buy milk 2023-10-31 12:00"
        )
        return

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    text = " ".join(context.args[:-1])  # Reminder text
    time_str = context.args[-1]  # Reminder time (e.g., "2023-10-31 12:00")

    try:
        # Parse the time string into a datetime object
        reminder_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        await update.message.reply_text(
            "Invalid time format. Please use: YYYY-MM-DD HH:MM\n"
            "Example: 2023-10-31 12:00"
        )
        return

    try:
        # Save the reminder to the database
        db = SessionLocal()
        reminder = Reminder(
            user_id=user_id,
            chat_id=chat_id,
            reminder_text=text,
            reminder_time=reminder_time
        )
        db.add(reminder)
        db.commit()
        await update.message.reply_text(f"Reminder set for {time_str}!")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        db.close()

# Post-initialization function to set menu commands
async def post_init(application):
    """Set menu commands after the bot starts."""
    await application.bot.set_my_commands(COMMANDS)

# Main function to run the bot
def main():
    # Build the bot application
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("remind", remind))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()