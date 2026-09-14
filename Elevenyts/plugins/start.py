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

import asyncio
import random

from pyrogram import enums, errors, filters, types

from MGB_NOT_FREE_MUSIC import app, config, db, lang, queue
from MGB_NOT_FREE_MUSIC.helpers import buttons, utils


# -------------------------------------------------------------------------
# Emoji Rain – individual drops one by one
# Only confirmed valid Telegram reaction emojis
# -------------------------------------------------------------------------
RAIN_EMOJIS = ["❤️‍🔥", "⚡", "🔥", "❤️‍🔥⚡", "❤️‍🩹", "🎉", "🕊️", "⭐", "🪄", "👑", "💎"]

# Stylish loading bar frames
_LOAD_FRAMES = [
    "<b>✨ Initializing module...</b>\n<blockquote expandable>🤖 Setting up Telegram Music Bot channels and configurations</blockquote>\n<code>▒▒▒▒▒▒▒▒▒▒</code>",
    "<b>⚡ Loading database...</b>\n<blockquote expandable>🤖 Setting up Telegram Music Bot channels and configurations</blockquote>\n<code>███▒▒▒▒▒▒▒</code>",
    "<b>🔥 Connecting APIs...</b>\n<blockquote expandable>🤖 Setting up Telegram Music Bot channels and configurations</blockquote>\n<code>██████▒▒▒▒</code>",
    "<b>⏳ Almost ready...</b>\n<blockquote expandable>🤖 Setting up Telegram Music Bot channels and configurations</blockquote>\n<code>████████▒▒</code>",
    "<b>🌟 System ready!</b>\n<blockquote expandable>💥 Launching Telegram Music Bot interface...</blockquote>\n<code>██████████</code>",
    "<b>🚀 Welcome!</b>\n<blockquote expandable>✨ Let's play some music!</blockquote>\n<code>██████████</code>",
]


async def _emoji_rain(message: types.Message):
    """Random big reaction on /start message — 2s → clear."""
    emoji = random.choice(RAIN_EMOJIS)
    try:
        await app.send_reaction(
            chat_id=message.chat.id,
            message_id=message.id,
            emoji=emoji,
            big=True,
        )
    except Exception as e:
        print(f"[REACTION ERROR] {e}")
    await asyncio.sleep(2.0)
    try:
        await app.send_reaction(
            chat_id=message.chat.id,
            message_id=message.id,
            emoji=None,
        )
    except Exception:
        pass


async def _loading_animation(message: types.Message):
    """Stylish animated loading bar — auto-deletes when done."""
    try:
        msg = await message.reply_text(_LOAD_FRAMES[0])
        for frame in _LOAD_FRAMES[1:]:
            await asyncio.sleep(0.4)
            try:
                await msg.edit_text(frame)
            except Exception:
                break
        await asyncio.sleep(0.5)
        await msg.delete()
    except Exception:
        pass


@app.on_message(filters.sticker & filters.private)
async def _get_sticker_id(_, message: types.Message):
    """Reply with sticker file_id so owner can set STICKER_ID."""
    if message.from_user and message.from_user.id == app.owner:
        fid = message.sticker.file_id
        await message.reply_text(
            f"📌 Sticker file_id:\n<code>{fid}</code>\n\n"
            f"Isko STICKER_ID mein set karo."
        )


@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    """Handle /help command in private chats – shows help menu with image."""
    try:
        await m.delete()
    except Exception:
        pass

    try:
        await m.reply_photo(
            photo=config.START_IMG,
            caption=m.lang["help_menu"],
            reply_markup=buttons.help_markup(m.lang),
            quote=True,
        )
    except Exception:
        await m.reply_text(
            text=m.lang["help_menu"],
            reply_markup=buttons.help_markup(m.lang),
            quote=True,
        )


@app.on_message(filters.command(["start"]))
@lang.language()
async def start(_, message: types.Message):
    """
    Handle /start command.

    Private DM sequence:
      1. Emoji rain (awaited – drops appear one by one, then disappear)
      2. Sticker (animates for 1s)
      3. Welcome photo + caption + buttons
      4. ❤️‍🔥 reaction on welcome photo
    """
    if message.chat.type != enums.ChatType.PRIVATE:
        try:
            await message.delete()
        except Exception:
            pass

    if not message.from_user:
        return

    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(message.lang["bl_user_notify"])

    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    private = message.chat.type == enums.ChatType.PRIVATE

    if private:
        # Step 1: Emoji reaction blast
        await _emoji_rain(message)

        # Step 2: Stylish loading animation
        await _loading_animation(message)

        # Step 3: Sticker -> animate -> delete
        if config.STICKER_ID and config.STICKER_ID.strip():
            try:
                sticker_msg = await app.send_sticker(
                    chat_id=message.chat.id,
                    sticker=config.STICKER_ID,
                )
                await asyncio.sleep(2.5)
                await sticker_msg.delete()
            except Exception as e:
                print(f"[STICKER ERROR] {e}")

    # Step 3/4: Welcome photo
    _text = (
        message.lang["start_pm"].format(message.from_user.first_name, app.name)
        if private
        else message.lang["start_gp"].format(app.name)
    )
    key = buttons.start_key(message.lang, private)

    sent = None
    try:
        sent = await message.reply_photo(
            photo=config.START_IMG,
            caption=_text,
            reply_markup=key,
            quote=not private,
        )
    except errors.ChatSendPhotosForbidden:
        try:
            sent = await message.reply_text(
                text=_text,
                reply_markup=key,
                quote=not private,
            )
        except Exception:
            pass
    except Exception:
        pass

    # Step 4: ❤️‍🔥 reaction on welcome message
    if private and sent:
        try:
            await app.send_reaction(
                chat_id=message.chat.id,
                message_id=sent.id,
                emoji="❤️‍🔥",
            )
        except Exception:
            pass

    if private:
        if await db.is_user(message.from_user.id):
            return
        await utils.send_log(message)
        return await db.add_user(message.from_user.id)


@app.on_message(filters.command(["playmode", "settings"]) & filters.group & ~app.bl_users)
@lang.language()
async def settings(_, message: types.Message):
    """Handle /playmode or /settings command – show group settings."""
    try:
        await message.delete()
    except Exception:
        pass

    admin_only = await db.get_play_mode(message.chat.id)
    force_admin = await db.get_force_mode(message.chat.id)
    _language = "en"
    await utils.safe_text(
        message,
        message.lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(
            message.lang, admin_only, force_admin, _language, message.chat.id
        ),
        quote=True,
    )


@app.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(_, message: types.Message):
    """Handle new member events – detect when bot is added to groups."""
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    for member in message.new_chat_members:
        if member.id == app.id:
            if await db.is_chat(message.chat.id):
                return
            await db.add_chat(message.chat.id)
