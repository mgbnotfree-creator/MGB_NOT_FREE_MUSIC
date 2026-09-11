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

from pathlib import Path

from Elevents import logger


def ensure_dirs():
    """
    Create necessary directories if they don't exist.

    Creates:
    - cache/: For temporary cache files
    - downloads/: For downloaded media files
    """
    # List of required directories
    for dir in ["cache", "downloads"]:
        # Create directory (and parents if needed)
        Path(dir).mkdir(parents=True, exist_ok=True)
    logger.info("📁 Cache directories updated.")
  
