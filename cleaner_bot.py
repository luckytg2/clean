from pyrogram import Client, filters
from pyrogram.types import Message
import os, asyncio, sys
from dotenv import load_dotenv

load_dotenv()  # Load .env file

# Check if variables exist
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not all([API_ID, API_HASH, BOT_TOKEN]):
    print("❌ Error: Missing environment variables (API_ID, API_HASH, BOT_TOKEN)")
    sys.exit(1)

try:
    API_ID = int(API_ID)  # Convert API_ID to integer
except ValueError:
    print("❌ Error: API_ID must be a number")
    sys.exit(1)

app = Client(
    "cleaner_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# ... rest of your code ...
async def get_admin_ids(chat_id):
    if chat_id in admins_cache:
        return admins_cache[chat_id]
    admins = await app.get_chat_members(chat_id, filter="administrators")
    admin_ids = {m.user.id for m in admins}
    admins_cache[chat_id] = admin_ids
    return admin_ids

@app.on_message(filters.command("clean") & filters.group)
async def clean(_, msg: Message):
    admins = await get_admin_ids(msg.chat.id)
    if msg.from_user.id not in admins:
        await msg.reply("❌ Only admins can use this command.")
        return

    await msg.reply("🧹 Cleaning started...")

    deleted = 0
    kept = 0
    async for m in app.get_chat_history(msg.chat.id):
        if m.from_user and m.from_user.id in admins:
            kept += 1
            continue
        try:
            await m.delete()
            deleted += 1
        except:
            pass

    await msg.reply(f"✅ Done!\nDeleted: {deleted}\nKept (admin): {kept}")

app.run()
