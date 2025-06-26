import logging
from telegram import Update, ChatPermissions
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from @BotFather
TOKEN = "8113998480:AAEa79XP5SW_gXswk3hMGrBzYowrEnEXQ9c"

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hello! I am a message cleanup bot. Add me to a group and give me admin rights to delete non-admin messages.')

def delete_non_admin_messages(update: Update, context: CallbackContext) -> None:
    """Delete non-admin messages in batches of 30."""
    if not update.message or not update.message.chat:
        return
    
    chat = update.message.chat
    bot = context.bot
    
    # Check if bot is admin
    bot_member = chat.get_member(bot.id)
    if not bot_member or not bot_member.status in ['administrator', 'creator']:
        logger.warning(f"Bot is not admin in chat {chat.id}")
        return
    
    # Get chat administrators
    try:
        admins = context.bot.get_chat_administrators(chat.id)
        admin_ids = [admin.user.id for admin in admins]
    except Exception as e:
        logger.error(f"Error getting admins: {e}")
        return
    
    # Function to process messages in batches
    def process_messages(messages):
        message_ids_to_delete = []
        
        for message in messages:
            # Skip if message is from admin or doesn't have a user
            if not message.from_user or message.from_user.id in admin_ids:
                continue
            
            message_ids_to_delete.append(message.message_id)
            
            # Process in batches of 30
            if len(message_ids_to_delete) >= 30:
                try:
                    context.bot.delete_messages(
                        chat_id=chat.id,
                        message_ids=message_ids_to_delete
                    )
                    logger.info(f"Deleted {len(message_ids_to_delete)} messages in chat {chat.id}")
                    message_ids_to_delete = []
                except Exception as e:
                    logger.error(f"Error deleting messages: {e}")
                    message_ids_to_delete = []
        
        # Delete any remaining messages
        if message_ids_to_delete:
            try:
                context.bot.delete_messages(
                    chat_id=chat.id,
                    message_ids=message_ids_to_delete
                )
                logger.info(f"Deleted {len(message_ids_to_delete)} messages in chat {chat.id}")
            except Exception as e:
                logger.error(f"Error deleting remaining messages: {e}")

    # Get recent messages (adjust limit as needed)
    try:
        messages = list(context.bot.get_chat_history(chat.id, limit=100))
        process_messages(messages)
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")

def main() -> None:
    """Start the bot."""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("clean", delete_non_admin_messages))
    
    # For auto-cleaning, you can add a MessageHandler that triggers on each message
    # dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.status_update, delete_non_admin_messages))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
