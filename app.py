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

# توابع مدیریت فایل انبار کانفیگ‌ها (حذف خودکار بعد از فروش)
def get_config(category):
    filename = f"{category}.txt"
    if not os.path.exists(filename):
        return None
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    if not lines:
        return None
    
    config = lines[0].strip()
    remaining = lines[1:]
    
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(remaining)
        
    return config

def add_config(category, config_text):
    filename = f"{category}.txt"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(config_text + "\n")

# توابع مدیریت شماره کارت
def get_card():
    if not os.path.exists("card.txt"):
        return "شماره کارتی ثبت نشده است."
    with open("card.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

def save_card(card_text):
    with open("card.txt", "w", encoding="utf-8") as f:
        f.write(card_text.strip())

# منوی اصلی
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👤 حساب کاربری و تعرفه‌ها", callback_data="account"))
    markup.add(InlineKeyboardButton("⚡ خرید کانفیگ (VIP / CIP / تک‌کاربره)", callback_data="buy_menu"))
    markup.add(InlineKeyboardButton("📞 پشتیبانی HyperConn", callback_data="support"))
    
    if is_admin(message.from_user):
        markup.add(InlineKeyboardButton("⚙️ پنل مدیریت ادمین", callback_data="admin_panel"))
        
    bot.send_message(message.chat.id, f"به منوی اصلی **HyperConn** خوش آمدید:", parse_mode="Markdown", reply_markup=markup)

# منوی خرید و نمایش شماره کارت
@bot.callback_query_handler(func=lambda call: call.data == "buy_menu")
def buy_menu(call):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💎 خرید VIP", callback_data="get_vip"))
    markup.add(InlineKeyboardButton("🚀 خرید CIP", callback_data="get_cip"))
    markup.add(InlineKeyboardButton("👤 خرید تک‌کاربره", callback_data="get_single"))
    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_home"))
    
    card = get_card()
    text = f"لطفاً پلن مورد نظر خود را انتخاب کنید:\n\n💳 **شماره کارت برای واریز:**\n`{card}`\n\nپس از واریز، فیش خود را به پشتیبانی ارسال کنید."
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# تحویل خودکار کانفیگ و کسر از انبار
@bot.callback_query_handler(func=lambda call: call.data in ["get_vip", "get_cip", "get_single"])
def process_purchase(call):
    cat_map = {"get_vip": "vip", "get_cip": "cip", "get_single": "single"}
    category = cat_map[call.data]
    
    config = get_config(category)
    if not config:
        bot.answer_callback_query(call.id, "❌ متأسفانه انبار این پلن در حال حاضر خالی است!", show_alert=True)
        return
        
    bot.send_message(call.message.chat.id, f"✅ خرید شما با موفقیت انجام شد و کانفیگ اختصاصی‌تان از انبار کسر گردید:\n\n`{config}`", parse_mode="Markdown")
    bot.answer_callback_query(call.id, "کانفیگ شما ارسال شد!")

# پنل مدیریت ادمین
@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if not is_admin(call.from_user):
        return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ افزودن کانفیگ VIP", callback_data="add_vip"))
    markup.add(InlineKeyboardButton("➕ افزودن کانفیگ CIP", callback_data="add_cip"))
    markup.add(InlineKeyboardButton("➕ افزودن کانفیگ تک‌کاربره", callback_data="add_single"))
    markup.add(InlineKeyboardButton("💳 تغییر شماره کارت بانکی", callback_data="edit_card"))
    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_home"))
    
    current_card = get_card()
    bot.edit_message_text(f"⚙️ **پنل مدیریت انبار و کارت**\n\nشماره کارت فعلی:\n`{current_card}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

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

@bot.callback_query_handler(func=lambda call: call.data in ["add_vip", "add_cip", "add_single"])
def ask_for_config(call):
    if not is_admin(call.from_user):
        return
    cat = call.data.replace("add_", "")
    msg = bot.send_message(call.message.chat.id, f"لطفاً کانفیگ خامِ مورد نظر برای بخش `{cat}` را بفرستید (می‌توانید چند خطی هم بفرستید):", parse_mode="Markdown")
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
    bot.send_message(message.chat.id, f"✅ تعداد {count} کانفیگ با موفقیت به انبار `{category}` اضافه شدند!")

@bot.callback_query_handler(func=lambda call: call.data == "back_home")
def back_home(call):
    send_welcome(call.message)

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
