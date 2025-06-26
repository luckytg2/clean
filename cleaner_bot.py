from pyrogram import Client, filters
from pyrogram.types import Message, ChatMember
from pyrogram.enums import ChatMembersFilter
import os
import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not all([API_ID, API_HASH, BOT_TOKEN]):
    print("Error: Missing required environment variables")
    sys.exit(1)

try:
    API_ID = int(API_ID)
except ValueError:
    print("Error: API_ID must be a valid integer")
    sys.exit(1)

app = Client(
    "group_cleaner_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

_admin_cache = {}

async def get_admin_ids(chat_id: int) -> set[int]:
    """Get all admin IDs for a chat with caching"""
    if chat_id in _admin_cache:
        return _admin_cache[chat_id]
    
    admin_ids = set()
    async for member in app.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
        if member.user:
            admin_ids.add(member.user.id)
    
    _admin_cache[chat_id] = admin_ids
    return admin_ids

def is_admin_message(msg: Message, admin_ids: set[int]) -> bool:
    """Check if message was sent by an admin"""
    # Regular admin message
    if msg.from_user and msg.from_user.id in admin_ids:
        return True
    
    # Anonymous admin message
    if msg.sender_chat and msg.sender_chat.id == msg.chat.id:
        return True
    
    return False

@app.on_message(filters.command("clean") & filters.group)
async def clean_messages(_, msg: Message):
    # Check if command sender is admin
    chat_id = msg.chat.id
    try:
        admins = await get_admin_ids(chat_id)
    except Exception as e:
        await msg.reply(f"❌ Failed to get admin list: {str(e)}")
        return
    
    if msg.from_user and msg.from_user.id not in admins:
        await msg.reply("❌ Only admins can use this command.")
        return
    
    status_msg = await msg.reply("🧹 Starting message cleanup...")
    
    deleted_count = 0
    kept_count = 0
    errors = 0
    
    # Use iter_history instead of get_chat_history
    async for message in app.iter_history(chat_id):
        if message.id == status_msg.id:
            continue
        
        if is_admin_message(message, admins):
            kept_count += 1
            continue
        
        try:
            await message.delete()
            deleted_count += 1
            await asyncio.sleep(0.5)  # Flood control
        except Exception:
            errors += 1
            continue
    
    report = (
        "✅ Cleanup completed!\n"
        f"• Kept (admin): {kept_count}\n"
        f"• Deleted: {deleted_count}\n"
        f"• Errors: {errors}"
    )
    
    await status_msg.edit(report)

@app.on_message(filters.command("start") & filters.private)
async def start(_, msg: Message):
    await msg.reply(
        "👋 Group Cleaner Bot\n\n"
        "Add me to a group, make me admin with delete permissions, "
        "then use /clean to remove non-admin messages.\n\n"
        "I preserve messages from admins (including anonymous ones)."
    )

if __name__ == "__main__":
    print("Bot is running...")
    app.run()
