import logging
import asyncio
from typing import List
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 100))  # Max allowed by Telegram API
DELAY_SECONDS = float(os.getenv('DELAY_SECONDS', 1.0))  # Anti-flood wait

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def delete_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete ALL messages in the chat"""
    if not update.effective_user or not update.effective_chat:
        return
    
    # Authorization check
    if ADMIN_IDS and update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You're not authorized!")
        return
    
    chat = update.effective_chat
    try:
        # Verify bot is admin
        bot_member = await chat.get_member(context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ I need admin rights!")
            return
        
        await update.message.reply_text("⚠️ Starting FULL message deletion...")
        
        total_deleted = 0
        while True:
            # Get the most recent batch
            messages = [
                msg async for msg in context.bot.get_chat_history(chat.id, limit=BATCH_SIZE)
            ]
            
            if not messages:
                break  # No more messages
            
            # Filter out service messages (joins, pins, etc.)
            deletable = [m.message_id for m in messages if m.message_id]
            
            if deletable:
                await context.bot.delete_messages(chat.id, deletable)
                total_deleted += len(deletable)
                logger.info(f"Deleted {len(deletable)} messages (Total: {total_deleted})")
            
            # Anti-flood delay
            await asyncio.sleep(DELAY_SECONDS)
        
        await update.message.reply_text(f"✅ Deleted ALL {total_deleted} messages!")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await update.message.reply_text(f"❌ Failed: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("nuke", delete_all_messages))
    app.run_polling()

if __name__ == '__main__':
    main()
