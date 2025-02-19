import logging
from datetime import datetime
import yt_dlp
import ffmpeg
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from db import SessionLocal, init_db
from models import User, Reminder
from config import BOT_TOKEN
from io import BytesIO

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
    BotCommand("download_mp3", "Download MP3 file from a link"),
]

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command. Register the user."""
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
    """Handle the /help command. Provide usage instructions."""
    help_text = "Available commands:\n"
    for command in COMMANDS:
        help_text += f"/{command.command} - {command.description}\n"
    await update.message.reply_text(help_text)

# Command to download MP3
async def download_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download MP3 file from a link provided by the user and send it in the chat."""
    url = context.args[0] if context.args else None
    if url:
        chat_id = update.message.chat_id
        
        # Download the audio file using yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloaded.%(ext)s',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            audio_file = ydl.prepare_filename(info_dict)

        # Convert the audio file to MP3 using ffmpeg
        mp3_file = "downloaded.mp3"
        ffmpeg.input(audio_file).output(mp3_file).run()

        # Read the converted MP3 file into memory
        with open(mp3_file, "rb") as file:
            buffer = BytesIO(file.read())
        
        buffer.seek(0)
        await context.bot.send_audio(chat_id=chat_id, audio=buffer, filename="downloaded.mp3")
    else:
        await update.message.reply_text("Please provide a link to download the MP3 file.")

# Post-initialization function to set menu commands
async def post_init(application):
    """Set menu commands after the bot starts."""
    await application.bot.set_my_commands(COMMANDS)

# Main function to run the bot
def main():
    """Run the bot."""
    # Build the bot application
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("download_mp3", download_mp3))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
