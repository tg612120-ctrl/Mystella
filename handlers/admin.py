from pyrogram import filters
from pyrogram.types import ChatPermissions
from clients import app
import asyncio
from core.guards import is_admin

# --- Admin Management Commands ---
async def kick_user(client, m):
    if not await is_admin(client, m.chat.id, m.from_user.id): return
    if m.reply_to_message:
        await m.chat.ban_member(m.reply_to_message.from_user.id)
        await m.chat.unban_member(m.reply_to_message.from_user.id)
        await m.reply_text("👞 Kicked.")

async def ban_user(client, m):
    if not await is_admin(client, m.chat.id, m.from_user.id): return
    if m.reply_to_message:
        await m.chat.ban_member(m.reply_to_message.from_user.id)
        await m.reply_text("⛔ Banned.")

async def unban_user(client, m):
    if not await is_admin(client, m.chat.id, m.from_user.id): return
    if m.reply_to_message:
        await m.chat.unban_member(m.reply_to_message.from_user.id)
        await m.reply_text("✅ Unbanned.")

async def mute_user(client, m):
    if not await is_admin(client, m.chat.id, m.from_user.id): return
    if m.reply_to_message:
        await m.chat.restrict_member(m.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False))
        await m.reply_text("🔇 Muted.")

async def unmute_user(client, m):
    if not await is_admin(client, m.chat.id, m.from_user.id): return
    if m.reply_to_message:
        await m.chat.restrict_member(m.reply_to_message.from_user.id, ChatPermissions(can_send_messages=True))
        await m.reply_text("🔊 Unmuted.")

# --- Database Commands ---
@app.on_message(filters.command("get") & filters.private)
async def get_groups(client, message):
    from main import db
    if message.from_user.id != client.clone_owner: return
    groups = await db.groups.find().to_list(length=None)
    if not groups: return await message.reply("No groups found!")
    for i in range(0, len(groups), 5):
        chunk = groups[i:i + 5]
        text = "**Groups List (5 per page):**\n\n"
        for g in chunk: text += f"🏢 {g['title']} (`{g['chat_id']}`)\n"
        await message.reply(text)
        await asyncio.sleep(1)

# --- Broadcast Feature with Logging ---
@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_message(client, message):
    from main import db
    if message.from_user.id != client.clone_owner: return
    
    if not message.reply_to_message:
        return await message.reply("❌ Please reply to a message with /broadcast")
    
    broadcast_msg = message.reply_to_message
    groups = await db.groups.find().to_list(length=None)
    
    if not groups:
        return await message.reply("❌ No groups found in database to broadcast.")
    
    status = await message.reply(f"🚀 Broadcast started to {len(groups)} groups...")
    count = 0
    
    for g in groups:
        try:
            # Ye line Railway logs mein dikhegi
            print(f"DEBUG: Forwarding to {g.get('title', 'Unknown')} (ID: {g['chat_id']})")
            await broadcast_msg.forward(chat_id=g['chat_id'])
            count += 1
            await asyncio.sleep(4) # 4 seconds gap
        except Exception as e:
            print(f"DEBUG: Failed for {g.get('chat_id')}: {e}")
            continue
            
    await status.edit(f"✅ Broadcast finished! Sent to {count} groups.")
