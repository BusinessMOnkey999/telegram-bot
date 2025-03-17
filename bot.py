import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

# Set up logging to capture phone numbers and codes
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# States for the conversation
PHONE, CODE = range(2)

# Start command
def start(update, context):
    update.message.reply_text(
        "Welcome to the Safeguard Bot! Please enter your phone number to verify.",
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

    # For this example, we'll use a fixed code "1234"
    verification_code = "1234"
    context.user_data['code'] = verification_code

    # Log the generated code
    logger.info(f"Verification code for user {user.id}: {verification_code}")

    update.message.reply_text(
        f"A verification code has been generated. Your code is: {verification_code}\nPlease enter the code to verify."
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
        update.message.reply_text("Verification successful! You're all set.")
    else:
        update.message.reply_text("Incorrect code. Please try again.")
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
    # Get the bot token from Heroku environment variables
    TOKEN = os.environ.get('TOKEN')
    PORT = int(os.environ.get('PORT', '8443'))
    APP_NAME = os.environ.get('APP_NAME')

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Set up the conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PHONE: [MessageHandler(Filters.text & ~Filters.command, phone)],
            CODE: [MessageHandler(Filters.text & ~Filters.command, code)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)

    # Start the bot using a webhook for Heroku
    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url=f"{APP_NAME}/{TOKEN}")
    updater.idle()

if __name__ == '__main__':
    main()
