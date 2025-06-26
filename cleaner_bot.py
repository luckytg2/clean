from pyrogram import Client, filters
from pyrogram.types import Message
import os
import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Validate environment variables
if not all([API_ID, API_HASH, BOT_TOKEN]):
    print("Error: Missing required environment variables (API_ID, API_HASH, BOT_TOKEN)")
    sys.exit(1)

try:
    API_ID = int(API_ID)
except ValueError:
    print("Error: API_ID must be a valid integer")
    sys.exit(1)

# Initialize Pyrogram client
app = Client(
    "group_cleaner_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# Admin cache to avoid frequent API calls
_admin_cache = {}

async def get_admin_ids(chat_id: int) -> set[int]:
    """Get all admin IDs for a chat with caching"""
    if chat_id in _admin_cache:
        return _admin_cache[chat_id]
    
    admins = await app.get_chat_members(chat_id, filter="administrators")
    admin_ids = {admin.user.id for admin in admins if admin.user}
    _admin_cache[chat_id] = admin_ids
    return admin_ids

def is_admin_message(msg: Message, admin_ids: set[int]) -> bool:
    """Check if a message was sent by an admin (including anonymous)"""
    # Regular admin message
    if msg.from_user and msg.from_user.id in admin_ids:
        return True
    
    # Anonymous admin message (when "post as channel" is enabled)
    if msg.sender_chat and msg.sender_chat.id == msg.chat.id:
        return True
    
    return False

@app.on_message(filters.command("clean") & filters.group)
async def clean_messages(_, msg: Message):
    # Check if the command sender is an admin
    chat_id = msg.chat.id
    admins = await get_admin_ids(chat_id)
    
    if msg.from_user and msg.from_user.id not in admins:
        await msg.reply("❌ Only admins can use this command.")
        return
    
    # Confirm the cleaning process
    status_msg = await msg.reply("🧹 Starting message cleanup...")
    
    deleted_count = 0
    kept_count = 0
    errors = 0
    
    # Iterate through chat history
    async for message in app.get_chat_history(chat_id):
        # Skip if it's the status message itself
        if message.id == status_msg.id:
            continue
        
        if is_admin_message(message, admins):
            kept_count += 1
            continue
        
        try:
            await message.delete()
            deleted_count += 1
            # Small delay to avoid flood limits
            await asyncio.sleep(0.5)
        except Exception as e:
            errors += 1
            continue
    
    # Send final report
    report = (
        "✅ Cleanup completed!\n"
        f"• Messages kept (admin): {kept_count}\n"
        f"• Messages deleted: {deleted_count}\n"
        f"• Errors encountered: {errors}"
    )
    
    await status_msg.edit(report)

@app.on_message(filters.command("start") & filters.private)
async def start(_, msg: Message):
    await msg.reply(
        "👋 Hello! I'm a group cleaner bot.\n\n"
        "Add me to a group where I have admin privileges, "
        "then use /clean in the group to delete all non-admin messages.\n\n"
        "⚠️ Note: I will preserve messages sent by admins, "
        "including those sent anonymously."
    )

if __name__ == "__main__":
    print("Bot is running...")
    app.run()
