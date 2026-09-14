# ==========================================================
# Copyright (c) 2026 VelocityBots 
# All Rights Reserved.
#
# Project      : VelocityBots Music Telegram Bot
# Powered By   : Artist
# Type         : API Based Telegram Music Bot
#
# Bot          : @ArtistApibot
# Channel      : https://t.me/artistbots
# GitHub       : https://github.com/elevenyts
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================
import asyncio
from pyrogram import filters, types, errors, enums

from Elevenyts import app, db, lang, logger, userbot, config


@app.on_message(filters.command(["leave"]) & app.app.sudo_filter)
@lang.language()
async def _leave(_, m: types.Message):
    """
    Command handler for /leave
    Makes both bot and assistant leave the current chat.
    """
    try:
        await m.delete()
    except Exception:
        pass
    
    chat_id = m.chat.id
    chat_name = m.chat.title or "this chat"

    sent = await m.reply_text(
        f"<blockquote><b>🌱 Leaving Chat</b></blockquote>\n\n"
        f"<blockquote>Bot and assistant are leaving <b>{chat_name}</b>...</blockquote>"
    )

    try:
        client = await db.get_client(chat_id)
        try:
            await client.leave_chat(chat_id)
        except errors.UserNotParticipant:
            pass
        except Exception:
            pass
    except Exception:
        pass

    try:
        await app.leave_chat(chat_id)
    except Exception as e:
        await sent.edit_text(
            f"<blockquote><b>ℹ️ Error</b></blockquote>\n\n"
            f"<blockquote>Failed to leave chat: {str(e)}</blockquote>"
        )


@app.on_message(filters.command(["leaveall"]) & app.sudo_filter)
@lang.language()
async def _leaveall(_, m: types.Message):
    """
    Command handler for /leaveall
    Makes all assistants leave all inactive groups (not in active calls).
    """
    try:
        await m.delete()
    except Exception:
        pass
    
    sent = await m.reply_text(
        f"<blockquote><b>⏳ Processing...</b></blockquote>\n\n"
        f"<blockquote>Making assistants leave all inactive groups...</blockquote>"
    )
    
    total_left = 0
    
    for ub in userbot.clients:
        left = 0
        try:
            async for dialog in ub.get_dialogs():
                chat_id = dialog.chat.id
                excluded = [app.logger] + config.EXCLUDED_CHATS
                if chat_id in excluded:
                    continue
                
                if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                    if chat_id in db.active_calls:
                        continue
                        
                    try:
                        await ub.leave_chat(chat_id)
                        left += 1
                        total_left += 1
                        await asyncio.sleep(1)  # Rate limit
                    except Exception as e:
                        logger.debug(f"Failed to leave {chat_id}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error in leaveall for assistant: {e}")
            continue
    
    await sent.edit_text(
        f"<blockquote><b>ℹ️ Cleanup Complete</b></blockquote>\n\n"
        f"<blockquote>Assistants left <b>{total_left}</b> inactive groups.</blockquote>"
    )
