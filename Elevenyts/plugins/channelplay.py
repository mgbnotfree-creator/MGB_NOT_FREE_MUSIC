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
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus, ChatType
from pyrogram.types import Message

from MGB_NOT_FREE_MUSIC import app, config, db


@app.on_message(filters.command(["channelplay"]) & filters.group & ~app.bl_users)
async def channelplay_command(_, m: Message):
    """Enable or disable channel play mode."""
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    # Check if from_user exists (not sent by channel/anonymous admin)
    if not m.from_user:
        return await m.reply_text("⚠️ This command cannot be used by anonymous admins or channels.")
    
    # Check if user is admin
    member = await app.get_chat_member(m.chat.id, m.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return await m.reply_text("⚠️ You must be an admin or owner of the group to use this command.")

    if len(m.command) < 2:
        return await m.reply_text(
            f"<blockquote><b>📢 Channel Play Settings for {m.chat.title}</b>\n\n"
            "<b>Usage:</b>\n"
            "• <code>/channelplay linked</code> - Connect to linked channel\n"
            "• <code>/channelplay [channel_id]</code> - Connect to specific channel ID/username\n"
            "• <code>/channelplay disable</code> - Disable channel play</blockquote>"
        )

    query = m.text.split(None, 1)[1].strip()

    # Disable channel play
    if query.lower() == "disable":
        await db.set_cmode(m.chat.id, None)
        return await m.reply_text("ℹ️ Channel play mode has been disabled for this group.")

    # Enable for linked channel
    elif query.lower() == "linked":
        chat = await app.get_chat(m.chat.id)
        if chat.linked_chat:
            channel_id = chat.linked_chat.id
            await db.set_cmode(m.chat.id, channel_id)
            return await m.reply_text(
                f"ℹ️ Channel play mode enabled for linked channel:\n"
                f"<b>Title:</b> {chat.linked_chat.title}\n"
                f"<b>ID:</b> <code>{chat.linked_chat.id}</code>"
            )
        else:
            return await m.reply_text("⚠️ This group does not have a linked channel.")

    # Enable for specific channel
    else:
        if query.lstrip("-").isdigit():
            channel_id = int(query)
        else:
            channel_id = query  # Username or invite link

        try:
            chat = await app.get_chat(channel_id)
        except Exception as e:
            return await m.reply_text(
                f"⚠️ Failed to get channel:\n"
                f"<b>Error:</b> <code>{type(e).__name__}</code>\n\n"
                "Make sure the bot is added as an administrator in the target channel."
            )

        if chat.type != ChatType.CHANNEL:
            return await m.reply_text("⚠️ The provided ID/username does not belong to a channel.")

        # Check if user is owner of the channel
        owner_username = None
        owner_id = None
        try:
            async for user in app.get_chat_members(
                chat.id, filter=ChatMembersFilter.ADMINISTRATORS
            ):
                if user.status == ChatMemberStatus.OWNER:
                    owner_username = user.user.username or "Unknown"
                    owner_id = user.user.id
                    break
        except Exception as e:
            return await m.reply_text(f"⚠️ Error checking channel owner: {e}")

        if not owner_id:
            return await m.reply_text("⚠️ Could not verify the owner of this channel.")

        if owner_id != m.from_user.id:
            return await m.reply_text(
                f"⚠️ You must be the owner of the channel <b>{chat.title}</b> to link it here.\n"
                f"<b>Channel Owner:</b> @{owner_username}"
            )

        await db.set_cmode(m.chat.id, chat.id)
        return await m.reply_text(
            f"ℹ️ Channel play mode enabled!\n"
            f"<b>Channel:</b> {chat.title}\n"
            f"<b>ID:</b> <code>{chat.id}</code>"
  )
          
