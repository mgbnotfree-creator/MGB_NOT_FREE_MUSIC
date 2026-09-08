import os
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import config

# Flask Server for Render Keep-Alive
app_server = Flask('')

@app_server.route('/')
def home():
    return "Music Bot is active and running!"

def run_web():
    try:
        port = int(os.environ.get("PORT", 10000))
        app_server.run(host='0.0.0.0', port=port, use_reloader=False)
    except Exception as e:
        print(f"Flask Error: {e}")

# Pyrogram Bot Client Setup using config.py
try:
    app = Client(
        "MusicBot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN
    )
except Exception as e:
    print(f"Pyrogram Client Init Error: {e}")

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    try:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🎵 Add Me To Your Group", url=f"https://t.me/{client.me.username}?startgroup=true")
                ],
                [
                    InlineKeyboardButton("🛠️ Support Group", url=config.SUPPORT_GROUP),
                    InlineKeyboardButton("👤 Bot Owner", url=f"tg://user?id={config.OWNER_ID}")
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
    except Exception as e:
        print(f"Start command error: {e}")

if __name__ == "__main__":
    # Start Flask server in background thread
    web_thread = Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()
    
    print("Bot is starting up...")
    try:
        app.run()
    except Exception as e:
        print(f"App run error: {e}")
        
