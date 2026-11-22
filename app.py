import telebot
from telebot import types
from flask import Flask, request
import sqlite3
import os

# ================= تنظیمات =================
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID'))
CHANNEL_USERNAME = os.environ.get('CHANNEL_USERNAME')
# ===========================================

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(name)

conn = sqlite3.connect('movies.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS movies 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, link TEXT)''')
conn.commit()

def check_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    if len(message.text.split()) > 1:
        movie_id = message.text.split()[1]
        if check_membership(message.from_user.id):
            cursor.execute("SELECT name, link FROM movies WHERE id=?", (movie_id,))
            result = cursor.fetchone()
            if result:
                bot.send_message(message.chat.id, f"🎬 فیلم: {result[0]}\n\n🔗 لینک دانلود:\n{result[1]}")
            else:
                bot.send_message(message.chat.id, "❌ متاسفانه این فیلم پیدا نشد.")
        else:
            markup = types.InlineKeyboardMarkup()
            btn_join = types.InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
            btn_check = types.InlineKeyboardButton("✅ عضو شدم", callback_data=f"check_{movie_id}")
            markup.add(btn_join, btn_check)
            bot.send_message(message.chat.id, "⚠️ برای دریافت لینک فیلم، ابتدا باید در کانال ما عضو شوید:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "سلام! به ربات فیلم خوش آمدید 👋")

@bot.callback_query_handler(func=lambda call: call.data.startswith('check_'))
def callback_check(call):
    movie_id = call.data.split('_')[1]
    if check_membership(call.from_user.id):
        cursor.execute("SELECT name, link FROM movies WHERE id=?", (movie_id,))
        result = cursor.fetchone()
        if result:
            bot.answer_callback_query(call.id, "✅ عضویت تایید شد!")
            bot.send_message(call.message.chat.id, f"🎬 فیلم: {result[0]}\n\n🔗 لینک دانلود:\n{result[1]}")
    else:
        bot.answer_callback_query(call.id, "❌ شما هنوز عضو کانال نشده‌اید!", show_alert=True)

@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔️ شما اجازه این کار را ندارید.")
        return
    try:
        text = message.text.replace('/add ', '')
        name, link = text.split('|')
        cursor.execute("INSERT INTO movies (name, link) VALUES (?, ?)", (name.strip(), link.strip()))
        conn.commit()
        movie_id = cursor.lastrowid
        bot_username = bot.get_me().username
        final_link = f"https://t.me/{bot_username}?start={movie_id}"
        bot.reply_to(message, f"✅ فیلم با موفقیت اضافه شد!\n\nلینک اختصاصی:\n{final_link}", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "❌ فرمت اشتباه است!\nدستور را به این شکل بفرستید:\n/add نام فیلم | لینک دانلود")

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://' + os.environ.get('RENDER_EXTERNAL_HOSTNAME') + '/' + BOT_TOKEN)
    return "ربات با موفقیت تنظیم شد!", 200

if name == "main":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
