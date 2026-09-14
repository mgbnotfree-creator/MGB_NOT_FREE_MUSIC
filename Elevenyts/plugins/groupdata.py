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

from pyrogram import Client, filters
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus, ChatType, ParseMode
from pyrogram.types import Message

from Elevenyts import app


@app.on_message(filters.command(["groupdata", "chatinfo", "groupinfo"]) & filters.group)
async def group_data_handler(client: Client, message: Message):
    """Display comprehensive information about the current group"""
    # Auto-delete command message
    try:
        await message.delete()
    except Exception:
        pass
    
    chat = message.chat
    chat_id = chat.id
    
    try:
        # Get chat information
        chat_info = await client.get_chat(chat_id)
        
        # Count members by type
        total_members = 0
        admin_count = 0
        bot_count = 0
        banned_count = 0
        deleted_count = 0
        premium_count = 0
        
        try:
            total_members = await client.get_chat_members_count(chat_id)
            
            # Count admins
            async for member in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
                admin_count += 1
            
            # Count bots
            async for _ in client.get_chat_members(chat_id, filter=ChatMembersFilter.BOTS):
                bot_count += 1
                
            # Count banned users
            try:
                async for _ in client.get_chat_members(chat_id, filter=ChatMembersFilter.BANNED):
                    banned_count += 1
            except Exception:
                pass
            
            # Iterate through recent members to count deleted accounts and premium users
            try:
                async for member in client.get_chat_members(chat_id, filter=ChatMembersFilter.SEARCH, limit=200):
                    if member.user.is_deleted:
                        deleted_count += 1
                    if member.user.is_premium:
                        premium_count += 1
            except Exception:
                pass
                
        except Exception:
            pass
        
        # Build information text
        info_lines = []
        info_lines.append("<b>🛡️ GROUP INFORMATION</b>\n")
        
        # Basic info
        info_lines.append(f"<b>📌 Title:</b> {chat_info.title}")
        info_lines.append(f"<b>🆔 ID:</b> <code>{chat_id}</code>")
        
        if chat_info.username:
            info_lines.append(f"<b>🌐 Username:</b> @{chat_info.username}")
        
        # Chat type
        chat_type_str = "Supergroup" if chat.type == ChatType.SUPERGROUP else "Group"
        info_lines.append(f"<b>ℹ️ Type:</b> {chat_type_str}")
        
        # Member statistics
        info_lines.append(f"\n<b>👥 Total Members:</b> {total_members}")
        info_lines.append(f"<b>🛡️ Administrators:</b> {admin_count}")
        info_lines.append(f"<b>🤖 Bots:</b> {bot_count}")
        
        if banned_count > 0:
            info_lines.append(f"<b>🚫 Banned Users:</b> {banned_count}")
        
        if deleted_count > 0:
            info_lines.append(f"<b>🗑️ Deleted Accounts:</b> {deleted_count}")
            
        if premium_count > 0:
            info_lines.append(f"<b>⭐ Telegram Premium Users:</b> {premium_count}")
        
        # Description if available
        if chat_info.description:
            desc = chat_info.description
            if len(desc) > 100:
                desc = desc[:100] + "..."
            info_lines.append(f"\n<b>📝 Description:</b>\n{desc}")
        
        # Linked chat if available
        if chat_info.linked_chat:
            info_lines.append(f"\n<b>🔗 Linked Channel:</b> {chat_info.linked_chat.title}")
            info_lines.append(f"<b>🆔 Linked Channel ID:</b> <code>{chat_info.linked_chat.id}</code>")
        
        # Invite link if available
        if hasattr(chat_info, 'invite_link') and chat_info.invite_link:
            info_lines.append(f"\n<b>🔗 Invite Link:</b> {chat_info.invite_link}")
        
        # Check user's admin status
        try:
            user_member = await client.get_chat_member(chat_id, message.from_user.id)
            if user_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                role = 'Owner' if user_member.status == ChatMemberStatus.OWNER else 'Admin'
                info_lines.append(f"\n<b>👑 Your Role:</b> {role}")
        except Exception:
            pass
        
        # Combine all info
        response = "<blockquote>" + "\n".join(info_lines) + "</blockquote>"
        
        await message.reply_text(
            response,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        
    except Exception as e:
        await message.reply_text(
            f"<blockquote>❌ <b>Failed to fetch group info:</b>\n<code>{str(e)}</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        
