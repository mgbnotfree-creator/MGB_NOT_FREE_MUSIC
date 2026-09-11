# ==========================================================
# Copyright (c) 2026 MGB Not Free Creator 
# All Rights Reserved.
#
# Project      : MGB Not Free Music Telegram Bot
# Powered By   : MGB Not Free Creator
# Type         : API Based Telegram Music Bot
#
# Bot          : @MUSIC1_NOT_FREE_BOT
# Channel      : https://t.me/MUSIC_SUPPORT_69
# GitHub       : https://github.com/mgbnotfree-creator/MGB_NOT_FREE_MUSIC
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================

from random import randint
from time import time
import asyncio
import logging

from pymongo import AsyncMongoClient

from Elevents import config, logger, userbot


# Suppress non-critical MongoDB background task errors
class MongoBackgroundFilter(logging.Filter):
    def filter(self, record):
        # Suppress AutoReconnect and _OperationCancelled background errors (these are handled internally)
        msg = record.getMessage()
        return not (
            'MongoClient background task encountered an error' in msg or
            ('AutoReconnect' in msg and 'background task' in msg) or
            ('_OperationCancelled' in msg and 'background task' in msg)
        )

logging.getLogger('pymongo.client').addFilter(MongoBackgroundFilter())


class MongoDB:
    def __init__(self):
        """
        Initialize the MongoDB connection.
        """
        self.mongo = AsyncMongoClient(
            config.MONGO_URL,
            serverSelectionTimeoutMS=12500,
            connectTimeoutMS=20000,
            socketTimeoutMS=20000,
            maxPoolSize=20,  # Reduced from 50 to prevent too many open connections
            minPoolSize=5,   # Reduced from 10 to prevent too many open connections
            maxIdleTimeMS=30000,  # Reduced from 45000 - close idle connections faster
            waitQueueTimeoutMS=10000,
            retryWrites=True,
            retryWrites=True
        )
        self.db = self.mongo.Elevents

        self.admin_list = {}  # Cache admin lists
        self.admin_cache_time = {}  # Track cache freshness
        self.active_calls = {}
        self.blacklisted = []
        self.notified = []
        self.cache = self.db.cache
        self.logger = False
        self.maintenance = False  # Maintenance mode status
        self.gbanned_users = []  # Globally banned users
        self.vplay_enabled = config.VIDEO_PLAY

        self.assistant = {}
        self.assistantdb = self.db.assistant

        self.auth = {}
        self.authdb = self.db.auth

        self.chats = []
        self.chatsdb = self.db.chats

        self.lang = {}
        self.langdb = self.db.lang

        self.play_mode = []
        self.playmodedb = self.db.play

        self.force_mode = []
        self.forcemodedb = self.db.forcemode

        self.users = []
        self.usersdb = self.db.users

    async def connect(self) -> None:
        """Check if we can connect to the database with exponential backoff retry logic.

        Raises:
            SystemExit: If the connection to the database fails after retries.
        """
        max_retries = 3
        retry_delay = 5  # Initial delay in seconds
        
        for attempt in range(1, max_retries + 1):
            try:
                start = time()
                await self.mongo.admin.command("ping")
                logger.info(
                    f"⚡ Database connection successful. ({time() - start:.2f}s)")

                # Create indexes for faster queries
                await self.authdb.create_index("_id")
                await self.langdb.create_index("_id")
                await self.cache.create_index("_id")

                await self.load_cache()
                return  # Success, exit the function
            except Exception as e:
                if attempt < max_retries:
                    # Exponential backoff: 5s, 10s, 20s
                    wait_time = retry_delay * (2 ** (attempt - 1))
                    logger.warning(f"Database connection attempt {attempt}/{max_retries} failed: {type(e).__name__}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise SystemExit(
                        f"Database connection failed after {max_retries} attempts: {type(e).__name__}") from e

    async def close(self) -> None:
        """Close the connection to the database."""
        await self.mongo.close()
        logger.info("Database connection closed.")

    # CACHE
    async def get_call(self, chat_id: int) -> bool:
        return chat_id in self.active_calls

    async def add_call(self, chat_id: int) -> None:
        self.active_calls[chat_id] = 1

    async def remove_call(self, chat_id: int) -> None:
        self.active_calls.pop(chat_id, None)

    async def playing(self, chat_id: int, paused: bool = None) -> bool | None:
        if paused is not None:
            self.active_calls[chat_id] = int(not paused)
        return bool(self.active_calls.get(chat_id))

    async def get_admins(self, chat_id: int, reload: bool = False) -> list[int]:
        from Elevents.helpers._admins import reload_admins

        # **PERFORMANCE FIX**: Increased cache from 5 to 15 minutes
        # Reduces MongoDB queries during peak load (15-20 concurrent streams)
        current_time = time()
        cache_age = current_time - self.admin_cache_time.get(chat_id, 0)

        if chat_id not in self.admin_list or reload or cache_age > 900:  # 15 minutes
            self.admin_list[chat_id] = await reload_admins(chat_id)
            self.admin_cache_time[chat_id] = current_time
        return self.admin_list[chat_id]

    # AUTH METHODS
    async def _get_auth(self, chat_id: int) -> set[int]:
        if chat_id not in self.auth:
            doc = await self.authdb.find_one({"_id": chat_id}) or {}
            self.auth[chat_id] = set(doc.get("user_ids", []))
        return self.auth[chat_id]

    async def is_auth(self, chat_id: int, user_id: int) -> bool:
        return user_id in await self._get_auth(chat_id)

    async def add_auth(self, chat_id: int, user_id: int) -> None:
        users = await self._get_auth(chat_id)
        if user_id not in users:
            users.add(user_id)
            await self.authdb.update_one(
                {"_id": chat_id}, {"$addToSet": {"user_ids": user_id}}, upsert=True
            )

    async def rm_auth(self, chat_id: int, user_id: int) -> None:
        users = await self._get_auth(chat_id)
        if user_id in users:
            users.discard(user_id)
            await self.authdb.update_one(
                {"_id": chat_id}, {"$pull": {"user_ids": user_id}}
            )

    # ASSISTANT METHODS
    async def set_assistant(self, chat_id: int) -> int:
        num = randint(1, len(userbot.clients))
        await self.assistantdb.update_one(
            {"_id": chat_id},
            {"$set": {"num": num}},
            upsert=True,
        )
        self.assistant[chat_id] = num
        return num

    async def get_assistant(self, chat_id: int):
        from Elevents import tune

        if chat_id not in self.assistant:
            doc = await self.assistantdb.find_one({"_id": chat_id})
            num = doc["num"] if doc else await self.set_assistant(chat_id)
            self.assistant[chat_id] = num

        # Check if assigned assistant is out of range (e.g., assistant was removed)
        if self.assistant[chat_id] > len(userbot.clients):
            # Reassign to a valid assistant
            num = await self.set_assistant(chat_id)
            self.assistant[chat_id] = num

        return tune.clients[self.assistant[chat_id] - 1]

    async def get_client(self, chat_id: int):
        if chat_id not in self.assistant:
            await self.get_assistant(chat_id)
        
        # Check if assigned assistant is out of range
        if self.assistant[chat_id] > len(userbot.clients):
            # Reassign to a valid assistant
            await self.set_assistant(chat_id)
        
        # Get available clients dynamically based on what's actually running
        available_clients = {}
        if hasattr(userbot, 'one') and userbot.one in userbot.clients:
            available_clients[1] = userbot.one
        if hasattr(userbot, 'two') and userbot.two in userbot.clients:
            available_clients[2] = userbot.two
        if hasattr(userbot, 'three') and userbot.three in userbot.clients:
            available_clients[3] = userbot.three
        
        return available_clients.get(self.assistant[chat_id])

    # BLACKLIST METHODS
    async def add_blacklist(self, chat_id: int) -> None:
        if str(chat_id).startswith("-"):
            self.blacklisted.append(chat_id)
            return await self.cache.update_one(
                {"_id": "bl_chats"}, {"$addToSet": {"chat_ids": chat_id}}, upsert=True
            )
        await self.cache.update_one(
            {"_id": "bl_users"}, {"$addToSet": {"user_ids": chat_id}}, upsert=True
        )

    async def del_blacklist(self, chat_id: int) -> None:
        if str(chat_id).startswith("-"):
            self.blacklisted.remove(chat_id)
            return await self.cache.update_one(
                {"_id": "bl_chats"},
                {"$pull": {"chat_ids": chat_id}},
            )
        await self.cache.update_one(
            {"_id": "bl_users"},
            {"$pull": {"user_ids": chat_id}},
        )

    async def get_blacklisted(self, chat: bool = False) -> list[int]:
        if chat:
            if not self.blacklisted:
                doc = await self.cache.find_one({"_id": "bl_chats"})
                self.blacklisted.extend(doc.get("chat_ids", []) if doc else [])
            return self.blacklisted
        doc = await self.cache.find_one({"_id": "bl_users"})
        return doc.get("user_ids", []) if doc else []

    # CHAT METHODS
    async def is_chat(self, chat_id: int) -> bool:
        return chat_id in self.chats

    async def add_chat(self, chat_id: int) -> None:
        if not await self.is_chat(chat_id):
            self.chats.append(chat_id)
            await self.chatsdb.insert_one({"_id": chat_id})

    async def rm_chat(self, chat_id: int) -> None:
        if await self.is_chat(chat_id):
            self.chats.remove(chat_id)
            await self.chatsdb.delete_one({"_id": chat_id})

    async def get_chats(self) -> list:
        if not self.chats:
            self.chats.extend([chat["_id"] async for chat in self.chatsdb.find()])
        return self.chats

    # LANGUAGE METHODS
    async def set_lang(self, chat_id: int, lang_code: str):
        await self.langdb.update_one(
            {"_id": chat_id},
            {"$set": {"lang": lang_code}},
            upsert=True,
        )
        self.lang[chat_id] = lang_code

    async def get_lang(self, chat_id: int) -> str:
        if chat_id not in self.lang:
            doc = await self.langdb.find_one({"_id": chat_id})
            self.lang[chat_id] = doc["lang"] if doc else "en"
        return self.lang[chat_id]

    # MAINTENANCE MODE METHODS
    async def set_maintenance(self, status: bool) -> None:
        """Enable or disable maintenance mode."""
        await self.cache.update_one(
            {"_id": "maintenance"},
            {"$set": {"status": status}},
            upsert=True,
        )
        self.maintenance = status

    async def get_maintenance(self) -> bool:
        """Check if maintenance mode is enabled."""
        if not hasattr(self, 'maintenance'):
            doc = await self.cache.find_one({"_id": "maintenance"})
            self.maintenance = doc.get("status", False) if doc else False
        return self.maintenance

    # VPLAY TOGGLE METHODS
    async def get_vplay_enabled(self) -> bool:
        """Check if /vplay commands are enabled."""
        if hasattr(self, 'vplay_enabled'):
            return self.vplay_enabled

        doc = await self.cache.find_one({"_id": "vplay_toggle"})
        self.vplay_enabled = doc.get("enabled", config.VIDEO_PLAY) if doc else config.VIDEO_PLAY
        return self.vplay_enabled

    async def set_vplay_enabled(self, enabled: bool) -> None:
        """Enable or disable /vplay commands globally."""
        self.vplay_enabled = enabled
        await self.cache.update_one(
            {"_id": "vplay_toggle"},
            {"$set": {"enabled": enabled}},
            upsert=True,
        )

    # GLOBAL BAN METHODS
    async def add_gban(self, user_id: int) -> None:
        """Add user to global ban list."""
        await self.cache.update_one(
            {"_id": "gbanned_users"},
            {"$addToSet": {"user_ids": user_id}},
            upsert=True,
        )
        if not hasattr(self, 'gbanned_users'):
            self.gbanned_users = []
        if user_id not in self.gbanned_users:
            self.gbanned_users.append(user_id)

    async def del_gban(self, user_id: int) -> None:
        """Remove user from global ban list."""
        await self.cache.update_one(
            {"_id": "gbanned_users"},
            {"$pull": {"user_ids": user_id}},
        )
        if hasattr(self, 'gbanned_users') and user_id in self.gbanned_users:
            self.gbanned_users.remove(user_id)

    async def get_gbanned(self) -> list[int]:
        """Get list of globally banned users."""
        if not hasattr(self, 'gbanned_users'):
            doc = await self.cache.find_one({"_id": "gbanned_users"})
            self.gbanned_users = doc.get("user_ids", []) if doc else []
        return self.gbanned_users
    
    async def is_gbanned(self, user_id: int) -> bool:
        """Check if user is globally banned."""
        gbanned = await self.get_gbanned()
        return user_id in gbanned

    # LOGGER METHODS
    async def is_logger(self) -> bool:
        return self.logger

    async def get_logger(self) -> bool:
        doc = await self.cache.find_one({"_id": "logger"})
        if doc:
            self.logger = doc["status"]
        return self.logger

    async def set_logger(self, status: bool) -> None:
        self.logger = status
        await self.cache.update_one(
            {"_id": "logger"},
            {"$set": {"status": status}},
            upsert=True,
        )

    # CHANNEL PLAY METHODS
    async def get_cmode(self, chat_id: int) -> int | None:
        """Get channel play mode for a chat."""
        doc = await self.cache.find_one({"_id": f"cplay_{chat_id}"})
        return doc.get("channel_id") if doc else None

    async def set_cmode(self, chat_id: int, channel_id: int | None) -> None:
        """Set channel play mode for a chat."""
        if channel_id is None:
            await self.cache.delete_one({"_id": f"cplay_{chat_id}"})
        else:
            await self.cache.update_one(
                {"_id": f"cplay_{chat_id}"},
                {"$set": {"channel_id": channel_id}},
                upsert=True,
      )
              
