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

logger = logging.getLogger("Elevenyts")

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
from Elevenyts.core.bot import Bot
app = Bot()

# Ensure required directories exist
from Elevenyts.core.dir import ensure_dirs
ensure_dirs()

# Initialize userbot/assistant clients
from Elevenyts.core.userbot import Userbot
userbot = Userbot()

# Initialize database connection
from Elevenyts.core.mongo import MongoDB
db = MongoDB()

# Initialize language system
from Elevenyts.core.lang import Language
lang = Language()

# Initialize Telegram and YouTube utilities
from Elevenyts.core.telegram import Telegram
from Elevenyts.core.youtube import YouTube
tg = Telegram()
yt = YouTube()

# Initialize preload manager for background track downloading
from Elevenyts.core.preload import PreloadManager
preload = PreloadManager()

# Initialize queue manager
from Elevenyts.helpers import Queue
queue = Queue()

# Initialize preload manager for next-track downloading
from Elevenyts.helpers._preload import PreloadManager
preload = PreloadManager()

# Initialize call handler
from Elevenyts.core.calls import TgCall

# Patch missing _is_running attribute for compatibility
if not hasattr(TgCall, '_is_running'):
    TgCall._is_running = property(
        lambda self: getattr(self, 'is_running', False),
        lambda self, val: setattr(self, 'is_running', val)
    )

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
    
