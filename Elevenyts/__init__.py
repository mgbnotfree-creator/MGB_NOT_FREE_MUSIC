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
import time
import logging
from logging.handlers import RotatingFileHandler
from typing import List

# Configure logging
logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=10485760, backupCount=5),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)

# Reduce noise from third-party libraries
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.CRITICAL)
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)

logger = logging.getLogger("MGB_NOT_FREE_MUSIC")

# Version
__version__ = "3.0.1"

# Load configuration
from config import Config

config = Config()
config.check()

# Global task list for background tasks
tasks: List = []
boot: float = time.time()

# Initialize bot client
from MGB_NOT_FREE_MUSIC.core.bot import Bot
app = Bot()

# Ensure required directories exist
from MGB_NOT_FREE_MUSIC.core.dir import ensure_dirs
ensure_dirs()

# Initialize userbot/assistant clients
from MGB_NOT_FREE_MUSIC.core.userbot import Userbot
userbot = Userbot()

# Initialize database connection
from MGB_NOT_FREE_MUSIC.core.mongo import MongoDB
db = MongoDB()

# Initialize language system
from MGB_NOT_FREE_MUSIC.core.lang import Language
lang = Language()

# Initialize Telegram and YouTube utilities
from MGB_NOT_FREE_MUSIC.core.telegram import Telegram
from MGB_NOT_FREE_MUSIC.core.youtube import YouTube
tg = Telegram()
yt = YouTube()

# Initialize preload manager for background track downloading
from MGB_NOT_FREE_MUSIC.core.preload import PreloadManager
preload = PreloadManager()

# Initialize queue manager
from MGB_NOT_FREE_MUSIC.helpers import Queue
queue = Queue()

# Initialize preload manager for next-track downloading
from MGB_NOT_FREE_MUSIC.helpers._preload import PreloadManager
preload = PreloadManager()

# Initialize call handler
from MGB_NOT_FREE_MUSIC.core.calls import TgCall
tune = TgCall()


async def stop() -> None:
    """
    Gracefully shutdown the bot and all its components.
    
    This function:
    - Cancels all running background tasks
    - Closes bot and userbot connections
    - Closes database connection
    - Logs shutdown completion
    """
    logger.info("🛑 Stopping bot...")
    
    # Cancel all background tasks
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            # Expected when cancelling tasks - suppress the error
            pass
        except Exception:
            pass
    
    # Close all connections
    await app.exit()
    await userbot.exit()
    await db.close()
    
    logger.info("✅ Bot stopped successfully.\n")
