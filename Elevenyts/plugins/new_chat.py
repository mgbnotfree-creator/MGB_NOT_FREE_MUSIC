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
from pyrogram.errors import ChatAdminRequired, ChannelPrivate

from MGB_NOT_FREE_MUSIC import app, config


# ==========================================================
# 🟢 BOT ADDED IN GROUP
# ==========================================================
@app.on_message(filters.new_chat_members & filters.group)
async def new_net_member(_, message: types.Message):
    for member in message.new_chat_members:
        if member.id == app.id:
            chat = message.chat

            chat_name = chat.title
            chat_id = chat.id
            chat_username = f"@{chat.username}" if chat.username else "Private Group"

            try:
                members_count = await app.get_chat_members_count(chat_id)
            except (ChannelPrivate, Exception):
                members_count = "Unknown"

            added_by = message.from_user
            added_by_name = added_by.mention if added_by else "Unknown"

            # 🔗 LINK SYSTEM
            try:
                if chat.username:
                    chat_link = f"https://t.me/{chat.username}"
                else:
                    bot_member = await app.get_chat_member(chat_id, app.id)
                    if bot_member.privileges and bot_member.privileges.can_invite_users:
                        chat_link = await app.export_chat_invite_link(chat_id)
                    else:
                        chat_link = "No Invite Permission"
            except ChatAdminRequired:
                chat_link = "Bot is not Admin"
            except Exception:
                chat_link = "Unavailable"

            text = f"""<blockquote><b>➕ Bot Added in Group</b></blockquote>

<blockquote>
<b>📌 Title:</b> {chat_name}
<b>🆔 ID:</b> <code>{chat_id}</code>
<b>🌐 Username:</b> {chat_username}
<b>🔗 Link:</b> {chat_link}
<b>👥 Members:</b> {members_count}
<b>👤 Added By:</b> {added_by_name}
</blockquote>"""

            try:
                await app.send_photo(
                    chat_id=config.LOGGER_ID,
                    photo=config.START_IMG,
                    caption=text,
                )
            except Exception as e:
                print(f"Failed to send new chat notification: {e}")

            break


# ==========================================================
# 🔴 BOT REMOVED
# ==========================================================
@app.on_message(filters.left_chat_member & filters.group)
async def left_chat_member(_, message: types.Message):
    if message.left_chat_member.id == app.id:
        chat = message.chat

        chat_name = chat.title
        chat_id = chat.id
        chat_username = f"@{chat.username}" if chat.username else "Private Group"

        removed_by = message.from_user
        removed_by_name = removed_by.mention if removed_by else "Unknown"

        # 🔗 LINK
        try:
            if chat.username:
                chat_link = f"https://t.me/{chat.username}"
            else:
                bot_member = await app.get_chat_member(chat_id, app.id)
                if bot_member.privileges and bot_member.privileges.can_invite_users:
                    chat_link = await app.export_chat_invite_link(chat_id)
                else:
                    chat_link = "No Invite Permission"
        except Exception:
            chat_link = "Unavailable"

        text = f"""<blockquote><b>➖ Bot Removed from Group</b></blockquote>

<blockquote>
<b>📌 Title:</b> {chat_name}
<b>🆔 ID:</b> <code>{chat_id}</code>
<b>🌐 Username:</b> {chat_username}
<b>🔗 Link:</b> {chat_link}
<b>👤 Removed By:</b> {removed_by_name}
</blockquote>"""

        try:
            await app.send_photo(
                chat_id=config.LOGGER_ID,
                photo=config.START_IMG,
                caption=text,
            )
        except Exception as e:
            print(f"Failed to send left chat notification: {e}")


# ==========================================================
# 🔗 /LINK COMMAND (OWNER ONLY)
# ==========================================================
@app.on_message(filters.command("link") & filters.private)
async def get_group_link(_, message: types.Message):
    # OWNER CHECK
    if message.from_user.id != config.OWNER_ID:
        return await message.reply_text("⚠️ You are not authorized.")

    if len(message.command) < 2:
        return await message.reply_text("🚫 Usage:\n/link <group_id>")

    try:
        chat_id = int(message.command[1])
    except Exception:
        return await message.reply_text("⚠️ Invalid group ID")

    try:
        chat = await app.get_chat(chat_id)

        if chat.username:
            link = f"https://t.me/{chat.username}"
        else:
            bot_member = await app.get_chat_member(chat_id, app.id)
            if bot_member.privileges and bot_member.privileges.can_invite_users:
                link = await app.export_chat_invite_link(chat_id)
            else:
                return await message.reply_text("⚠️ No invite permission")

        await message.reply_text(
            f"🔗 <b>Group Link:</b>\n{link}",
            disable_web_page_preview=True,
        )

    except ChannelPrivate:
        return await message.reply_text("⚠️ Bot is not in that group")

    except ChatAdminRequired:
        return await message.reply_text("⚠️ Bot is not admin")

    except Exception as e:
        return await message.reply_text(f"⚠️ Error:\n{e}")
      
