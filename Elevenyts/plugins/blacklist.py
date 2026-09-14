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


# =====================================================
# CHAT BLACKLIST COMMANDS
# =====================================================

@app.on_message(filters.command(["blacklistchat"]) & app.sudo_filter)
@lang.language()
async def _blacklist_chat(_, m: types.Message):
    """Add chat to blacklist."""
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    if len(m.command) < 2:
        return await m.reply_text(
            "<blockquote><b>🚫 Blacklist Chat:</b>\n"
            "<code>/blacklistchat [chat_id]</code></blockquote>"
        )

    try:
        chat_id = int(m.command[1])
        chat = await app.get_chat(chat_id)
    except ValueError:
        return await m.reply_text("<blockquote>⚠️ Invalid chat ID</blockquote>")
    except Exception:
        return await m.reply_text("<blockquote>⚠️ Chat not found</blockquote>")

    if chat_id in db.blacklisted:
        return await m.reply_text(
            f"<blockquote>ℹ️ {chat.title} is already blacklisted</blockquote>"
        )

    await db.add_blacklist(chat_id)
    await m.reply_text(
        f"<blockquote><u><b>ℹ️ Chat Blacklisted Successfully!</b></u>\n\n"
        f"<b>Chat Name:</b> {chat.title}\n"
        f"<b>ID:</b> <code>{chat_id}</code></blockquote>"
    )


@app.on_message(filters.command(["whitelistchat", "unblacklistchat"]) & app.sudo_filter)
@lang.language()
async def _whitelist_chat(_, m: types.Message):
    """Remove chat from blacklist."""
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    if len(m.command) < 2:
        return await m.reply_text(
            "<blockquote><b>✅ Whitelist Chat:</b>\n"
            "<code>/whitelistchat [chat_id]</code></blockquote>"
        )

    try:
        chat_id = int(m.command[1])
        try:
            chat = await app.get_chat(chat_id)
            chat_name = chat.title
        except:
            chat_name = f"Chat {chat_id}"
    except ValueError:
        return await m.reply_text("<blockquote>⚠️ Invalid chat ID</blockquote>")

    if chat_id not in db.blacklisted:
        return await m.reply_text(
            f"<blockquote>ℹ️ {chat_name} is not blacklisted</blockquote>"
        )

    await db.del_blacklist(chat_id)
    await m.reply_text(
        f"<blockquote><u><b>ℹ️ Chat Whitelisted Successfully!</b></u>\n\n"
        f"<b>Chat Name:</b> {chat_name}\n"
        f"<b>ID:</b> <code>{chat_id}</code></blockquote>"
    )


@app.on_message(filters.command(["blacklistedchat", "blchats"]) & app.sudo_filter)
@lang.language()
async def _blacklisted_chats(_, m: types.Message):
    """Show all blacklisted chats."""
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    sent = await m.reply_text("🔄 Fetching blacklisted chats...")
    
    blacklisted = await db.get_blacklisted(chat=True)
    
    # Filter only chats (negative IDs)
    chats_list = [chat_id for chat_id in blacklisted if chat_id < 0]
    
    if not chats_list:
        return await sent.edit_text("<blockquote>ℹ️ No chats are blacklisted</blockquote>")
    
    text = "<u><b>🌐 Blacklisted Chats:</b></u>\n<blockquote>"
    
    for chat_id in chats_list:
        try:
            chat = await app.get_chat(chat_id)
            text += f"\n- {chat.title} ({chat_id})"
        except:
            text += f"\n- Unknown Chat ({chat_id})"
    
    text += "\n\n</blockquote>"
    await sent.edit_text(text)


# =====================================================
# USER BLACKLIST COMMANDS
# =====================================================

@app.on_message(filters.command(["block"]) & app.sudo_filter)
@lang.language()
async def _block_user(_, m: types.Message):
    """Block a user from using the bot."""
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    # Extract user from command or reply
    user_id = None
    
    if m.reply_to_message and m.reply_to_message.from_user:
        user_id = m.reply_to_message.from_user.id
        user_mention = m.reply_to_message.from_user.mention
    elif len(m.command) > 1:
        try:
            user_id = int(m.command[1])
            user = await app.get_users(user_id)
            user_mention = user.mention
        except ValueError:
            return await m.reply_text("<blockquote>⚠️ Invalid user ID</blockquote>")
        except Exception:
            return await m.reply_text("<blockquote>⚠️ User not found</blockquote>")
    else:
        return await m.reply_text(
            "<blockquote><b>🚫 Block User:</b>\n"
            "<code>/block [user_id]</code>\n"
            "<i>Or reply to user's message with /block</i></blockquote>"
        )
    
    # Don't allow blocking sudo users
    if user_id in app.sudoers:
        return await m.reply_text("<blockquote>⚠️ Cannot block sudo users</blockquote>")
    
    if user_id in app.bl_users:
        return await m.reply_text(
            f"<blockquote>ℹ️ {user_mention} is already blocked</blockquote>"
        )

    app.bl_users.add(user_id)
    await db.add_blacklist(user_id)
    await m.reply_text(
        f"<blockquote><u><b>ℹ️ User Blocked Successfully!</b></u>\n\n"
        f"<b>User:</b> {user_mention}\n"
        f"<b>ID:</b> <code>{user_id}</code></blockquote>"
    )


@app.on_message(filters.command(["unblock"]) & app.sudo_filter)
@lang.language()
async def _unblock_user(_, m: types.Message):
    """Unblock a user."""
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    # Extract user from command or reply
    user_id = None
    
    if m.reply_to_message and m.reply_to_message.from_user:
        user_id = m.reply_to_message.from_user.id
        user_mention = m.reply_to_message.from_user.mention
    elif len(m.command) > 1:
        try:
            user_id = int(m.command[1])
            user = await app.get_users(user_id)
            user_mention = user.mention
        except ValueError:
            return await m.reply_text("<blockquote>⚠️ Invalid user ID</blockquote>")
        except Exception:
            user_mention = f"User {user_id}"
    else:
        return await m.reply_text(
            "<blockquote><b>✅ Unblock User:</b>\n"
            "<code>/unblock [user_id]</code>\n"
            "<i>Or reply to user's message with /unblock</i></blockquote>"
        )
    
    if user_id not in app.bl_users:
        return await m.reply_text(
            f"<blockquote>ℹ️ {user_mention} is not blocked</blockquote>"
        )

    app.bl_users.discard(user_id)
    await db.del_blacklist(user_id)
    await m.reply_text(
        f"<blockquote><u><b>ℹ️ User Unblocked Successfully!</b></u>\n\n"
        f"<b>User:</b> {user_mention}\n"
        f"<b>ID:</b> <code>{user_id}</code></blockquote>"
    )


@app.on_message(filters.command(["blockedusers", "blusers"]) & app.sudo_filter)
@lang.language()
async def _blocked_users(_, m: types.Message):
    """Show all blocked users."""
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    sent = await m.reply_text("🔄 Fetching blocked users...")
    
    blacklisted = await db.get_blacklisted()
    
    if not blacklisted:
        return await sent.edit_text("<blockquote>ℹ️ No users are blocked</blockquote>")
    
    text = "<u><b>🚫 Blocked Users:</b></u>\n<blockquote>"
    
    for user_id in blacklisted:
        try:
            user = await app.get_users(user_id)
            text += f"\n- {user.mention} ({user_id})"
        except:
            text += f"\n- Deleted Account ({user_id})"
    
    text += "\n\n</blockquote>"
    await sent.edit_text(text)
        
