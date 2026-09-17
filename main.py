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

API_ID = 31148936
API_HASH = "2e0c357ffb4f8bc9f5ed21cca77e9719"
BOT_TOKEN = "8579898320:AAE4AS4-frD2vCe0-yPprElEMWzFYWnZzkM"

SOURCE_CHAT = -1003550975849
TARGET_CHAT = -1004440392510

SESSION_STRING = os.environ.get("SESSION_STRING")

user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient('bot', API_ID, API_HASH)

def normalize_text(text):
    """सुपरस्क्रिप्ट अक्षरों (¹ ² ³) को सामान्य अंकों में बदलना"""
    if not text:
        return ""
    trans_table = str.maketrans("¹²³⁴⁵⁶⁷⁸⁹⁰", "1234567890")
    return text.translate(trans_table)

def clean_text(text):
    """लिंक्स, यूजरनेम और अनचाहे कैरेक्टर हटाना"""
    if not text:
        return ""
    text = re.sub(r'(https?://\S+|t\.me/\S+|telegram\.me/\S+)', '', text)
    text = re.sub(r'@[a-zA-Z0-9_]+', '', text)
    text = re.sub(r'(\+?\d[\d -]{8,}\d)', '', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text).strip()
    return text

def is_trading_signal(text):
    t = normalize_text(text).upper()
    has_action = any(k in t for k in ["BUY", "SELL"])
    has_levels = any(k in t for k in ["TP", "TARGET", "SL", "STOP LOSS"])
    return has_action and has_levels

def parse_signal(text):
    """हर फॉर्मेट (इमोजी, टिक मार्क, सुपरस्क्रिप्ट) से TP और SL निकालना"""
    norm = normalize_text(text)
    is_sell = "SELL" in norm.upper()
    action = "SELL" if is_sell else "BUY"
    
    data = {
        "is_sell": is_sell,
        "action": action,
        "pair": "XAUUSD (GOLD)",
        "entry": f"{action}  {'↓' if is_sell else '↑'}",
        "tps": [],
        "sl": ""
    }

    # पेयर निकालना
    pair_match = re.search(r'#?([A-Z]{6}|XAUUSD|GOLD)', norm, re.IGNORECASE)
    if pair_match:
        found_pair = pair_match.group(1).upper()
        data["pair"] = "XAUUSD (GOLD)" if ("XAU" in found_pair or "GOLD" in found_pair) else found_pair

    # एंट्री रेट
    entry_match = re.search(r'(?:BUY|SELL|@)\s*@?\s*([0-9]+(?:\.[0-9]+)?)', norm, re.IGNORECASE)
    arrow = "↓" if is_sell else "↑"
    if entry_match:
        data["entry"] = f"{action} @ {entry_match.group(1)}  {arrow}"

    # TP लेवल्स (TP1, TP2, TP3 या सिर्फ TP के बाद की संख्या)
    tp_pattern = re.compile(r'TP\s*(\d)?\s*[:=-]?\s*([0-9]+(?:\.[0-9]+)?)', re.IGNORECASE)
    found_tps = tp_pattern.findall(norm)
    for idx, (tp_num, val) in enumerate(found_tps[:3], 1):
        num = tp_num if tp_num else str(idx)
        data["tps"].append((f"TARGET {num} (TP {num})", val))

    # SL लेवल
    sl_match = re.search(r'SL\s*[:=-]?\s*([0-9]+(?:\.[0-9]+)?)', norm, re.IGNORECASE)
    if sl_match:
        data["sl"] = sl_match.group(1)

    return data

def generate_signal_card(data):
    """फाइनल वीआईपी कार्ड जनरेटर"""
    is_sell = data["is_sell"]
    
    if is_sell:
        bg_color = '#FDF4F4'
        border_color = '#E53E3E'
        header_bg = '#FED7D7'
        header_text = '#C53030'
        pair_bg = '#FFF5F5'
        pair_border = '#FEB2B2'
        action_text = '#E53E3E'
        title = "SELL SIGNAL ALERT  ↓"
    else:
        bg_color = '#F0FAF4'
        border_color = '#2EA043'
        header_bg = '#C6F6D5'
        header_text = '#22543D'
        pair_bg = '#F0FFF4'
        pair_border = '#9AE6B4'
        action_text = '#2EA043'
        title = "BUY SIGNAL ALERT  ↑"

    fig, ax = plt.subplots(figsize=(7, 9.6), dpi=200)
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    outer_box = patches.FancyBboxPatch(
        (0.06, 0.03), 0.88, 0.94,
        boxstyle="round,pad=0.02,rounding_size=0.035",
        linewidth=2.2, edgecolor=border_color, facecolor='#FFFFFF', zorder=1
    )
    ax.add_patch(outer_box)

    # हेडर बॉक्स
    hdr_box = patches.FancyBboxPatch(
        (0.10, 0.84), 0.80, 0.105,
        boxstyle="round,pad=0.015,rounding_size=0.025",
        linewidth=1.2, edgecolor=border_color, facecolor=header_bg, zorder=2
    )
    ax.add_patch(hdr_box)
    ax.text(0.5, 0.902, title, color=header_text, fontsize=16, fontweight='heavy', ha='center', va='center', zorder=3)
    ax.text(0.5, 0.865, "PIPS POWER OFFICIAL | VIP SETUP", color=header_text, fontsize=9.5, fontweight='bold', ha='center', va='center', zorder=3)

    # पेयर & एंट्री बॉक्स
    pair_box = patches.FancyBboxPatch(
        (0.10, 0.72), 0.80, 0.095,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        linewidth=1.0, edgecolor=pair_border, facecolor=pair_bg, zorder=2
    )
    ax.add_patch(pair_box)
    ax.text(0.14, 0.767, f"PAIR : {data['pair']}", color='#2D3748', fontsize=12, fontweight='bold', va='center', zorder=3)
    ax.text(0.86, 0.767, data['entry'], color=action_text, fontsize=13, fontweight='heavy', ha='right', va='center', zorder=3)

    # TP बॉक्सेस
    y_pos = 0.63
    for label, val in data['tps']:
        tp_box = patches.FancyBboxPatch(
            (0.10, y_pos - 0.012), 0.80, 0.062,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            linewidth=0.9, edgecolor='#81E6D9', facecolor='#E6FFFA', zorder=2
        )
        ax.add_patch(tp_box)
        ax.text(0.14, y_pos + 0.019, f">>  {label}", color='#234E52', fontsize=11, fontweight='bold', va='center', zorder=3)
        ax.text(0.86, y_pos + 0.019, val, color='#22543D', fontsize=12, fontweight='heavy', ha='right', va='center', zorder=3)
        y_pos -= 0.072

    # SL बॉक्स
    if data['sl']:
        sl_box = patches.FancyBboxPatch(
            (0.10, y_pos - 0.012), 0.80, 0.062,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            linewidth=0.9, edgecolor='#FEB2B2', facecolor='#FED7D7', zorder=2
        )
        ax.add_patch(sl_box)
        ax.text(0.14, y_pos + 0.019, ">>  STOP LOSS (SL)", color='#742A2A', fontsize=11, fontweight='bold', va='center', zorder=3)
        ax.text(0.86, y_pos + 0.019, data['sl'], color='#C53030', fontsize=12, fontweight='heavy', ha='right', va='center', zorder=3)

    # लोगो लगाना
    if os.path.exists('logo.png'):
        try:
            logo_img = Image.open('logo.png')
            logo_ax = fig.add_axes([0.43, 0.21, 0.14, 0.14], zorder=4)
            logo_ax.imshow(logo_img)
            logo_ax.axis('off')
        except Exception as e:
            print(f"--> Logo load error: {e}")

    # फुटर टेक्स्ट
    ax.text(0.5, 0.14, "Discipline & Risk Management Over Emotion", color='#718096', fontsize=9, style='italic', ha='center', va='center', zorder=3)
    ax.text(0.5, 0.08, "Any query - @PipsFxPower  |  For Educational Purposes", color=border_color, fontsize=10.5, fontweight='bold', ha='center', va='center', zorder=3)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor=bg_color)
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
        print(f"--> Crop error: {e}")
        return False

@user_client.on(events.NewMessage)
async def new_message_handler(event):
    if event.chat_id == SOURCE_CHAT:
        raw_text = event.message.text or ""
        cleaned = clean_text(raw_text)
        
        try:
            # 1. चार्ट इमेज
            if event.message.photo:
                path = await event.message.download_media()
                c_path = f"c_{path}"
                send_path = c_path if crop_image(path, c_path) else path
                
                await bot_client.send_file(TARGET_CHAT, file=send_path, caption=cleaned, parse_mode='md')
                if os.path.exists(path): os.remove(path)
                if os.path.exists(c_path): os.remove(c_path)

            # 2. अन्य मीडिया
            elif event.message.media:
                path = await event.message.download_media()
                await bot_client.send_file(TARGET_CHAT, file=path, caption=cleaned, parse_mode='md')
                if os.path.exists(path): os.remove(path)

            # 3. टेक्स्ट संदेश
            else:
                if is_trading_signal(raw_text):
                    parsed = parse_signal(raw_text)
                    card_buf = generate_signal_card(parsed)
                    card_buf.name = "signal.png"
                    
                    # बिना किसी टेक्स्ट कैप्शन के केवल कार्ड भेजा जाएगा
                    await bot_client.send_file(TARGET_CHAT, file=card_buf)
                else:
                    if cleaned:
                        await bot_client.send_message(TARGET_CHAT, cleaned, parse_mode='md')

        except Exception as e:
            print(f"--> Error: {e}")

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
    print("--> Bot starting...")
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    await start_web_server()
    print(">>> 24/7 Automation Live <<<")
    await user_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
