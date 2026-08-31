import os
import threading
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask

TOKEN = "8689876289:AAFtWxe-M3JkgHW1x3A5LYXfzQ_q7uI4Az4"
ADMIN_ID = 666875325
ADMIN_USERNAME = "HyperConn"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "HyperConn Bot is running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def is_admin(user):
    if user.id == ADMIN_ID:
        return True
    if user.username and user.username.lower() == ADMIN_USERNAME.lower():
        return True
    return False

# ساخت خودکار فایل‌های انبار ۴گانه و کارت
categories = ["vip_single", "vip_double", "cip_single", "cip_double"]
for cat in categories:
    fname = f"{cat}.txt"
    if not os.path.exists(fname):
        with open(fname, "w", encoding="utf-8") as f:
            f.write("")

if not os.path.exists("card.txt"):
    with open("card.txt", "w", encoding="utf-8") as f:
        f.write("هنوز شماره کارتی ثبت نشده است")

def get_config(category):
    filename = f"{category}.txt"
    if not os.path.exists(filename):
        return None
    with open(filename, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    if not lines:
        return None
    
    config = lines[0]
    remaining = lines[1:]
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(remaining) + ("\n" if remaining else ""))
        
    return config

def add_config(category, config_text):
    filename = f"{category}.txt"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(config_text.strip() + "\n")

def get_card():
    if not os.path.exists("card.txt"):
        return "هنوز شماره کارتی ثبت نشده است"
    with open("card.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

def save_card(card_text):
    with open("card.txt", "w", encoding="utf-8") as f:
        f.write(card_text.strip())

# منوی اصلی
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("👤 حساب کاربری و تعرفه‌ها", callback_data="account"))
        markup.add(InlineKeyboardButton("⚡ خرید کانفیگ (VIP / CIP)", callback_data="buy_menu"))
        markup.add(InlineKeyboardButton("📞 پشتیبانی HyperConn", callback_data="support"))
        
        if is_admin(message.from_user):
            markup.add(InlineKeyboardButton("⚙️ پنل مدیریت ادمین", callback_data="admin_panel"))
            
        bot.send_message(message.chat.id, "به منوی اصلی **HyperConn** خوش آمدید:", parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(f"Error in start: {e}")

# منوی اصلی خرید (انتخاب VIP یا CIP)
@bot.callback_query_handler(func=lambda call: call.data == "buy_menu")
def buy_menu(call):
    try:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💎 کانفیگ‌های VIP", callback_data="menu_vip"))
        markup.add(InlineKeyboardButton("🚀 کانفیگ‌های CIP", callback_data="menu_cip"))
        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_home"))
        
        card = get_card()
        text = f"لطفاً نوع سرویس مورد نظر خود را انتخاب کنید:\n\n💳 **شماره کارت برای واریز:**\n`{card}`\n\nپس از واریز، فیش خود را به پشتیبانی ارسال کنید."
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        bot.answer_callback_query(call.id, "خطایی رخ داد، لطفاً دوباره /start بفرستید.", show_alert=True)

# زیرمنوی VIP (تک کاربره / دو کاربره)
@bot.callback_query_handler(func=lambda call: call.data == "menu_vip")
def menu_vip(call):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👤 VIP تک‌کاربره", callback_data="get_vip_single"))
    markup.add(InlineKeyboardButton("👥 VIP دو کاربره", callback_data="get_vip_double"))
    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="buy_menu"))
    bot.edit_message_text("💎 سرویس VIP مورد نظر را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=markup)

# زیرمنوی CIP (تک کاربره / دو کاربره)
@bot.callback_query_handler(func=lambda call: call.data == "menu_cip")
def menu_cip(call):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👤 CIP تک‌کاربره", callback_data="get_cip_single"))
    markup.add(InlineKeyboardButton("👥 CIP دو کاربره", callback_data="get_cip_double"))
    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="buy_menu"))
    bot.edit_message_text("🚀 سرویس CIP مورد نظر را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=markup)

# تحویل خودکار کانفیگ بر اساس دکمه انتخابی و کسر از انبار مربوطه
@bot.callback_query_handler(func=lambda call: call.data in ["get_vip_single", "get_vip_double", "get_cip_single", "get_cip_double"])
def process_purchase(call):
    try:
        category = call.data.replace("get_", "") # vip_single, vip_double, cip_single, cip_double
        
        config = get_config(category)
        if not config:
            bot.answer_callback_query(call.id, "❌ متأسفانه انبار این پلن در حال حاضر خالی است!", show_alert=True)
            return
            
        bot.send_message(call.message.chat.id, f"✅ خرید شما با موفقیت انجام شد و کانفیگ اختصاصی‌تان از انبار کسر گردید:\n\n`{config}`", parse_mode="Markdown")
        bot.answer_callback_query(call.id, "کانفیگ شما ارسال شد!")
    except Exception as e:
        bot.answer_callback_query(call.id, "خطا در پردازش خرید.", show_alert=True)

# پنل مدیریت ادمین
@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    try:
        if not is_admin(call.from_user):
            return
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("➕ افزودن VIP تک‌کاربره", callback_data="add_vip_single"))
        markup.add(InlineKeyboardButton("➕ افزودن VIP دوکاربره", callback_data="add_vip_double"))
        markup.add(InlineKeyboardButton("➕ افزودن CIP تک‌کاربره", callback_data="add_cip_single"))
        markup.add(InlineKeyboardButton("➕ افزودن CIP دوکاربره", callback_data="add_cip_double"))
        markup.add(InlineKeyboardButton("💳 تغییر شماره کارت بانکی", callback_data="edit_card"))
        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_home"))
        
        current_card = get_card()
        bot.edit_message_text(f"⚙️ **پنل مدیریت انبار و کارت**\n\nشماره کارت فعلی:\n`{current_card}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(f"Error admin_panel: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "edit_card")
def ask_for_card(call):
    if not is_admin(call.from_user):
        return
    msg = bot.send_message(call.message.chat.id, "لطفاً شماره کارت جدید (به همراه نام صاحب کارت) را بفرستید:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_card_step)

def save_card_step(message):
    if not is_admin(message.from_user):
        return
    save_card(message.text)
    bot.send_message(message.chat.id, f"✅ شماره کارت با موفقیت تغییر کرد:\n\n`{message.text}`", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data in ["add_vip_single", "add_vip_double", "add_cip_single", "add_cip_double"])
def ask_for_config(call):
    if not is_admin(call.from_user):
        return
    cat = call.data.replace("add_", "")
    cat_names = {
        "vip_single": "VIP تک‌کاربره",
        "vip_double": "VIP دو کاربره",
        "cip_single": "CIP تک‌کاربره",
        "cip_double": "CIP دو کاربره"
    }
    msg = bot.send_message(call.message.chat.id, f"لطفاً کانفیگ خامِ مورد نظر برای بخش `{cat_names.get(cat, cat)}` را بفرستید (می‌توانید چند خطی هم بفرستید):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_config_step, cat)

def save_config_step(message, category):
    if not is_admin(message.from_user):
        return
    text = message.text.strip()
    count = 0
    for line in text.split("\n"):
        if line.strip():
            add_config(category, line.strip())
            count += 1
    bot.send_message(message.chat.id, f"✅ تعداد {count} کانفیگ با موفقیت به انبار این بخش اضافه شدند!")

@bot.callback_query_handler(func=lambda call: call.data == "back_home")
def back_home(call):
    try:
        send_welcome(call.message)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "account")
def account_info(call):
    bot.answer_callback_query(call.id, "بخش حساب کاربری شما")
    bot.send_message(call.message.chat.id, "اطلاعات حساب کاربری شما در سیستم ثبت است.")

@bot.callback_query_handler(func=lambda call: call.data == "support")
def support_info(call):
    bot.answer_callback_query(call.id, "پشتیبانی")
    bot.send_message(call.message.chat.id, f"برای ارتباط با پشتیبانی و ارسال فیش به ادمین پیام دهید:\n@{ADMIN_USERNAME}")

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    bot.infinity_polling()
