import os
import sys
import re
import asyncio
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# अनबफ़र्ड आउटपुट
sys.stdout.reconfigure(line_buffering=True)

API_ID = 31148936
API_HASH = "2e0c357ffb4f8bc9f5ed21cca77e9719"
BOT_TOKEN = "8579898320:AAE4AS4-frD2vCe0-yPprElEMWzFYWnZzkM"

# चैनल IDs
SOURCE_CHAT = -1003550975849
TARGET_CHAT = -1004440392510

SESSION_STRING = os.environ.get("SESSION_STRING")

user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient('bot', API_ID, API_HASH)

def clean_text(text):
    """दोस्त के लिंक्स, यूजरनेम और कॉन्टैक्ट हटाने के लिए फ़ंक्शन"""
    if not text:
        return ""
    
    # 1. सभी वेब लिंक्स (http, https, t.me, telegram.me) हटाएं
    text = re.sub(r'(https?://\S+|t\.me/\S+|telegram\.me/\S+)', '', text)
    
    # 2. सभी यूजरनेम्स (@username) हटाएं
    text = re.sub(r'@[a-zA-Z0-9_]+', '', text)
    
    # 3. 10 या अधिक अंकों वाले फोन नंबर हटाएं
    text = re.sub(r'(\+?\d[\d -]{8,}\d)', '', text)
    
    # 4. फालतू खाली लाइनें साफ़ करें
    text = re.sub(r'\n\s*\n+', '\n\n', text).strip()
    
    return text

@user_client.on(events.NewMessage)
async def new_message_handler(event):
    chat_id = event.chat_id

    if chat_id == SOURCE_CHAT:
        print(f"--> नया पोस्ट मिला! ID: {event.message.id}")
        
        # टेक्स्ट में से लिंक्स और कॉन्टैक्ट साफ़ करें
        original_text = event.message.text or ""
        cleaned_caption = clean_text(original_text)
        
        try:
            # अगर पोस्ट में इमेज, वीडियो या डॉक्यूमेंट है
            if event.message.media:
                print("--> मीडिया (फ़ोटो/फ़ाइल) डाउनलोड हो रहा है...")
                media_path = await event.message.download_media()
                
                print("--> टारगेट चैनल पर मीडिया भेजा जा रहा है...")
                await bot_client.send_file(
                    TARGET_CHAT, 
                    file=media_path, 
                    caption=cleaned_caption
                )
                
                # सर्वर स्टोरेज भरने से बचाने के लिए फ़ाइल तुरंत डिलीट करें
                if media_path and os.path.exists(media_path):
                    os.remove(media_path)
            else:
                # सिर्फ टेक्स्ट मैसेज होने पर
                if cleaned_caption:
                    await bot_client.send_message(TARGET_CHAT, cleaned_caption)
                else:
                    print("--> मैसेज में सिर्फ लिंक/कॉन्टैक्ट था, इसलिए खाली मैसेज नहीं भेजा गया।")
                    
            print("--> सफलतापूर्वक टारगेट चैनल पर पहुँच गया!")
            
        except Exception as e:
            print(f"--> भेजने में एरर: {e}")

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
    print(f"--> User Account लॉग-इन सफल: {me.first_name}")

    await bot_client.start(bot_token=BOT_TOKEN)
    bot_me = await bot_client.get_me()
    print(f"--> Telegram Bot कनेक्ट हुआ: @{bot_me.username}")

    await start_web_server()
    print(">>> 24/7 ऑटोमेशन एक्टिव है और नए मैसेज सुन रहा है! <<<")
    
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
