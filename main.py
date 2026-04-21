import telebot
import websocket
import json
import threading
import pytz
from datetime import datetime
from telebot import types

# --- بيانات البوت ---
TOKEN = "8176918240:AAH1OD1xDDSQJlqGRwcut71PYWaLcnkT6qM"
bot = telebot.TeleBot(TOKEN)

# مخزن الأسعار اللحظية
prices = {"BTCUSDT": 0, "PAXGUSDT": 0}
user_choice = {}

# --- اتصال البث المباشر (WebSocket) ---
def on_message(ws, message):
    data = json.loads(message)
    if 's' in data and 'c' in data:
        prices[data['s']] = float(data['c'])

def run_stream():
    # فتح قناة بث مباشرة للذهب وسمارتي
    url = "wss://stream.binance.com:9443/ws/btcusdt@ticker/paxgusdt@ticker"
    ws = websocket.WebSocketApp(url, on_message=on_message)
    ws.run_forever()

# تشغيل البث في الخلفية
threading.Thread(target=run_stream, daemon=True).start()

def generate_signal(symbol):
    price = prices.get(symbol, 0)
    if price == 0: return "جاري صيد السعر...", "ثواني", 0
    
    last_digit = int(str(price)[-1])
    direction = "شراء 🟢" if last_digit % 2 == 0 else "بيع 🔴"
    dur = f"{30 + (last_digit * 3)} ثانية"
    strength = 90.0 + (last_digit / 2)
    return direction, dur, strength

@bot.message_handler(commands=['start'])
def start(m):
    kb = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb.add("🟡 سوق الذهب (XAU/USD)", "🧠 مؤشر سمارتي (Smarty)", "ارسل اشاره 🎯")
    bot.send_message(m.chat.id, "أهلاً علي! نظام البث المباشر متصل وجاهز 🚀", reply_markup=kb)

@bot.message_handler(func=lambda m: True)
def handle(m):
    cid = m.chat.id
    if "الذهب" in m.text: 
        user_choice[cid] = "PAXGUSDT"
        bot.send_message(cid, "تم تفعيل رادار الذهب اللحظي 🟡")
    elif "سمارتي" in m.text: 
        user_choice[cid] = "BTCUSDT"
        bot.send_message(cid, "تم تفعيل مؤشر سمارتي الذكي 🧠")
    elif m.text == "ارسل اشاره 🎯":
        sym = user_choice.get(cid)
        if not sym: return bot.send_message(cid, "حدد السوق أولاً!")
        
        dr, du, st = generate_signal(sym)
        tm = datetime.now(pytz.timezone('Asia/Riyadh')).strftime('%I:%M:%S %p')
        
        msg = (f"**🎯 إشارة بث مباشر (فورية)**\n\n"
               f"**السوق:** {sym}\n"
               f"**الاتجاه:** {dr}\n"
               f"**المدة:** {du}\n"
               f"**القوة:** {st}%\n\n"
               f"⏰ {tm}")
        bot.send_message(cid, msg, parse_mode="Markdown")

bot.polling(none_stop=True)
