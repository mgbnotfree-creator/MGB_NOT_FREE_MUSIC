import logging
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
import yt_dlp
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Client(
    "MusicAssistantBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    user = message.from_user
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 Support Channel", url=config.CHANNEL_URL),
         InlineKeyboardButton("🛠 Support Group", url=config.SUPPORT_URL)],
        [InlineKeyboardButton("👑 Owner", url=config.OWNER_URL)]
    ])
    await message.reply_text(
        f"Hello **{user.first_name}**! 🎶\n\nMain ek Advanced Telegram Music Assistant Bot hoon. `/play [Song Name]` command ka use karein.",
        reply_markup=keyboard,
        parse_mode="markdown"
    )

@app.on_message(filters.command("play"))
async def play_handler(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ Kripya gaane ka naam likhein!\nExample: `/play Unstoppable`", parse_mode="markdown")
        return

    query = " ".join(message.command[1:])
    processing_msg = await message.reply_text(f"🔍 Searching for: *{query}*...", parse_mode="markdown")

    ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'default_search': 'ytsearch1', 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            title, duration, webpage_url, thumbnail = info.get('title'), info.get('duration_string', 'N/A'), info.get('webpage_url'), info.get('thumbnail')

        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📥 Watch on YouTube", url=webpage_url)]])
        await processing_msg.delete()
        await message.reply_photo(
            photo=thumbnail,
            caption=f"🎶 **Track Found!**\n\n🏷 **Title:** {title}\n⏱ **Duration:** {duration}",
            reply_markup=keyboard,
            parse_mode="markdown"
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await processing_msg.edit_text("❌ Kuch error aayi hai. Dubara koshish karein.")

if __name__ == "__main__":
    logger.info("Starting Advanced Music Bot...")
    app.start()
    logger.info("Bot started successfully! Running idle...")
    idle()
    app.stop()
    
