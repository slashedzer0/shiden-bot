import logging
import os
import requests
from telegram import Update, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from instaloader import Instaloader, Post

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the Telegram bot command handlers
def start(update: Update, context: CallbackContext):
    """Send a welcome message when the command /start is issued."""
    update.message.reply_text('Hi! Send me a link to an Instagram post and I will download the media for you.')

def download_instagram_media(update: Update, context: CallbackContext):
    """Download media from Instagram and send it to the user in Telegram."""
    chat_id = update.message.chat_id
    message = update.message.text
    logger.info(f"User {chat_id} entered {message}")

    # Initialize instaloader
    insta = Instaloader()

    # Load post by URL
    post = Post.from_shortcode(insta.context, message.split("/")[-2])

    # Check if post is a video or an image
    if post.is_video:
        # Get highest resolution video URL
        video_url = post.video_url

        # Download video
        r = requests.get(video_url, stream=True)

        # Send video to user
        context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
        context.bot.send_video(chat_id=chat_id, video=r.raw, supports_streaming=True)
    else:
        # Get highest resolution image URL
        image_url = post.url

        # Download image
        r = requests.get(image_url)

        # Send image to user
        context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
        context.bot.send_photo(chat_id=chat_id, photo=r.content)

def echo(update: Update, context: CallbackContext):
    """Echo the user message."""
    update.message.reply_text(update.message.text)

def error(update: Update, context: CallbackContext):
    """Log errors caused by updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """Start the bot."""
    # Get the Telegram bot token from the environment variable
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token is None:
        logger.error("Please set the TELEGRAM_BOT_TOKEN environment variable.")
        return

    # Create the Updater and pass it the bot token
    updater = Updater(token, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add the command handlers
    dp.add_handler(CommandHandler("start", start))

    # Add the message handler
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_instagram_media))

    # Log all errors
    dp.add_error_handler(error)

    # Start the bot
    logger.info("Bot started.")
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process is stopped
    updater.idle()

if __name__ == '__main__':
    main()
