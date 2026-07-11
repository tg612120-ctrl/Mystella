from pyrogram import filters
from pyrogram.types import ChatPermissions
from clients import app
import asyncio
from core.guards import is_admin

# --- Purana Code ---
async def kick_user(client, m):
    if not await is_admin(client, m.chat.id, m.from_user.id):
        return
    if m.reply_to_message:
        await m.chat.ban_member(m.reply_to_message.from_user.id)
        await m.chat.unban_member(m.reply_to_message.from_user.id)
        await m.reply_text("👞 Kicked.")

async def ban_user(client, m):
    if not await is_admin(client, m.chat.id, m.from_user.id):
        return
    if m.reply_to_message:
        await m.chat.ban_member(m.reply_to_message.from_user.id)
        await m.reply_text("⛔ Banned.")

async def unban_user(client, m):
    if not await is_admin(client, m.chat.id, m.from_user.id):
        return
    if m.reply_to_message:
        await m.chat.unban_member(m.reply_to_message.from_user.id)
        await m.reply_text("✅ Unbanned.")

async def mute_user(client, m):
    if not await is_admin(client, m.chat.id, m.from_user.id):
        return
    if m.reply_to_message:
        await m.chat.restrict_member(
            m.reply_to_message.from_user.id,
            ChatPermissions(can_send_messages=False),
        )
        await m.reply_text("🔇 Muted.")

async def unmute_user(client, m):
    if not await is_admin(client, m.chat.id, m.from_user.id):
        return
    if m.reply_to_message:
        await m.chat.restrict_member(
            m.reply_to_message.from_user.id,
            ChatPermissions(can_send_messages=True),
        )
        await m.reply_text("🔊 Unmuted.")

# --- Naya /get Feature (Fixed version) ---
@app.on_message(filters.command("get") & filters.private)
async def get_groups(client, message):
    # Circular import fix: db ko yahan function ke andar import kiya hai
    from main import db
    
    # Sirf tum access kar paoge
    if message.from_user.id != client.clone_owner:
        return

    groups = await db.groups.find().to_list(length=None)
    if not groups:
        return await message.reply("No groups found in database!")
    
    for i in range(0, len(groups), 5):
        chunk = groups[i:i + 5]
        text = "**Groups List (5 per page):**\n\n"
        for g in chunk:
            text += f"🏢 {g['title']} (`{g['chat_id']}`)\n"
        await message.reply(text)
        await asyncio.sleep(1)

