import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = 36041423
API_HASH = "09ded9c30cbd3d152dcab19d034e046d"
BOT_TOKEN = "8579898320:AAE4AS4-frD2vCe0-yPprElEMWzFYWnZzkM"
SOURCE_CHAT = -1003550975849
TARGET_CHAT = -1004440392510

SESSION_STRING = os.environ.get("SESSION_STRING")

user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient('bot', API_ID, API_HASH)

@user_client.on(events.NewMessage(chats=SOURCE_CHAT))
async def new_message_handler(event):
    try:
        await bot_client.send_message(TARGET_CHAT, event.message)
        print("मैसेज सफलतापूर्वक फॉरवर्ड हो गया!")
    except Exception as e:
        print(f"Error: {e}")

async def main():
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    print(">>> 24/7 ऑटोमेशन एक्टिव है! <<<")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
  
