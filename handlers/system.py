import time
import aiohttp
import psutil
from pyrogram import Client as PyroClient
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import state
from config import API_ID, API_HASH, MAIN_OWNER, SEARCH_API_URL
from core.guards import check_abuse
from core.helpers import get_readable_time, format_text

async def ping_handler(client, message):
    start = time.time()
    response = await message.reply_text(format_text("Pinging..."))
    tg_ping = round((time.time() - start) * 1000)

    api_ping = "N/A"
    try:
        api_start = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(SEARCH_API_URL, timeout=aiohttp.ClientTimeout(total=5)):
                pass
        api_ping = f"{round((time.time() - api_start) * 1000)}ms"
    except Exception:
        api_ping = "Timeout"

    uptime = get_readable_time(int(time.time() - state.bot_start_time))
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    msg = (
        f"{format_text('Pong!')}\n\n"
        f"{format_text('Telegram:')} <code>{tg_ping}ms</code>\n"
        f"{format_text('Search API:')} <code>{api_ping}</code>\n\n"
        f"<blockquote>{format_text('System')}\n"
        f"{format_text('Uptime:')} <code>{uptime}</code>\n"
        f"{format_text('CPU:')} <code>{cpu}%</code>\n"
        f"{format_text('RAM:')} <code>{mem}%</code>\n"
        f"{format_text('Disk:')} <code>{disk}%</code></blockquote>"
    )
    await response.edit_text(msg, parse_mode=ParseMode.HTML)


async def start_handler(client, message):
    if await check_abuse(message.from_user.id):
        return

    # User ka naam wahi rahega jo uski profile mein hai
    user_mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    photo_url = "https://www.image2url.com/r2/default/images/1783610446751-a7a7fc57-4d6d-44e8-8816-de0463df8b75.jpeg"

    # Screenshot jaisa exact layout, koi extra naam nahi
    caption = (
        f"<blockquote>ʜᴇʏ {user_mention},🌹</blockquote>\n\n"
        f"<blockquote>⊙ ᴛʜɪs ɪs {client.me.first_name} : ғᴀsᴛ & ᴘᴏᴡᴇʀғᴜʟ ᴛɢ ᴍᴜsɪᴄ ʙᴏᴛ.\n"
        f"⊙ sᴍᴏᴏᴛʜ ʙᴇᴀᴛs • sᴛᴀʙʟᴇ & sᴇᴀᴍʟᴇss ᴍᴜsɪᴄ ғʟᴏᴡ.\n"
        f"⊙ ɴᴇᴡ ᴠᴇʀsɪᴏɴ ᴡɪᴛʜ sᴜᴘᴇʀ ғᴀsᴛ ʏᴏᴜᴛᴜʙᴇ ᴀᴘɪ ʙᴀsᴇᴅ .</blockquote>"
    )

    buttons = [
        [InlineKeyboardButton("➕ ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ", url=f"https://t.me/{client.me.username}?startgroup=true")],
        [
            InlineKeyboardButton("ᴏᴡɴᴇʀ", url="https://t.me/izoph"),
            InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="about_cb"),
        ],
        [
            InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/genzportals"),
            InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇs", url="https://t.me/stellabotxsupport"),
        ],
    ]
    await message.reply_photo(photo=photo_url, caption=caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))


async def clone_command(client, message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        return await message.reply_text(
            format_text("Usage: /clone BOT_TOKEN") + "\n\n"
            "<blockquote>" + format_text("How to get a bot token:") + "\n"
            "1. Open @BotFather\n"
            "2. Send /newbot and follow steps\n"
            "3. Copy the token and paste it here" + "</blockquote>",
            parse_mode=ParseMode.HTML,
        )

    token = message.command[1]
    status = await message.reply_text(format_text("Initializing clone..."), parse_mode=ParseMode.HTML)
    try:
        new_client = PyroClient(
            f"clone_{token.split(':')[0]}", api_id=API_ID, api_hash=API_HASH, bot_token=token
        )
        await new_client.start()
        me = await new_client.get_me()
        new_client.clone_owner = user_id
        new_client.is_main = False

        from handlers.router import register_handlers
        register_handlers(new_client)
        state.active_clients[me.id] = new_client

        clone_count = len([c for c in state.active_clients.values() if not getattr(c, "is_main", False)])

        await status.edit_text(
            format_text("Bot cloned successfully!") + "\n\n"
            "<blockquote>" + format_text("Bot:") + f" @{me.username}\n"
            + format_text("Owner:") + f" <code>{user_id}</code>\n"
            + format_text("Total clones:") + f" <code>{clone_count}</code>" + "</blockquote>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await status.edit_text(format_text("Clone failed:") + f"\n<code>{e}</code>", parse_mode=ParseMode.HTML)


async def active_bots_command(client, message):
    if message.from_user.id != MAIN_OWNER:
        return await message.reply_text(format_text("Restricted to main owner."), parse_mode=ParseMode.HTML)

    if not state.active_clients:
        return await message.reply_text(format_text("No active bots found."), parse_mode=ParseMode.HTML)

    text = format_text(f"Active Bots — Total: {len(state.active_clients)}") + "\n\n"
    for _, c in state.active_clients.items():
        username = c.me.username if c.me else "Unknown"
        owner = getattr(c, "clone_owner", "Main")
        tag = format_text("Main") if getattr(c, "is_main", False) else format_text("Clone · Owner: ") + f"<code>{owner}</code>"
        text += f"├ @{username} · {tag}\n"

    await message.reply_text(text, parse_mode=ParseMode.HTML)

