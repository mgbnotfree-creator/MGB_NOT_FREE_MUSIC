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

from pathlib import Path


def _list_modules():
    """
    List all Python module filenames (without extension) in the current directory
    and subdirectories, excluding the __init__.py file.

    Returns:
        list: A list of module names as strings with relative paths (e.g., 'admin_controls.broadcast').
    """
    mod_dir = Path(__file__).parent
    modules = []

    # Get all Python files in subdirectories
    for file in mod_dir.rglob("*.py"):
        if file.is_file() and file.name != "__init__.py":
            # Get relative path from modules directory
            relative_path = file.relative_to(mod_dir)
            # Convert path to module format: folder/file.py -> folder.file
            module_path = str(relative_path.with_suffix("")).replace('\\', '.').replace('/', '.')
            modules.append(module_path)

    return modules


all_modules = frozenset(sorted(_list_modules()))
