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

from pyrogram import filters
from pyrogram.types import Message

from Elevenyts import app


@app.on_message(filters.command("link") & filters.private & app.sudo_filter)
async def group_link(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage:\n/link <group_id>")

    try:
        chat_id = int(message.command[1])
        invite = await app.create_chat_invite_link(chat_id)

        await message.reply_text(
            f"🔗 <b>Group Link:</b>\n{invite.invite_link}",
            disable_web_page_preview=True
        )
    except Exception as e:
        await message.reply_text(f"❌ <b>Error:</b> {e}")
        
