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

import re
from pyrogram import filters, types, enums

from MGB_NOT_FREE_MUSIC import app, config


# Pattern to detect admin triggers
TRIGGER_PATTERN = re.compile(r"(?i)([.@]|\/)admin")


@app.on_message(filters.group & filters.regex(r"(?i)([.@]|\/)admin"))
async def mention_admins(_, message: types.Message):
    """
    Mention all group admins when someone types @admin, .admin, or /admin
    """
    try:
        # Extract the message without the trigger
        message_text = message.text or message.caption or ""
        cleaned_text = TRIGGER_PATTERN.sub("", message_text).strip()

        # Get user info (handle anonymous admins)
        sender = message.from_user
        if sender:
            user_display = f"{sender.first_name}"
            if sender.username:
                user_display += f" (@{sender.username})"
        else:
            user_display = "Anonymous Admin / Channel"

        # Build formatted reply message
        if cleaned_text:
            reply_msg = (
                f"<blockquote><b><i>\"{cleaned_text}\"</i></b></blockquote>\n"
                f"<b>Requested by: {user_display} 🔔</b>\n\n"
            )
        else:
            reply_msg = (
                f"<blockquote><b>Requested by: {user_display} 🔔</b>\n\n</blockquote>"
            )

        # Get all administrators
        mentions = []
        try:
            async for admin in app.get_chat_members(
                message.chat.id,
                filter=enums.ChatMembersFilter.ADMINISTRATORS,
            ):
                user = admin.user

                # Skip bots and deleted accounts
                if user.is_bot or user.is_deleted:
                    continue

                # Skip admins who have "Remain Anonymous" enabled
                if hasattr(admin, 'privileges') and admin.privileges:
                    if getattr(admin.privileges, 'is_anonymous', False):
                        continue

                # Skip usernames in the excluded list
                if user.username and user.username.lower() in [u.lower() for u in config.EXCLUDED_USERNAMES]:
                    continue

                # Add mention
                if user.username:
                    mentions.append(f"@{user.username}")
                else:
                    mentions.append(
                        f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
                    )
        except Exception:
            await message.reply_text(
                "<blockquote>⚠️ Failed to fetch administrators. Make sure the bot has proper permissions.</blockquote>"
            )
            return

        if mentions:
            reply_msg += ", ".join(mentions)
        else:
            reply_msg += "<i>No visible human admins found to mention.</i>"

        # Send the reply
        try:
            await message.reply_text(reply_msg, disable_web_page_preview=True)
        except Exception:
            await message.reply_text(
                "<blockquote>⚠️ Failed to send admin notification.</blockquote>"
            )
    except Exception:
        # Catch all exceptions to prevent bot crashes
        try:
            await message.reply_text("<blockquote>⚠️ An error occurred while processing admin mention.</blockquote>")
        except:
            pass  # Silent failure if reply fails
