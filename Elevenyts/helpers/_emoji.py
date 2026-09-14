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

import itertools

# Rotating emoji sequence shown on /play and on autoplay messages.
# Each call to next_play_emoji() advances to the next emoji in the list,
# wrapping back to the start once the end is reached — so consecutive
# /play (and autoplay) triggers each show a different emoji in turn.
PLAY_EMOJIS = ["🎵", "🎶", "🎸", "🌟", "🔥", "🎧", "🌈", "💫"]

_emoji_cycle = itertools.cycle(PLAY_EMOJIS)


def next_play_emoji() -> str:
    return next(_emoji_cycle)
