# ==========================================================
# Copyright (c) 2026 MGB NOT FREE 
# All Rights Reserved.
#
# Project      : mgb not free
# Powered By   : MGB NOT FREE 
# Type         : API Based Telegram Music Bot
#
# Bot          : @RIYA_MUSIC_X_BOT
# Channel      : https://t.me/RIYA_MUSIC_BOT_786
# GitHub       : https://github.com/mgbnotfree-creator/MGB_NOT_FREE_MUSIC
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================

from pyrogram import Client, filters
from pyrogram.enums import ParseMode

from Elevenyts import app


@app.on_message(filters.command("id"))
async def getid(client: Client, message):
    chat = message.chat
    your_id = message.from_user.id if message.from_user else None
    message_id = message.id
    reply = message.reply_to_message

    text = f"<blockquote><b>🆔 ID Information</b></blockquote>\n\n"
    text += f"<b>💬 Message ID:</b> <a href='{message.link}'><code>{message_id}</code></a>\n"
    
    if your_id:
        text += f"<b>👤 Your ID:</b> <a href='tg://user?id={your_id}'><code>{your_id}</code></a>\n"

    # Check if a username or user ID was passed as an argument
    if len(message.command) == 2:
        try:
            split = message.text.split(None, 1)[1].strip()
            user_obj = await client.get_users(split)
            text += f"<b>🔍 Searched User ID:</b> <a href='tg://user?id={user_obj.id}'><code>{user_obj.id}</code></a>\n"
        except Exception:
            return await message.reply_text("⚠️ Could not find user.", quote=True)

    if chat.username:
        text += f"<b>👥 Chat ID:</b> <a href='https://t.me/{chat.username}'><code>{chat.id}</code></a>\n"
    else:
        text += f"<b>👥 Chat ID:</b> <code>{chat.id}</code>\n"

    if reply:
        if reply.from_user:
            text += f"\n<b>↩️ Replied User ID:</b> <a href='tg://user?id={reply.from_user.id}'><code>{reply.from_user.id}</code></a>"
        if reply.forward_from_chat:
            text += f"\n<b>⏩ Forwarded From:</b> {reply.forward_from_chat.title} (<code>{reply.forward_from_chat.id}</code>)"
        if reply.sender_chat:
            text += f"\n<b>📢 Sender Chat ID:</b> <code>{reply.sender_chat.id}</code>"

    await message.reply_text(
        text,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML,
    )
    
