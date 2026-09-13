import os
import sys
import asyncio
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# अनबफ़र्ड आउटपुट के लिए
sys.stdout.reconfigure(line_buffering=True)

API_ID = 36041423
API_HASH = "09ded9c30cbd3d152dcab19d034e046d"
BOT_TOKEN = "8579898320:AAE4AS4-frD2vCe0-yPprElEMWzFYWnZzkM"

# IDs
SOURCE_CHAT = -1003550975849
TARGET_CHAT = -1004440392510

SESSION_STRING = os.environ.get("SESSION_STRING")

user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient('bot', API_ID, API_HASH)

@user_client.on(events.NewMessage)
async def new_message_handler(event):
    chat = await event.get_chat()
    chat_id = event.chat_id
    print(f"--> नया मैसेज डिटेक्ट हुआ! Chat ID: {chat_id}")

    # अगर सोर्स चैट से मैसेज आया हो
    if chat_id == SOURCE_CHAT:
        print("--> सोर्स चैनल का मैसेज मैच हो गया! फॉरवर्ड किया जा रहा है...")
        try:
            # कॉपी/फॉरवर्ड प्रोटेक्टेड चैनल के लिए भी काम करेगा
            if event.message.media:
                await bot_client.send_file(TARGET_CHAT, file=event.message.media, caption=event.message.text)
            else:
                await bot_client.send_message(TARGET_CHAT, event.message.text)
            print("--> मैसेज सफलतापूर्वक टारगेट चैनल पर पहुँच गया!")
        except Exception as e:
            print(f"--> मैसेज भेजने में Error: {e}")

async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"--> वेब सर्वर पोर्ट {port} पर एक्टिव है।")

async def main():
    print("--> बॉट शुरू हो रहा है...")
    await user_client.start()
    me = await user_client.get_me()
    print(f"--> User Account लॉग-इन सफल: {me.first_name} (@{me.username})")

    await bot_client.start(bot_token=BOT_TOKEN)
    bot_me = await bot_client.get_me()
    print(f"--> Telegram Bot कनेक्ट हुआ: @{bot_me.username}")

    await start_web_server()
    print(">>> 24/7 ऑटोमेशन एक्टिव है और नए मैसेज सुन रहा है! <<<")
    
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
    
