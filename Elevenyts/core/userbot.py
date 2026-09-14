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
from pyrogram import Client

from MGB_NOT_FREE_MUSIC import config, logger


class Userbot(Client):
    def __init__(self):
        """
        Initialize userbot with multiple assistant clients.

        Creates up to 3 assistant clients based on available session strings.
        Each assistant can independently join voice chats and stream music.
        More assistants = ability to serve more groups simultaneously.
        """
        self.clients = []  # List to store all active assistant clients

        # Map of client names to their session string config keys
        clients = {"one": "SESSION1", "two": "SESSION2", "three": "SESSION3"}

        # Create a Pyrogram client for each configured session
        for key, string_key in clients.items():
            # Unique name: MGB_NOT_FREE_MUSIC_UB1, MGB_NOT_FREE_MUSIC_UB2, etc.
            name = f"MGB_NOT_FREE_MUSIC_UB{key[-1]}"
            # Get session string from config
            session = getattr(config, string_key)

            # Create and attach the client as an attribute (self.one, self.two, self.three)
            setattr(
                self,
                key,
                Client(
                    name=name,
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=session,  # Pyrogram session string
                ),
            )

    async def boot_client(self, num: int, ub: Client):
        """
        Boot a client and perform initial setup.
        Args:
            num (int): The client number to boot (1, 2, or 3).
            ub (Client): The userbot client instance.
        Raises:
            SystemExit: If the client fails to send a message in the log group.
        """
        clients = {
            1: self.one,
            2: self.two,
            3: self.three,
        }
        client = clients[num]
        try:
            await client.start()
        except Exception as e:
            logger.error(f"❌ Assistant {num} failed to start: {e}")
            logger.error(f"   This could be due to:")
            logger.error(f"   • Invalid session string (STRING_SESSION{num})")
            logger.error(f"   • Session logged out from another device")
            logger.error(f"   • Network/connectivity issues")
            return  # Don't raise SystemExit, just skip this assistant

        try:
            await client.send_message(config.LOGGER_ID, f"Assistant {num} Started")
        except Exception as e:
            logger.warning(
                f"⚠️ Assistant {num} couldn't send message to logger: {e}"
            )
            # Continue anyway - this is not critical

        client.id = client.me.id if hasattr(
            client, 'me') and client.me else None
        client.name = client.me.first_name if hasattr(
            client, 'me') and client.me else f"Assistant{num}"
        client.username = client.me.username if hasattr(
            client, 'me') and client.me else None
        client.mention = client.me.mention if hasattr(
            client, 'me') and client.me else client.name
        self.clients.append(client)
        logger.info(f"👤 Assistant {num} started as @{client.username}")

    async def boot(self):
        """
        Asynchronously starts the assistants.
        """
        # Start all configured assistants concurrently so the first available
        # account is ready for VC playback as quickly as possible.
        tasks = []
        if config.SESSION1:
            tasks.append(self.boot_client(1, self.one))
        if config.SESSION2:
            tasks.append(self.boot_client(2, self.two))
        if config.SESSION3:
            tasks.append(self.boot_client(3, self.three))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Userbot automatic joins for support and update channels
        _targets = ["RIYA_MUSIC_BOT_786", "MGB_SUPPPOT"]
        
        async def _join_targets(client):
            async def _join(target):
                try:
                    await client.join_chat(target)
                    logger.info(f"Joined {target}")
                except Exception:
                    pass
            await asyncio.gather(*(_join(target) for target in _targets), return_exceptions=True)

        if _targets and self.clients:
            await asyncio.gather(*(_join_targets(client) for client in self.clients), return_exceptions=True)

    async def exit(self):
        """
        Asynchronously stops the assistants.
        """
        try:
            if config.SESSION1 and hasattr(self.one, 'is_connected') and self.one.is_connected:
                await self.one.stop()
        except Exception as e:
            logger.warning(f"Error stopping assistant 1: {e}")
        
        try:
            if config.SESSION2 and hasattr(self.two, 'is_connected') and self.two.is_connected:
                await self.two.stop()
        except Exception as e:
            logger.warning(f"Error stopping assistant 2: {e}")
        
        try:
            if config.SESSION3 and hasattr(self.three, 'is_connected') and self.three.is_connected:
                await self.three.stop()
        except Exception as e:
            logger.warning(f"Error stopping assistant 3: {e}")
        
        logger.info("Assistants stopped.")
