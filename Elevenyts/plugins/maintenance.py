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

from Elevenyts import app, db, lang


@app.on_message(filters.command(["maintenance"]) & app.sudo_filter)
@lang.language()
async def _maintenance(_, m: types.Message):
    """Toggle or check maintenance mode status."""
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    # If no argument, show current status
    if len(m.command) < 2:
        status = await db.get_maintenance()
        status_text = "Enabled 🟢" if status else "Disabled 🔴"
        
        await m.reply_text(
            f"<blockquote><u><b>🛠️ Maintenance Mode Status</b></u>\n\n"
            f"<b>Current Status:</b> {status_text}\n\n"
            f"<b>Commands:</b>\n"
            f"<code>/maintenance enable</code> - Enable mode\n"
            f"<code>/maintenance disable</code> - Disable mode</blockquote>"
        )
        return
    
    mode = m.command[1].lower()
    
    if mode in ["enable", "on", "1", "true"]:
        await db.set_maintenance(True)
        await m.reply_text(
            "<blockquote><u><b>🛠️ Maintenance Mode Enabled</b></u>\n\n"
            "The bot has been put into maintenance mode. Only sudo users can use commands.\n"
            "Regular users will be notified that the bot is under maintenance.</blockquote>"
        )
        
    elif mode in ["disable", "off", "0", "false"]:
        await db.set_maintenance(False)
        await m.reply_text(
            "<blockquote><u><b>🛠️ Maintenance Mode Disabled</b></u>\n\n"
            "The bot is now online and available for all users.</blockquote>"
        )
        
    else:
        await m.reply_text(
            "<blockquote>⚠️ <b>Invalid maintenance mode argument</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/maintenance enable</code>\n"
            "<code>/maintenance disable</code></blockquote>"
        )
        
