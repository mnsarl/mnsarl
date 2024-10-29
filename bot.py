import telebot
import sqlite3
import random
from datetime import datetime

# إعداد البوت وقاعدة البيانات
API_TOKEN = '7231107818:AAGGlGgJOMTDm5PlhsCBZyX6_HSAGp_2SX8'  # ضع هنا رمز البوت الخاص بك
bot = telebot.TeleBot(API_TOKEN)

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('users.db', check_same_thread=False)

# إنشاء الجداول إذا لم تكن موجودة
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    last_guess_game DATE,
    referrer_id INTEGER,
    referred_count INTEGER DEFAULT 0
)''')

# جدول تحليل سلوكي للمستخدمين
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_behavior (
    user_id INTEGER,
    games_played INTEGER DEFAULT 0,
    last_game_date DATE,
    active_times TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)''')
conn.commit()

# دالة لإرسال زر مختصر
def create_main_menu():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("دعم فني", callback_data='support'))
    keyboard.add(telebot.types.InlineKeyboardButton("نقاطي", callback_data='points'))
    keyboard.add(telebot.types.InlineKeyboardButton("رابط إحالة", callback_data='referral_link'))
    keyboard.add(telebot.types.InlineKeyboardButton("إحصائيات الأداء", callback_data='stats'))
    keyboard.add(telebot.types.InlineKeyboardButton("تحليل سلوكي", callback_data='behavior_analysis'))
    keyboard.add(telebot.types.InlineKeyboardButton("الألعاب التفاعلية", callback_data='interactive_games'))
    return keyboard

# استجابة للأوامر
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    referrer_id = None
    if len(message.text.split()) > 1:
        referrer_id = int(message.text.split()[1])
    
    cursor.execute("INSERT OR IGNORE INTO users (user_id, points, last_guess_game, referrer_id) VALUES (?, 0, NULL, ?)", (user_id, referrer_id))
    if referrer_id:
        cursor.execute("UPDATE users SET referred_count = referred_count + 1 WHERE user_id = ?", (referrer_id,))
    conn.commit()

    # إضافة المستخدم إلى جدول تحليل سلوكي إذا لم يكن موجودًا
    cursor.execute("INSERT OR IGNORE INTO user_behavior (user_id) VALUES (?)", (user_id,))
    conn.commit()

    bot.send_message(message.chat.id, "مرحباً بك! استخدم الأزرار أدناه.", reply_markup=create_main_menu())

# دالة لنقاط المستخدم
@bot.callback_query_handler(func=lambda call: call.data == 'points')
def points(call):
    user_id = call.from_user.id
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    points = result[0] if result else 0
    bot.send_message(call.message.chat.id, f"نقاطك: {points}", reply_markup=create_main_menu())

# دالة للرابط الإحالي
@bot.callback_query_handler(func=lambda call: call.data == 'referral_link')
def referral_link(call):
    user_id = call.from_user.id
    referral_link = f"https://t.me/yourbot?start={user_id}"
    bot.send_message(call.message.chat.id, f"رابط إحالتك: {referral_link}", reply_markup=create_main_menu())

# دالة للدعم الفني
@bot.callback_query_handler(func=lambda call: call.data == 'support')
def support(call):
    bot.send_message(call.message.chat.id, "للدعم الفني، يرجى التواصل عبر البريد الإلكتروني: support@example.com", reply_markup=create_main_menu())

# دالة لعرض إحصائيات الأداء
@bot.callback_query_handler(func=lambda call: call.data == 'stats')
def stats(call):
    user_id = call.from_user.id
    cursor.execute("SELECT referred_count, points FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    referred_count = result[0] if result else 0
    points = result[1] if result else 0
    bot.send_message(call.message.chat.id, f"عدد الأشخاص الذين قمت بإحالتهم: {referred_count}\nنقاطك: {points}", reply_markup=create_main_menu())

# دالة لتحليل سلوكي
@bot.callback_query_handler(func=lambda call: call.data == 'behavior_analysis')
def behavior_analysis(call):
    user_id = call.from_user.id
    cursor.execute("SELECT games_played, last_game_date, active_times FROM user_behavior WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        games_played = result[0]
        last_game_date = result[1]
        active_times = result[2]
        bot.send_message(call.message.chat.id, f"عدد الألعاب التي لعبتها: {games_played}\nآخر لعبة لعبتها في: {last_game_date}\nأوقات نشاطك: {active_times}", reply_markup=create_main_menu())
    else:
        bot.send_message(call.message.chat.id, "لا توجد بيانات سلوكية متاحة.", reply_markup=create_main_menu())

# دالة للألعاب التفاعلية
@bot.callback_query_handler(func=lambda call: call.data == 'interactive_games')
def interactive_games(call):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("لعبة التخمين", callback_data='guess_game'))
    bot.send_message(call.message.chat.id, "اختر لعبة تفاعلية!", reply_markup=keyboard)

# دالة لعبة التخمين
@bot.callback_query_handler(func=lambda call: call.data == 'guess_game')
def guess_game(call):
    user_id = call.from_user.id
    today = datetime.now().date()

    # التأكد من أن المستخدم موجود في قاعدة البيانات أو إضافته
    cursor.execute("SELECT last_guess_game FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    # التحقق إذا لعب المستخدم اليوم
    if result and result[0] == str(today):
        bot.send_message(call.message.chat.id, "لقد لعبت لعبة التخمين اليوم بالفعل. يمكنك اللعب مرة أخرى غدًا.", reply_markup=create_main_menu())
        return
    elif not result:
        cursor.execute("INSERT INTO users (user_id, points, last_guess_game) VALUES (?, 0, ?)", (user_id, today))
    else:
        cursor.execute("UPDATE users SET last_guess_game = ? WHERE user_id = ?", (today, user_id))

    # تحديث سلوك المستخدم
    cursor.execute("UPDATE user_behavior SET games_played = games_played + 1, last_game_date = ? WHERE user_id = ?", (today, user_id))
    conn.commit()

    number_to_guess = random.randint(1, 10)
    attempts = 0

    bot.send_message(call.message.chat.id, "لديك 3 محاولات لتخمين الرقم بين 1 و 10. اكتب تخمينك:")

    # دالة للتحقق من التخمين
    def check_guess(user_guess):
        nonlocal attempts
        attempts += 1
        
        if user_guess == number_to_guess:
            cursor.execute("UPDATE users SET points = points + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            bot.send_message(call.message.chat.id, "مبروك! لقد خمنت الرقم بشكل صحيح. لقد ربحت نقطة واحدة.", reply_markup=create_main_menu())
        else:
            if attempts < 3:
                bot.send_message(call.message.chat.id, f"خاطئ! لديك {3 - attempts} محاولات متبقية. اكتب تخمينك التالي:")
            else:
                bot.send_message(call.message.chat.id, f"لقد خسرت! الرقم الصحيح كان {number_to_guess}. يمكنك اللعب مرة أخرى غدًا.", reply_markup=create_main_menu())

    # دالة للتعامل مع التخمينات
    def handle_guess(m):
        if m.from_user.id == user_id:
            try:
                user_guess = int(m.text)
                check_guess(user_guess)
                if attempts < 3 and user_guess != number_to_guess:
                    bot.register_next_step_handler(m, handle_guess)  # استمر في الانتظار لتخمين آخر
            except ValueError:
                bot.send_message(m.chat.id, "يرجى إدخال رقم صحيح بين 1 و 10.")
                bot.register_next_step_handler(m, handle_guess)  # الانتظار لتخمين آخر

    bot.register_next_step_handler(call.message, handle_guess)  # بدء معالجة التخمينات

# تشغيل البوت
if __name__ == '__main__':
    bot.polling()
