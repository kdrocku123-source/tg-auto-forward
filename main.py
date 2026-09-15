import os
import sys
import re
import asyncio
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from PIL import Image # Pillow लाइब्रेरी का इस्तेमाल क्रॉप करने के लिए

# अनबफ़र्ड आउटपुट के लिए
sys.stdout.reconfigure(line_buffering=True)

# आपकी API डिटेल्स
API_ID = 31148936
API_HASH = "2e0c357ffb4f8bc9f5ed21cca77e9719"
BOT_TOKEN = "8579898320:AAE4AS4-frD2vCe0-yPprElEMWzFYWnZzkM"

# चैनल IDs
SOURCE_CHAT = -1003550975849
TARGET_CHAT = -1004440392510

SESSION_STRING = os.environ.get("SESSION_STRING")

# आपका प्रोफ़ेशनल सिग्नेचर
MY_SIGNATURE = """

───────────────────────
📊 **Pips Power Official**
⚡ *Real-time Analysis & Setups*
📌 **Join:** https://t.me/pipspower1
⚠️ *For educational purposes only.*
───────────────────────"""

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
    
    # 3. फोन नंबर हटाएं
    text = re.sub(r'(\+?\d[\d -]{8,}\d)', '', text)
    
    # 4. फालतू खाली लाइनें साफ़ करें
    text = re.sub(r'\n\s*\n+', '\n\n', text).strip()
    
    return text

def crop_image(input_path, output_path):
    """इमेज के ऊपरी बाएँ हिस्से को क्रॉप करने के लिए फ़ंक्शन"""
    try:
        img = Image.open(input_path)
        width, height = img.size
        # ऊपरी 5% हिस्सा काट देंगे (यह 'tradehub1' नाम को हटाने के लिए पर्याप्त होना चाहिए)
        crop_percent = 0.05
        top_crop = int(height * crop_percent)
        # क्रॉपिंग एरिया (left, top, right, bottom)
        crop_box = (0, top_crop, width, height)
        cropped_img = img.crop(crop_box)
        cropped_img.save(output_path)
        print("--> इमेज को क्रॉप किया गया (शीर्ष का 5% काटा गया)।")
        return True
    except Exception as e:
        print(f"--> इमेज क्रॉप करने में एरर: {e}")
        return False

@user_client.on(events.NewMessage)
async def new_message_handler(event):
    chat_id = event.chat_id

    if chat_id == SOURCE_CHAT:
        print(f"--> नया पोस्ट मिला! ID: {event.message.id}")
        
        # दोस्त का कॉन्टैक्ट हटाना
        original_text = event.message.text or ""
        cleaned_text = clean_text(original_text)
        
        # अपना प्रोफेशनल सिग्नेचर जोड़ना
        if cleaned_text:
            final_caption = cleaned_text + MY_SIGNATURE
        else:
            final_caption = MY_SIGNATURE.strip()
        
        try:
            # अगर पोस्ट में इमेज है
            if event.message.photo:
                print("--> इमेज डाउनलोड हो रही है...")
                media_path = await event.message.download_media()
                cropped_path = f"cropped_{media_path}"
                
                # इमेज को क्रॉप करें
                if crop_image(media_path, cropped_path):
                    # क्रॉप की गई इमेज भेजें
                    file_to_send = cropped_path
                else:
                    # यदि क्रॉपिंग विफल हो जाती है, तो मूल इमेज भेजें
                    file_to_send = media_path
                    print("--> क्रॉपिंग विफल, मूल इमेज भेज रहे हैं।")
                
                print("--> टारगेट चैनल पर मीडिया और नया कैप्शन भेजा जा रहा है...")
                await bot_client.send_file(
                    TARGET_CHAT, 
                    file=file_to_send, 
                    caption=final_caption,
                    parse_mode='md'
                )
                
                # सर्वर स्टोरेज साफ़ रखने के लिए फ़ाइलें डिलीट करें
                if media_path and os.path.exists(media_path):
                    os.remove(media_path)
                if cropped_path and os.path.exists(cropped_path):
                    os.remove(cropped_path)
                    
            elif event.message.media:
                # अन्य मीडिया (वीडियो/डॉक्यूमेंट) के लिए (उन्हें क्रॉप नहीं कर सकते)
                print("--> अन्य मीडिया फ़ाइल डाउनलोड हो रही है...")
                media_path = await event.message.download_media()
                print("--> टारगेट चैनल पर मीडिया भेजा जा रहा है...")
                await bot_client.send_file(
                    TARGET_CHAT, 
                    file=media_path, 
                    caption=final_caption,
                    parse_mode='md'
                )
                if media_path and os.path.exists(media_path):
                    os.remove(media_path)
                    
            else:
                # केवल टेक्स्ट मैसेज होने पर
                await bot_client.send_message(
                    TARGET_CHAT, 
                    final_caption, 
                    parse_mode='md'
                )
                    
            print("--> पोस्ट सफलतापूर्वक आपके चैनल पर पहुँच गई!")
            
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
    
