import asyncio
import os
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
import yt_dlp
import config

# Flask Server for Render (Satisfies port binding requirement)
app_server = Flask('')

@app_server.route('/')
def home():
    return "Music Bot & VC Streamer is active and running!"

# Pyrogram Bot Client Setup
app = Client(
    "MusicBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# PyTgCalls Assistant Userbot Setup using STRING_SESSION
user_app = Client(
    "Assistant",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.STRING_SESSION
)

call_py = PyTgCalls(user_app)

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🟢 Add Me To Your Group", url=f"https://t.me/{client.me.username}?startgroup=true")
            ],
            [
                InlineKeyboardButton("🔵 Support Group", url=config.SUPPORT_GROUP),
                InlineKeyboardButton("🔴 Bot Owner", url=f"tg://user?id={config.OWNER_ID}")
            ]
        ]
    )
    
    welcome_text = (
        "✨ **Welcome to MGB Voice Chat Music Bot!** ✨\n\n"
        "🎵 I can stream high-quality audio directly into your Telegram Voice Chats.\n"
        "🚀 Use `/play <song name>` in your group chat!\n"
    )
    
    await message.reply_text(welcome_text, reply_markup=keyboard)

@app.on_message(filters.command("play"))
async def play_command(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide a song name! Example: `/play Faded`")
        return
    
    if not message.chat.type in ["supergroup", "group"]:
        await message.reply_text("❌ This command can only be used inside groups!")
        return

    query = " ".join(message.command[1:])
    m = await message.reply_text(f"🔎 Searching for `{query}` on YouTube...")

    try:
        ydl_opts = {'format': 'bestaudio', 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            stream_url = info['url']
            song_title = info['title']
        
        # Updated play method for latest py-tgcalls
        await call_py.play(
            message.chat.id,
            stream_url
        )
        
        await m.edit_text(
            f"🎶 **Now Playing in Voice Chat:**\n"
            f"📌 [{song_title}]({info.get('webpage_url', '')})\n"
            f"👤 **Requested by:** {message.from_user.mention}"
        )
    except Exception as e:
        await m.edit_text(f"❌ An error occurred: `{str(e)}`")

@app.on_message(filters.command("stop"))
async def stop_command(client, message: Message):
    try:
        await call_py.leave_group_call(message.chat.id)
        await message.reply_text("⏹️ Music stopped and voice chat left successfully!")
    except Exception as e:
        await message.reply_text(f"❌ Error: `{str(e)}`")

def run_telegram_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def main():
        print("Starting Telegram Music Bot & PyTgCalls...")
        await user_app.start()
        await call_py.start()
        await app.start()
        await asyncio.Event().wait()
        
    loop.run_until_complete(main())

if __name__ == "__main__":
    # Start Telegram Bot in background thread
    bot_thread = Thread(target=run_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Run Flask Web Server on main thread
    port = int(os.environ.get("PORT", 10000))
    app_server.run(host='0.0.0.0', port=port)
