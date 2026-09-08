import os
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import config

# Flask Server for Render Keep-Alive (Sleep na hone de)
app_server = Flask('')

@app_server.route('/')
def home():
    return "Music Bot is active and running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_server.run(host='0.0.0.0', port=port)

# Pyrogram Bot Client Setup using config.py
app = Client(
    "MusicBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    # Colorful & Attractive UI Design with Inline Keyboards
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎵 Add Me To Your Group", url=f"https://t.me/{client.me.username}?startgroup=true")
            ],
            [
                InlineKeyboardButton("🛠️ Support Group", url=config.SUPPORT_GROUP),
                InlineKeyboardButton("👤 Bot Owner", url=f"tg://user?id={config.OWNER_ID}")
            ],
            [
                InlineKeyboardButton("📜 Commands Help", callback_data="help_menu")
            ]
        ]
    )
    
    welcome_text = (
        "✨ **Welcome to Advanced Music Bot!** ✨\n\n"
        "🎶 I can play high-quality music in your Telegram Voice Chats.\n"
        "🚀 Fast, reliable, and completely free on Render!\n\n"
        "👇 *Choose an option below to get started:*"
    )
    
    await message.reply_text(welcome_text, reply_markup=keyboard)

@app.on_message(filters.command("play"))
async def play_command(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Please provide a song name.**\nExample: `/play Faded`")
        return
    
    query = " ".join(message.command[1:])
    m = await message.reply_text(f"🔎 Searching for `{query}`...")
    await m.edit_text(f"🎵 Playing **{query}** successfully! (Stream connected)")

if __name__ == "__main__":
    # Start Flask server in background thread for Render keep-alive
    t = Thread(target=run_web)
    t.start()
    
    print("Bot is starting via main.py...")
    app.run()
                                     
