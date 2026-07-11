import asyncio
import logging
import os
import subprocess
import threading

from pyrogram import filters, idle
from pyrogram.handlers import MessageHandler
# New Imports for Database
from motor.motor_asyncio import AsyncIOMotorClient

import state
from clients import app, call_py, user_app
from config import COOKIES_FILE, DEPLOYED_OWNER_ID, YOUTUBE_COOKIES, MONGO_DB_URI
from handlers.router import register_handlers
from handlers.system import active_bots_command, clone_command
from server import start_server

# Database Initialization
mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client.kustmusic

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [KustMusic] - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if not os.path.exists("downloads"):
    os.makedirs("downloads")

if YOUTUBE_COOKIES:
    with open(COOKIES_FILE, "w", encoding="utf-8") as _cf:
        _cf.write(YOUTUBE_COOKIES)
    logger.info(f"Cookies written to {COOKIES_FILE} from YOUTUBE_COOKIES env")

def _init_ejs_solver():
    try:
        result = subprocess.run(["deno", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Deno detected: {result.stdout.strip()}")
        else:
            logger.warning("Deno not found in PATH — yt-dlp JS challenges may fail")
        subprocess.run(["yt-dlp", "--rm-cache-dir"], check=False, capture_output=True)
        subprocess.run(
            ["yt-dlp", "--remote-components", "ejs:github",
             "--simulate", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
            check=False, capture_output=True,
        )
        logger.info("yt-dlp EJS solver initialized")
    except Exception as e:
        logger.warning(f"EJS solver init failed: {e}")

threading.Thread(target=_init_ejs_solver, daemon=True).start()

async def main():
    logger.info("Starting KustMusic")
    await start_server()
    await app.start()
    
    app.clone_owner = DEPLOYED_OWNER_ID
    app.is_main = True
    register_handlers(app)
    app.add_handler(MessageHandler(clone_command, filters.command("clone") & filters.private))
    app.add_handler(MessageHandler(active_bots_command, filters.command("active") & filters.private))
    
    # --- MONITORING & DATABASE LOGIC START ---
    @app.on_message(filters.group & (filters.new_chat_members | filters.left_chat_member), group=10)
    async def group_monitor(client, message):
        bot_id = (await client.get_me()).id
        
        # Logic for Adding Bot
        if message.new_chat_members and any(m.id == bot_id for m in message.new_chat_members):
            await db.groups.update_one({"chat_id": message.chat.id}, {"$set": {"title": message.chat.title}}, upsert=True)
            adder = message.from_user
            mention = adder.mention if adder else "Unknown"
            try:
                link = await client.export_chat_invite_link(message.chat.id)
            except:
                link = "No admin rights"
            await client.send_message(DEPLOYED_OWNER_ID, f"➕ **Bot Added!**\n\n🏢 Group: {message.chat.title}\n👤 By: {mention}\n🔗 {link}")

        # Logic for Removing Bot
        elif message.left_chat_member and message.left_chat_member.id == bot_id:
            await db.groups.delete_one({"chat_id": message.chat.id})
            await client.send_message(DEPLOYED_OWNER_ID, f"➖ **Bot Removed from:** {message.chat.title}")

    @app.on_message(filters.command("start") & filters.private, group=11)
    async def start_monitor(client, message):
        user = message.from_user
        await client.send_message(
            DEPLOYED_OWNER_ID,
            f"👤 **User Started Bot**\n\nName: {user.mention}\nID: `{user.id}`\nUsername: @{user.username}"
        )
        message.continue_propagation()

    # Command to get group list (5 per message)
    @app.on_message(filters.command("get") & filters.private & filters.user(DEPLOYED_OWNER_ID), group=12)
    async def get_groups(client, message):
        groups = await db.groups.find().to_list(length=None)
        if not groups:
            return await message.reply("No groups in database!")
        for i in range(0, len(groups), 5):
            chunk = groups[i:i + 5]
            text = "**Groups List (5 per page):**\n\n"
            for g in chunk:
                text += f"🏢 {g['title']} (`{g['chat_id']}`)\n"
            await message.reply(text)
            await asyncio.sleep(1)
    # --- MONITORING & DATABASE LOGIC END ---

    state.active_clients[app.me.id] = app
    await user_app.start()
    me = await user_app.get_me()
    state.ASSISTANT_ID = me.id
    state.ASSISTANT_USERNAME = me.username
    logger.info(f"Assistant: {state.ASSISTANT_ID} (@{state.ASSISTANT_USERNAME})")

    await call_py.start()
    logger.info(f"Bot running: @{app.me.username}")
    await idle()
    await call_py.stop()
    await user_app.stop()
    for c in list(state.active_clients.values()):
        try:
            await c.stop()
        except Exception:
            pass

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
