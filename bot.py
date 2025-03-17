import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

# Set up logging to capture user interactions
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# States for the conversation
VERIFY = range(1)

# Start command
def start(update, context):
    # Initial message mimicking the new UI
    welcome_message = (
        "Verify you're human with Safeguard Protection"
    )
    # Create a "Start" button
    keyboard = [[InlineKeyboardButton("START", callback_data='start_verification')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_message, reply_markup=reply_markup)
    return ConversationHandler.END

# Handle the "START" button click
def button_callback(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'start_verification':
        # Prompt for human verification
        query.message.reply_text(
            "🔒 *Human Verification*\n"
            "Verify below to be granted entry",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Click here", callback_data='verify')]])
        )

# Handle the "Click here" button
def verify_callback(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'verify':
        # Prompt the user to log in via QR code or login code
        qr_message = (
            "🔒 *Human Verification*\n\n"
            "To verify, please log in to Telegram on another device:\n"
            "1. Open Telegram on your phone\n"
            "2. Go to Settings > Devices > Link Desktop Device\n"
            "3. Scan the QR code or enter the login code sent to your Telegram account\n\n"
            "Once you’ve logged in, click 'I have logged in' below."
        )
        keyboard = [[InlineKeyboardButton("I have logged in", callback_data='confirm_login')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text(qr_message, parse_mode='Markdown', reply_markup=reply_markup)
        return VERIFY

# Handle the "I have logged in" button
def confirm_login_callback(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'confirm_login':
        user = query.from_user
        # Log the user who completed verification
        logger.info(f"User {user.id} completed verification")

        # Generate a temporary invite link for the group
        group_id = os.environ.get('GROUP_ID')
        if not group_id:
            logger.error("GROUP_ID not set in environment variables.")
            query.message.reply_text("Verification completed, but GROUP_ID is not set. Please contact the admin.")
            return ConversationHandler.END

        try:
            invite_link = query.message.bot.create_chat_invite_link(
                chat_id=group_id,
                expire_date=int(query.message.date.timestamp()) + 3600,  # Link expires in 1 hour
                member_limit=1  # Single-use link
            ).invite_link
            query.message.reply_text(
                "✅ *Verification successful!*\n\n"
                "You can now join the group using the link below:\n"
                f"{invite_link}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to generate invite link: {e}")
            query.message.reply_text("Verification completed, but failed to generate the invite link. Please contact the admin.")

        return ConversationHandler.END

# Cancel command
def cancel(update, context):
    update.message.reply_text("Verification cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Error handler
def error(update, context):
    logger.warning(f"Update {update} caused error {context.error}")

def main():
    # Get the bot token from environment variables
    TOKEN = os.environ.get('TOKEN')
    if not TOKEN:
        logger.error("No TOKEN provided. Set the TOKEN environment variable.")
        return

    PORT = int(os.environ.get('PORT', '8443'))
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Set up the conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(button_callback, pattern='start_verification'),
            CallbackQueryHandler(verify_callback, pattern='verify'),
            CallbackQueryHandler(confirm_login_callback, pattern='confirm_login')
        ],
        states={
            VERIFY: [CallbackQueryHandler(confirm_login_callback, pattern='confirm_login')]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)

    # Get the Render hostname or use a placeholder
    hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'your-app-name.onrender.com')
    webhook_url = f"https://{hostname}/{TOKEN}"
    logger.info(f"Setting webhook to: {webhook_url}")

    try:
        # Start the bot using a webhook
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url=webhook_url)
        logger.info("Webhook set successfully!")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        logger.info("Falling back to polling...")
        updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
