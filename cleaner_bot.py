import logging
import os
from typing import List, Optional
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
ADMIN_IDS: List[int] = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
ALLOWED_CHAT_IDS: List[int] = [int(id) for id in os.getenv('ALLOWED_CHAT_IDS', '').split(',') if id]
BATCH_SIZE: int = int(os.getenv('BATCH_SIZE', 30))
MESSAGE_LIMIT: int = int(os.getenv('MESSAGE_LIMIT', 100))
LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL)
)
logger = logging.getLogger(__name__)

def is_authorized(update: Update) -> bool:
    """Check if user is authorized to use bot commands."""
    if not ADMIN_IDS:  # No restriction if not set
        return True
    return update.effective_user.id in ADMIN_IDS

def is_allowed_chat(chat_id: int) -> bool:
    """Check if bot is allowed to operate in this chat."""
    if not ALLOWED_CHAT_IDS:  # No restriction if not set
        return True
    return chat_id in ALLOWED_CHAT_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message."""
    if not is_authorized(update):
        return
    await update.message.reply_text(
        "🧹 Group Cleaner Bot\n\n"
        "I automatically delete non-admin messages.\n"
        "Commands:\n"
        "/clean - Delete recent non-admin messages\n"
        "/start - Show this message"
    )

async def clean_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete non-admin messages in batches."""
    if not update.message or not update.effective_chat:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Authorization checks
    if not is_authorized(update):
        logger.warning(f"Unauthorized access by {user.id} in chat {chat.id}")
        return
    
    if not is_allowed_chat(chat.id):
        logger.warning(f"Attempt to use in non-allowed chat {chat.id}")
        return
    
    try:
        # Verify bot admin status
        bot_member = await chat.get_member(context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ I need admin rights with 'Delete Messages' permission!")
            return
        
        # Get admin list
        admins = await chat.get_administrators()
        admin_ids = {admin.user.id for admin in admins}
        
        # Collect message IDs to delete
        message_ids = []
        deleted_count = 0
        
        async for message in context.bot.get_chat_history(chat.id, limit=MESSAGE_LIMIT):
            if message.from_user and message.from_user.id not in admin_ids:
                message_ids.append(message.message_id)
                
                # Delete in batches
                if len(message_ids) >= BATCH_SIZE:
                    await context.bot.delete_messages(chat.id, message_ids)
                    deleted_count += len(message_ids)
                    message_ids = []
                    logger.info(f"Deleted batch in chat {chat.id}")
        
        # Delete remaining messages
        if message_ids:
            await context.bot.delete_messages(chat.id, message_ids)
            deleted_count += len(message_ids)
        
        # Send confirmation
        await update.message.reply_text(f"✅ Deleted {deleted_count} non-admin messages!")
        logger.info(f"Total deleted in chat {chat.id}: {deleted_count}")
    
    except Exception as e:
        logger.error(f"Error in chat {chat.id}: {str(e)}", exc_info=True)
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN must be set in .env file")
    
    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clean", clean_messages))
    
    # Start the bot
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
