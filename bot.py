import telebot
import sqlite3
import random
from datetime import datetime
import os
from flask import Flask, request
import requests

# إعداد البوت وقاعدة البيانات
API_TOKEN = os.environ.get("7231107818:AAGGlGgJOMTDm5PlhsCBZyX6_HSAGp_2SX8")  # احفظ رمز البوت كمتغير بيئي
bot = telebot.TeleBot("7231107818:AAGGlGgJOMTDm5PlhsCBZyX6_HSAGp_2SX8")

# إعداد القناة (استبدل '<@Caststone14>' باسم قناتك)
CHANNEL_USERNAME = '@your_channel_username'

# إنشاء تطبيق Flask لدعم Webhook
app = Flask(__name__)

# دالة لإنشاء قائمة رئيسية بالأزرار
def create_main_menu():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("دعم فني", callback_data='support'))
    keyboard.add(telebot.types.InlineKeyboardButton("نقاطي", callback_data='points'))
    keyboard.add(telebot.types.InlineKeyboardButton("رابط إحالة", callback_data='referral_link'))
    keyboard.add(telebot.types.InlineKeyboardButton("إحصائيات الأداء", callback_data='stats'))
    keyboard.add(telebot.types.InlineKeyboardButton("تحليل سلوكي", callback_data='behavior_analysis'))
    keyboard.add(telebot.types.InlineKeyboardButton("الألعاب التفاعلية", callback_data='interactive_games'))
    return keyboard

# إعداد قاعدة البيانات
def setup_database():
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            points INTEGER DEFAULT 0,
            last_guess_game DATE,
            referrer_id INTEGER,
            referred_count INTEGER DEFAULT 0
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_behavior (
            user_id INTEGER,
            games_played INTEGER DEFAULT 0,
            last_game_date DATE,
            active_times TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        conn.commit()

setup_database()

# أوامر البوت
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    referrer_id = None
    if len(message.text.split()) > 1:
        referrer_id = int(message.text.split()[1])

    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, points, last_guess_game, referrer_id) VALUES (?, 0, NULL, ?)", (user_id, referrer_id))
        if referrer_id:
            cursor.execute("UPDATE users SET referred_count = referred_count + 1 WHERE user_id = ?", (referrer_id,))
        cursor.execute("INSERT OR IGNORE INTO user_behavior (user_id) VALUES (?)", (user_id,))
        conn.commit()

    bot.send_message(message.chat.id, "مرحباً بك! استخدم الأزرار أدناه.", reply_markup=create_main_menu())

# عرض نقاط المستخدم
@bot.callback_query_handler(func=lambda call: call.data == 'points')
def points(call):
    user_id = call.from_user.id
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        points = result[0] if result else 0

    bot.send_message(call.message.chat.id, f"نقاطك: {points}", reply_markup=create_main_menu())

# إرسال رابط الإحالة
@bot.callback_query_handler(func=lambda call: call.data == 'referral_link')
def referral_link(call):
    user_id = call.from_user.id
    referral_link = f"https://t.me/yourbot?start={user_id}"
    bot.send_message(call.message.chat.id, f"رابط إحالتك: {referral_link}", reply_markup=create_main_menu())

# دعم فني
@bot.callback_query_handler(func=lambda call: call.data == 'support')
def support(call):
    bot.send_message(call.message.chat.id, "للدعم الفني، يرجى التواصل عبر البريد الإلكتروني: support@example.com", reply_markup=create_main_menu())

# إحصائيات الأداء
@bot.callback_query_handler(func=lambda call: call.data == 'stats')
def stats(call):
    user_id = call.from_user.id
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT referred_count, points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        referred_count = result[0] if result else 0
        points = result[1] if result else 0

    bot.send_message(call.message.chat.id, f"عدد الأشخاص الذين قمت بإحالتهم: {referred_count}\nنقاطك: {points}", reply_markup=create_main_menu())

# تحليل سلوكي
@bot.callback_query_handler(func=lambda call: call.data == 'behavior_analysis')
def behavior_analysis(call):
    user_id = call.from_user.id
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT games_played, last_game_date, active_times FROM user_behavior WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result:
            games_played = result[0]
            last_game_date = result[1]
            active_times = result[2]
            bot.send_message(call.message.chat.id, f"عدد الألعاب التي لعبتها: {games_played}\nآخر لعبة لعبتها في: {last_game_date}\nأوقات نشاطك: {active_times}", reply_markup=create_main_menu())
        else:
            bot.send_message(call.message.chat.id, "لا توجد بيانات سلوكية متاحة.", reply_markup=create_main_menu())

# الألعاب التفاعلية
@bot.callback_query_handler(func=lambda call: call.data == 'interactive_games')
def interactive_games(call):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("لعبة التخمين", callback_data='guess_game'))
    bot.send_message(call.message.chat.id, "اختر لعبة تفاعلية!", reply_markup=keyboard)

# دالة للتحقق مما إذا كان المستخدم مشتركًا في القناة
def is_user_subscribed(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        return False

# لعبة التخمين
@bot.callback_query_handler(func=lambda call: call.data == 'guess_game')
def guess_game(call):
    user_id = call.from_user.id

    if not is_user_subscribed(user_id):
        bot.send_message(call.message.chat.id, "يجب عليك الاشتراك في القناة للعب هذه اللعبة. يرجى الاشتراك ثم إعادة تشغيل البوت.", reply_markup=create_main_menu())
        return

    today = datetime.now().date()
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_guess_game FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if result and result[0] == str(today):
            bot.send_message(call.message.chat.id, "لقد لعبت لعبة التخمين اليوم بالفعل. يمكنك اللعب مرة أخرى غدًا.", reply_markup=create_main_menu())
            return

        cursor.execute("UPDATE users SET last_guess_game = ? WHERE user_id = ?", (today, user_id))
        conn.commit()

    number_to_guess = random.randint(1, 10)
    attempts = 0

    bot.send_message(call.message.chat.id, "لديك 3 محاولات لتخمين الرقم بين 1 و 10. اكتب تخمينك:")

    def check_guess(user_guess):
        nonlocal attempts
        attempts += 1
        if user_guess == number_to_guess:
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET points = points + 1 WHERE user_id = ?", (user_id,))
                conn.commit()
            bot.send_message(call.message.chat.id, "مبروك! لقد خمنت الرقم بشكل صحيح. لقد ربحت نقطة واحدة.", reply_markup=create_main_menu())
        else:
            if attempts < 3:
                bot.send_message(call.message.chat.id, f"خاطئ! لديك {3 - attempts} محاولات متبقية. اكتب تخمينك التالي:")
            else:
                bot.send_message(call.message.chat.id, f"لقد خسرت! الرقم الصحيح كان {number_to_guess}. يمكنك اللعب مرة أخرى غدًا.", reply_markup=create_main_menu())

    def handle_guess(m):
        if m.from_user.id == user_id:
            try:
                user_guess = int(m.text)
                check_guess(user_guess)
                if attempts < 3 and user_guess != number_to_guess:
                    bot.register_next_step_handler(m, handle_guess)
            except ValueError:
                bot.send_message(m.chat.id, "يرجى إدخال رقم صحيح بين 1 و 10.")
                bot.register_next_step_handler(m, handle_guess)

    bot.register_next_step_handler(call.message, handle_guess)

# تفعيل Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    json_data = request.get_json()
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return "ok"

# تعيين Webhook
def set_webhook():
    webhook_url = f'https://<your-service-name>.onrender.com/webhook'
    response = requests.get(f'https://api.telegram.org/bot{API_TOKEN}/setWebhook?url={webhook_url}')
    return response.json()

if __name__ == '__main__':
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
