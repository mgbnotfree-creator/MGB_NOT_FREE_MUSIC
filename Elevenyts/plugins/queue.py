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

from pyrogram import filters, types

from Elevenyts import app, config, db, lang, queue
from Elevenyts.helpers import Track, buttons, thumb


@app.on_message(filters.command(["queue", "playing", "cqueue", "cplaying"]) & filters.group & ~app.bl_users)
@lang.language()
async def _queue_func(_, m: types.Message):
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    # Check for channel play mode
    is_channel = m.command[0].lower() in ["cqueue", "cplaying"]
    chat_id = m.chat.id
    
    if is_channel:
        channel_id = await db.get_cmode(m.chat.id)
        if channel_id is None:
            return await m.reply_text("Channel play is not enabled. Use /channelplay to enable.")
        chat_id = channel_id
    
    if not await db.get_call(chat_id):
        return await m.reply_text("Nothing is playing.")

    _reply = await m.reply_text("Fetching queue...")
    _queue = queue.get_queue(chat_id)
    if not _queue:
        return await _reply.edit_text("Nothing is playing.")
        
    _media = _queue[0]
    _thumb = (
        await thumb.generate(_media)
        if isinstance(_media, Track)
        else config.DEFAULT_THUMB
    )
    _text = f"<b>Now Playing:</b>\n{_media.title}\n<b>Duration:</b> {_media.duration}\n<b>Requested by:</b> {_media.user}"
    
    _queue.pop(0)

    if _queue:
        _text += "\n\n<b>Upcoming:</b>"
        for i, media in enumerate(_queue, start=1):
            if i == 15:
                break
            _text += f"\n{i}. {media.title} (<code>{media.duration}</code>)"

    _playing = await db.playing(chat_id)
    await _reply.edit_media(
        media=types.InputMediaPhoto(
            media=_thumb,
            caption=_text,
        ),
        reply_markup=buttons.queue_markup(
            chat_id,
            "Playing" if _playing else "Paused",
            _playing,
        ),
    )
    
