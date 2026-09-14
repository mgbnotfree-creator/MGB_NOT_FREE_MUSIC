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

from Elevenyts import app, db


@app.on_message(
    filters.command(["autoleave"])
    & filters.group
    & ~app.bl_users
)
async def autoleave_command(_, m: Message) -> None:
    """Handle /autoleave enable or /autoleave disable command."""
    
    # Check if user is sudo user
    if m.from_user.id not in app.sudoers:
        return await m.reply_text(
            "<blockquote>⚠️ <b>Access Denied:</b> This command is restricted to Sudo users only.</blockquote>"
        )
    
    # Check if subcommand is provided
    if len(m.command) < 2:
        current_status = await db.get_autoleave(m.chat.id)
        status_text = "Enabled ✅" if current_status else "Disabled ❌"
        return await m.reply_text(
            f"<blockquote><b>🤖 Auto-Leave Status:</b> {status_text}</blockquote>\n\n"
            f"<blockquote><b>Available Subcommands:</b>\n"
            f"• <code>/autoleave enable</code> - Enable auto-leave feature\n"
            f"• <code>/autoleave disable</code> - Disable auto-leave feature</blockquote>\n\n"
            f"<blockquote><i>Note: When enabled, the assistant will automatically leave empty voice chats after 5 minutes of inactivity.</i></blockquote>"
        )
    
    subcommand = m.command[1].lower()
    
    subcommand = m.command[1].lower()
    
    if subcommand == "enable":
        await db.set_autoleave(m.chat.id, True)
        await m.reply_text(
            "ℹ️ <blockquote><b>Auto-Leave has been ENABLED!</b></blockquote>\n\n"
            "<blockquote>The assistant bot will now automatically leave the voice chat after <b>5 minutes</b> of inactivity.</blockquote>"
        )
    elif subcommand == "disable":
        await db.set_autoleave(m.chat.id, False)
        await m.reply_text(
            "ℹ️ <blockquote><b>Auto-Leave has been DISABLED!</b></blockquote>\n\n"
            "<blockquote>The assistant bot will remain in the voice chat even if playback is paused or empty.</blockquote>"
        )
    else:
        await m.reply_text(
            "⚠️ <blockquote>Invalid subcommand provided!</blockquote>\n\n"
            "<blockquote><b>Available Subcommands:</b>\n"
            "• <code>/autoleave enable</code>\n"
            "• <code>/autoleave disable</code></blockquote>"
        )
        
