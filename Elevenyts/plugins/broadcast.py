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

import os
import asyncio
from typing import List, Tuple

from pyrogram import enums, errors, filters, types

from Elevenyts import app, db, lang, config


# Global flag to track if a broadcast is currently running
broadcasting: bool = False

def _broadcast_buttons(bot_username: str | None):
    """Inline buttons applied to every broadcast delivery."""
    add_url = f"https://t.me/{bot_username}?startgroup=true" if bot_username else "https://t.me/"
    support_url = getattr(config, "SUPPORT_CHAT", None) or getattr(config, "SUPPORT_CHANNEL", None) or "https://t.me/"
    if support_url.startswith("@"):
        support_url = f"https://t.me/{support_url[1:]}"
    return types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("➕ Add Me To Your Group", url=add_url)],
        [types.InlineKeyboardButton("💬 Support Chat", url=support_url)],
    ])


@app.on_message(filters.command(["broadcast"]) & app.sudo_filter)
@lang.language()
async def broadcast_message(_, message: types.Message) -> None:
    """
    Broadcast a message to all groups and/or users.

    Usage:
        /broadcast <reply to message> - Send message to all groups (as copy)
        /broadcast <text> - Send text to all groups
        /broadcast -user <reply to message> - Send to all groups and users
        /broadcast -nochat -user <message> - Send only to users
    """
    # Auto-delete command message
    try:
        await message.delete()
    except Exception:
        pass
    
    global broadcasting

    # Check if another broadcast is already running
    if broadcasting:
        return await message.reply_text(message.lang["gcast_active"])

    # Determine if the command was a reply to a media message
    media_message = None
    media_group = None
    if message.reply_to_message:
        media_message = message.reply_to_message
        
        # Check if it's part of a media group (album)
        if media_message.media_group_id:
            try:
                media_group = await _get_media_group(message.chat.id, media_message)
            except Exception:
                pass

    # Parse command: extract flags and actual message
    flags, broadcast_text = _parse_broadcast_command(message.text)

    # Validate: either text or media must be present
    if not broadcast_text and not media_message:
        return await message.reply_text(message.lang["gcast_usage"])

    # Determine recipients based on flags
    groups, users = await _get_broadcast_recipients(flags)
    all_chats = groups + users

    if not all_chats:
        return await message.reply_text(
            "⚠️ No recipients found. Make sure the bot is added to groups or has users."
        )

    # Set broadcasting flag
    broadcasting = True
    sent = await message.reply_text(message.lang["gcast_start"])

    # Log broadcast initiation
    await _log_broadcast_start(message)
    await asyncio.sleep(5)

    # Perform the broadcast (supports text and media messages)
    success_groups, success_users, failed_chats = await _send_broadcast(
        broadcast_text, groups, users, sent, media_message, flags, message.lang, media_group
    )

    # Reset broadcasting flag
    broadcasting = False

    # Send completion message
    await _send_broadcast_completion(
        message, sent, success_groups, success_users, failed_chats, media_message
    )


@app.on_message(filters.command(["stop_gcast", "stop_broadcast"]) & app.sudo_filter)
@lang.language()
async def stop_broadcast(_, message: types.Message) -> None:
    """Stop an ongoing broadcast operation."""
    # Auto-delete command message
    try:
        await message.delete()
    except Exception:
        pass
    
    global broadcasting

    if not broadcasting:
        return await message.reply_text(message.lang["gcast_inactive"])

    broadcasting = False

    # Log broadcast stop
    try:
        log_msg = await app.send_message(
            chat_id=app.logger,
            text=message.lang["gcast_stop_log"].format(
                message.from_user.id,
                message.from_user.mention
            )
        )
        await log_msg.pin(disable_notification=False)
    except Exception:
        pass

    await message.reply_text(message.lang["gcast_stop"])


async def _get_media_group(chat_id: int, message: types.Message) -> List[types.Message] | None:
    """Get all messages in a media group (album)."""
    if not message.media_group_id:
        return None

    media_group_id = message.media_group_id
    messages = []
    search_range = 20

    try:
        start_id = max(1, message.id - search_range)
        end_id = message.id + search_range
        
        for msg_id in range(start_id, end_id + 1):
            try:
                msg = await app.get_messages(chat_id, msg_id)
                if msg and hasattr(msg, 'media_group_id') and msg.media_group_id == media_group_id:
                    messages.append(msg)
            except Exception:
                continue
                
        messages.sort(key=lambda x: x.id)
        return messages if messages else None
    except Exception:
        return None


def _parse_broadcast_command(text: str) -> Tuple[List[str], str]:
    """Parse broadcast command to extract flags and message."""
    if not text:
        return [], ""

    parts = text.split(None, 1)
    if len(parts) < 2:
        return [], ""

    remaining_text = parts[1]
    flags = []
    lines = remaining_text.split('\n')
    first_line_parts = lines[0].split()

    message_start_index = 0
    for i, part in enumerate(first_line_parts):
        if part.startswith('-'):
            flags.append(part)
            message_start_index = i + 1
        else:
            break

    if message_start_index > 0:
        first_line_without_flags = ' '.join(first_line_parts[message_start_index:])
        if len(lines) > 1:
            message_text = first_line_without_flags + '\n' + '\n'.join(lines[1:])
        else:
            message_text = first_line_without_flags
    else:
            message_text = remaining_text

    return flags, message_text.strip()


async def _get_broadcast_recipients(flags: List[str]) -> Tuple[List[int], List[int]]:
    """Get list of groups and users to broadcast to based on flags."""
    groups = []
    users = []

    if "-nochat" not in flags:
        groups = await db.get_chats()

    if "-user" in flags:
        users = await db.get_users()

    return groups, users


async def _log_broadcast_start(message: types.Message) -> None:
    """Log broadcast initiation to logger group."""
    try:
        log_message = await app.send_message(
            chat_id=app.logger,
            text=message.lang["gcast_log"].format(
                message.from_user.id,
                message.from_user.mention,
                message.text,
            )
        )
        await log_message.pin(disable_notification=False)
    except errors.FloodWait as fw:
        await asyncio.sleep(fw.value + 1)
        log_message = await app.send_message(
            chat_id=app.logger,
            text=message.lang["gcast_log"].format(
                message.from_user.id,
                message.from_user.mention,
                message.text,
            )
        )
        try:
            await log_message.pin(disable_notification=False)
        except Exception:
            pass


async def _send_broadcast(
    text: str,
    groups: List[int],
    users: List[int],
    status_message: types.Message,
    media_message: types.Message | None = None,
    flags: List[str] = None,
    lang: dict = None,
    media_group: List[types.Message] = None,
) -> Tuple[int, int, str]:
    """Send broadcast message to all recipients."""
    global broadcasting

    if flags is None:
        flags = []

    success_groups = 0
    success_users = 0
    failed_log = ""
    pinned_count = 0
    all_chats = groups + users
    total_chats = len(all_chats)

    for index, chat_id in enumerate(all_chats, start=1):
        if not broadcasting:
            await status_message.edit_text(
                lang["gcast_stopped"].format(success_groups, success_users)
            )
            break

        if index % 50 == 0:
            try:
                await status_message.edit_text(
                    f"📢 <b>Broadcasting...</b>\n\n"
                    f"Progress: {index}/{total_chats}\n"
                    f"✅ Groups: {success_groups}\n"
                    f"✅ Users: {success_users}"
                )
            except Exception:
                pass

        try:
            if chat_id in groups:
                try:
                    chat = await app.get_chat(chat_id)
                    if chat.type == enums.ChatType.CHANNEL:
                        failed_log += f"{chat_id} - Skipped (channel, not a group)\n"
                        continue
                except Exception:
                    pass

            if media_group:
                sent_message = None
                try:
                    media_list = []
                    for idx, msg in enumerate(media_group):
                        caption = text if (idx == 0 and text) else (msg.caption if idx == 0 else None)
                        if msg.photo:
                            file_id = msg.photo.file_id if hasattr(msg.photo, 'file_id') else msg.photo[-1].file_id
                            media_list.append(types.InputMediaPhoto(media=file_id, caption=caption))
                        elif getattr(msg, 'video', None):
                            media_list.append(types.InputMediaVideo(media=msg.video.file_id, caption=caption))
                        elif getattr(msg, 'audio', None):
                            media_list.append(types.InputMediaAudio(media=msg.audio.file_id, caption=caption))
                        elif getattr(msg, 'document', None):
                            media_list.append(types.InputMediaDocument(media=msg.document.file_id, caption=caption))
                    
                    if media_list:
                        sent_messages = await app.send_media_group(chat_id=chat_id, media=media_list)
                        sent_message = sent_messages[0] if sent_messages else None
                        await app.send_message(
                            chat_id=chat_id,
                            text="🔗",
                            reply_markup=_broadcast_buttons(getattr(app, "username", None))
                        )
                        if sent_message and chat_id in groups:
                            if "-pin" in flags:
                                try:
                                    await sent_message.pin(disable_notification=True)
                                    pinned_count += 1
                                except Exception:
                                    pass
                            elif "-pinloud" in flags:
                                try:
                                    await sent_message.pin(disable_notification=False)
                                    pinned_count += 1
                                except Exception:
                                    pass
                    else:
                        failed_log += f"{chat_id} - No valid media in group\n"
                        await asyncio.sleep(0.3)
                        continue
                except Exception as mg_ex:
                    failed_log += f"{chat_id} - Media group send failed: {type(mg_ex).__name__}: {str(mg_ex)}\n"
                    await asyncio.sleep(0.3)
                    continue

            elif media_message:
                sent_message = None
                caption = text if text else (media_message.caption or "")
                caption_entities = None if text else (media_message.caption_entities or None)

                try:
                    if media_message.photo:
                        file_id = media_message.photo.file_id if hasattr(media_message.photo, 'file_id') else media_message.photo[-1].file_id
                        sent_message = await app.send_photo(
                            chat_id=chat_id, photo=file_id, caption=caption,
                            caption_entities=caption_entities,
                            reply_markup=_broadcast_buttons(getattr(app, "username", None))
                        )
                    elif getattr(media_message, 'video', None):
                        sent_message = await app.send_video(
                            chat_id=chat_id, video=media_message.video.file_id, caption=caption,
                            caption_entities=caption_entities,
                            reply_markup=_broadcast_buttons(getattr(app, "username", None))
                        )
                    elif getattr(media_message, 'audio', None):
                        sent_message = await app.send_audio(
                            chat_id=chat_id, audio=media_message.audio.file_id, caption=caption,
                            caption_entities=caption_entities,
                            reply_markup=_broadcast_buttons(getattr(app, "username", None))
                        )
                    elif getattr(media_message, 'voice', None):
                        sent_message = await app.send_voice(
                            chat_id=chat_id, voice=media_message.voice.file_id, caption=caption,
                            caption_entities=caption_entities,
                            reply_markup=_broadcast_buttons(getattr(app, "username", None))
                        )
                    elif getattr(media_message, 'document', None):
                        sent_message = await app.send_document(
                            chat_id=chat_id, document=media_message.document.file_id, caption=caption,
                            caption_entities=caption_entities,
                            reply_markup=_broadcast_buttons(getattr(app, "username", None))
                        )
                    elif getattr(media_message, 'animation', None):
                        sent_message = await app.send_animation(
                            chat_id=chat_id, animation=media_message.animation.file_id, caption=caption,
                            caption_entities=caption_entities,
                            reply_markup=_broadcast_buttons(getattr(app, "username", None))
                        )
                    elif getattr(media_message, 'sticker', None):
                        sent_message = await app.send_sticker(
                            chat_id=chat_id, sticker=media_message.sticker.file_id,
                            reply_markup=_broadcast_buttons(getattr(app, "username", None))
                        )
                    else:
                        msg_text = text if text else (media_message.text or media_message.caption or "")
                        msg_entities = None if text else (media_message.entities or media_message.caption_entities or None)
                        if msg_text:
                            sent_message = await app.send_message(
                                chat_id, msg_text, entities=msg_entities,
                                reply_markup=_broadcast_buttons(getattr(app, "username", None))
                            )
                        else:
                            failed_log += f"{chat_id} - Empty message\n"
                            await asyncio.sleep(0.3)
                            continue

                    if sent_message and chat_id in groups:
                        if "-pin" in flags:
                            try:
                                await sent_message.pin(disable_notification=True)
                                pinned_count += 1
                            except Exception:
                                pass
                        elif "-pinloud" in flags:
                            try:
                                await sent_message.pin(disable_notification=False)
                                pinned_count += 1
                            except Exception:
                                pass
                except Exception as send_ex:
                    failed_log += f"{chat_id} - Media send failed: {type(send_ex).__name__}: {str(send_ex)}\n"
                    await asyncio.sleep(0.3)
                    continue
            else:
                sent_message = await app.send_message(
                    chat_id, text,
                    reply_markup=_broadcast_buttons(getattr(app, "username", None))
                )
                if sent_message and chat_id in groups:
                    if "-pin" in flags:
                        try:
                            await sent_message.pin(disable_notification=True)
                            pinned_count += 1
                        except Exception:
                            pass
                    elif "-pinloud" in flags:
                        try:
                            await sent_message.pin(disable_notification=False)
                            pinned_count += 1
                        except Exception:
                            pass

            if chat_id in groups:
                success_groups += 1
            else:
                success_users += 1

            await asyncio.sleep(0.3)

        except errors.FloodWait as fw:
            try:
                await status_message.edit_text(
                    f"⏳ Flood wait triggered. Waiting {fw.value} seconds...\n\n"
                    f"Progress: {index}/{total_chats}\n"
                    f"Don't worry, broadcast will continue!"
                )
            except Exception:
                pass
            await asyncio.sleep(fw.value + 5)
        except errors.UserIsBlocked:
            failed_log += f"{chat_id} - User blocked bot\n"
            continue
        except errors.ChatWriteForbidden:
            failed_log += f"{chat_id} - No write permission\n"
            continue
        except errors.ChannelPrivate:
            if chat_id in groups:
                try:
                    await db.rm_chat(chat_id)
                except Exception:
                    pass
            failed_log += f"{chat_id} - Channel private\n"
            continue
        except errors.PeerIdInvalid:
            if chat_id in groups:
                try:
                    await db.rm_chat(chat_id)
                except Exception:
                    pass
            failed_log += f"{chat_id} - Invalid ID (cleaned from database)\n"
            continue
        except Exception as ex:
            failed_log += f"{chat_id} - {type(ex).__name__}: {str(ex)}\n"
            continue

    return success_groups, success_users, failed_log


async def _send_broadcast_completion(
    message: types.Message,
    status_message: types.Message,
    success_groups: int,
    success_users: int,
    failed_log: str,
    media_message: types.Message | None = None,
) -> None:
    """Send broadcast completion message with results."""
    media_type = "text"
    if media_message:
        if media_message.photo:
            media_type = "photo"
        elif getattr(media_message, 'video', None):
            media_type = "video"
        elif getattr(media_message, 'audio', None):
            media_type = "audio"
        elif getattr(media_message, 'document', None):
            media_type = "document"
                
