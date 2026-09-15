import os
import sys
import re
import asyncio
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from PIL import Image

sys.stdout.reconfigure(line_buffering=True)

# आपकी API डिटेल्स
API_ID = 31148936
API_HASH = "2e0c357ffb4f8bc9f5ed21cca77e9719"
BOT_TOKEN = "8579898320:AAE4AS4-frD2vCe0-yPprElEMWzFYWnZzkM"

# चैनल IDs
SOURCE_CHAT = -1003550975849
TARGET_CHAT = -1004440392510

SESSION_STRING = os.environ.get("SESSION_STRING")

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
    if not text:
        return ""
    text = re.sub(r'(https?://\S+|t\.me/\S+|telegram\.me/\S+)', '', text)
    text = re.sub(r'@[a-zA-Z0-9_]+', '', text)
    text = re.sub(r'(\+?\d[\d -]{8,}\d)', '', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text).strip()
    return text

def is_trading_signal(text):
    t = text.upper()
    return any(k in t for k in ["BUY", "SELL"]) and any(k in t for k in ["TP", "TARGET", "SL"])

def parse_signal(text):
    """सिग्नल में से पेयर, एक्शन, टीपी और एसएल निकालना"""
    data = {
        "is_sell": "SELL" in text.upper(),
        "action": "SELL" if "SELL" in text.upper() else "BUY",
        "pair": "XAUUSD (GOLD)",
        "entry": "",
        "tps": [],
        "sl": ""
    }
    
    # पेयर निकालना
    pair_match = re.search(r'#?([A-Z]{6}|XAUUSD|GOLD)', text, re.IGNORECASE)
    if pair_match:
        found_pair = pair_match.group(1).upper()
        data["pair"] = "XAUUSD (GOLD)" if "XAU" in found_pair or "GOLD" in found_pair else found_pair
        
    # एंट्री रेट
    entry_match = re.search(r'(?:BUY|SELL|@)\s*@?\s*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
    if entry_match:
        data["entry"] = f"{data['action']} @ {entry_match.group(1)}"
    else:
        data["entry"] = data["action"]

    # TP लेवल्स
    tp_matches = re.findall(r'(?:TP\s*[\d]?|TARGET\s*[\d]?)\s*[:=-]?\s*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
    for i, tp in enumerate(tp_matches[:3], 1):
        data["tps"].append((f"TARGET {i} (TP {i})", tp))
        
    # SL लेवल
    sl_match = re.search(r'SL\s*[:=-]?\s*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
    if sl_match:
        data["sl"] = sl_match.group(1)
        
    return data

def generate_first_style_card(data):
    """पहली इमेज स्टाइल वाला वीआईपी कार्ड जनरेट करना"""
    is_sell = data["is_sell"]
    accent_color = '#E74C3C' if is_sell else '#2ECC71'
    header_title = "SELL SIGNAL ALERT" if is_sell else "BUY SIGNAL ALERT"
    
    fig, ax = plt.subplots(figsize=(8, 8), dpi=160)
    fig.patch.set_facecolor('#0B0E14')
    ax.set_facecolor('#0B0E14')

    # आउटर बॉर्डर बॉक्स
    rect = patches.FancyBboxPatch(
        (0.05, 0.05), 0.9, 0.9,
        boxstyle="round,pad=0.03,rounding_size=0.04",
        linewidth=2.5, edgecolor=accent_color, facecolor='#131722', zorder=1
    )
    ax.add_patch(rect)

    # हेडर बॉक्स
    hdr_bg = '#2A1215' if is_sell else '#0F2A1C'
    header_box = patches.FancyBboxPatch(
        (0.08, 0.78), 0.84, 0.12,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        linewidth=1, edgecolor=accent_color, facecolor=hdr_bg, zorder=2
    )
    ax.add_patch(header_box)

    ax.text(0.5, 0.85, header_title, color='#FF4B4B' if is_sell else '#2ECC71', fontsize=18, fontweight='heavy', ha='center', va='center', zorder=3)
    ax.text(0.5, 0.805, "PIPS POWER OFFICIAL | VIP SETUP", color='#E0B853', fontsize=11, fontweight='bold', ha='center', va='center', zorder=3)

    # पेयर & एक्शन बॉक्स
    pair_box = patches.FancyBboxPatch(
        (0.08, 0.63), 0.84, 0.11,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=1, edgecolor='#3A3E4A', facecolor='#1A202C', zorder=2
    )
    ax.add_patch(pair_box)
    ax.text(0.12, 0.685, f"PAIR : {data['pair']}", color='#FFFFFF', fontsize=14, fontweight='bold', va='center', zorder=3)
    ax.text(0.88, 0.685, data['entry'], color='#FF4B4B' if is_sell else '#2ECC71', fontsize=15, fontweight='heavy', ha='right', va='center', zorder=3)

    # TP बॉक्सेस
    y_pos = 0.50
    for label, val in data['tps']:
        tp_box = patches.FancyBboxPatch(
            (0.08, y_pos - 0.02), 0.84, 0.075,
            boxstyle="round,pad=0.015,rounding_size=0.02",
            linewidth=1, edgecolor='#1E3A2F', facecolor='#0D221A', zorder=2
        )
        ax.add_patch(tp_box)
        ax.text(0.12, y_pos + 0.018, f">>  {label}", color='#A0AEC0', fontsize=12, fontweight='bold', va='center', zorder=3)
        ax.text(0.88, y_pos + 0.018, val, color='#00E676', fontsize=14, fontweight='heavy', ha='right', va='center', zorder=3)
        y_pos -= 0.095

    # SL बॉक्स
    if data['sl']:
        sl_box = patches.FancyBboxPatch(
            (0.08, y_pos - 0.02), 0.84, 0.075,
            boxstyle="round,pad=0.015,rounding_size=0.02",
            linewidth=1, edgecolor='#4A1C1C', facecolor='#251113', zorder=2
        )
        ax.add_patch(sl_box)
        ax.text(0.12, y_pos + 0.018, ">>  STOP LOSS (SL)", color='#A0AEC0', fontsize=12, fontweight='bold', va='center', zorder=3)
        ax.text(0.88, y_pos + 0.018, data['sl'], color='#FF5252', fontsize=14, fontweight='heavy', ha='right', va='center', zorder=3)

    # फुटर
    ax.text(0.5, 0.11, "Discipline & Risk Management Over Emotion", color='#718096', fontsize=10, style='italic', ha='center', va='center', zorder=3)
    ax.text(0.5, 0.075, "Telegram: @pipspower1  |  For Educational Purposes", color='#F1C40F', fontsize=11, fontweight='bold', ha='center', va='center', zorder=3)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=160, bbox_inches='tight', facecolor='#0B0E14')
    plt.close(fig)
    buf.seek(0)
    return buf

def crop_image(input_path, output_path):
    try:
        img = Image.open(input_path)
        w, h = img.size
        crop_box = (0, int(h * 0.05), w, h)
        cropped = img.crop(crop_box)
        cropped.save(output_path)
        return True
    except Exception as e:
        print(f"--> क्रॉपिंग एरर: {e}")
        return False

@user_client.on(events.NewMessage)
async def new_message_handler(event):
    if event.chat_id == SOURCE_CHAT:
        print(f"--> नया पोस्ट मिला! ID: {event.message.id}")
        raw_text = event.message.text or ""
        cleaned = clean_text(raw_text)
        
        try:
            # 1. चार्ट इमेज होने पर
            if event.message.photo:
                print("--> इमेज डाउनलोड हो रही है...")
                path = await event.message.download_media()
                c_path = f"c_{path}"
                send_path = c_path if crop_image(path, c_path) else path
                final_caption = (cleaned + MY_SIGNATURE) if cleaned else MY_SIGNATURE.strip()
                
                await bot_client.send_file(TARGET_CHAT, file=send_path, caption=final_caption, parse_mode='md')
                if os.path.exists(path): os.remove(path)
                if os.path.exists(c_path): os.remove(c_path)

            # 2. अन्य मीडिया होने पर
            elif event.message.media:
                path = await event.message.download_media()
                final_caption = (cleaned + MY_SIGNATURE) if cleaned else MY_SIGNATURE.strip()
                await bot_client.send_file(TARGET_CHAT, file=path, caption=final_caption, parse_mode='md')
                if os.path.exists(path): os.remove(path)

            # 3. टेक्स्ट मैसेज
            else:
                if is_trading_signal(cleaned):
                    print("--> ट्रेडिंग सिग्नल मिला! पहली स्टाइल का वीआईपी कार्ड तैयार हो रहा है...")
                    parsed = parse_signal(cleaned)
                    card_buf = generate_first_style_card(parsed)
                    final_caption = cleaned + MY_SIGNATURE
                    
                    # इमेज को फाइल नाम 'signal.png' देकर भेजें
                    card_buf.name = "signal.png"
                    await bot_client.send_file(TARGET_CHAT, file=card_buf, caption=final_caption, parse_mode='md')
                else:
                    # सामान्य टेक्स्ट (Now, Gold आदि) सीधे जाएँगे
                    if cleaned:
                        await bot_client.send_message(TARGET_CHAT, cleaned, parse_mode='md')

            print("--> पोस्ट सफलतापूर्वक आपके चैनल पर पहुँच गई!")
        except Exception as e:
            print(f"--> एरर: {e}")

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

async def main():
    print("--> बॉट चालू हो रहा है...")
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    await start_web_server()
    print(">>> 24/7 ऑटोमेशन एक्टिव है! <<<")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
    
