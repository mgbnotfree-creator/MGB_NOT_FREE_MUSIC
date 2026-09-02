import asyncio
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, BaseHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

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
        f"Hello {user.first_name}! Main ek Advanced Telegram Music Assistant Bot hoon. /play [Song Name] command ka use karein.",
        reply_markup=keyboard
    )

@app.on_message(filters.command("play"))
async def play_handler(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ Kripya gaane ka naam likhein!\nExample: /play Unstoppable")
        return

    query = " ".join(message.command[1:])
    processing_msg = await message.reply_text(f"🔍 Searching for: {query}...")

    # Bot detection bypass karne ke liye android client extractor argument add kiya hai
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch1',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                if not info['entries']:
                    await processing_msg.edit_text("❌ Koi gaana nahi mila. Kripya dusra naam try karein.")
                    return
                info = info['entries'][0]
            
            title = info.get('title', 'Unknown Title')
            duration = info.get('duration_string', 'N/A')
            webpage_url = info.get('webpage_url', '#')
            thumbnail = info.get('thumbnail', None)

        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📥 Watch on YouTube", url=webpage_url)]])
        await processing_msg.delete()
        
        if thumbnail:
            await message.reply_photo(
                photo=thumbnail,
                caption=f"🎶 Track Found!\n\n🏷 Title: {title}\n⏱ Duration: {duration}",
                reply_markup=keyboard
            )
        else:
            await message.reply_text(
                f"🎶 Track Found!\n\n🏷 Title: {title}\n⏱ Duration: {duration}",
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Error details: {e}")
        await processing_msg.edit_text(f"❌ Error: {str(e)}")

async def main():
    logger.info("Starting bot client...")
    await app.start()
    logger.info("Bot started successfully and running live!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop.run_until_complete(main())
    
