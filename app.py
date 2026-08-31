import os
import threading
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask

TOKEN = "8226487699:AAGQdfgbudiw3FWIJsidwfvmJ5AhxaHvNLk"
ADMIN_ID = 666875325
ADMIN_USERNAME = "HyperConn"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_pending_purchase = {}

@app.route('/')
def home():
    return "HyperConn Bot is running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def is_admin(user_id):
    return user_id == ADMIN_ID

def get_main_reply_markup(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("⚡ خرید کانفیگ"), KeyboardButton("👤 حساب کاربری و تعرفه‌ها"))
    markup.add(KeyboardButton("📞 پشتیبانی HyperConn"))
    if is_admin(user_id):
        markup.add(KeyboardButton("⚙️ پنل مدیریت ادمین"))
    return markup

categories = ["eco_single", "eco_double", "pro_single", "pro_double"]

plan_details = {
    "eco_single": {"name": "پکیج اقتصادی - ۱ کاربره", "price": "290,000 تومان"},
    "eco_double": {"name": "پکیج اقتصادی - ۲ کاربره", "price": "380,000 تومان"},
    "pro_single": {"name": "پکیج حرفه‌ای - ۱ کاربره", "price": "390,000 تومان"},
    "pro_double": {"name": "پکیج حرفه‌ای - ۲ کاربره", "price": "540,000 تومان"},
}

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

def get_stock_count(category):
    filename = f"{category}.txt"
    if not os.path.exists(filename):
        return 0
    with open(filename, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return len(lines)

def clear_warehouse(category):
    filename = f"{category}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("")

def get_card():
    if not os.path.exists("card.txt"):
        return "هنوز شماره کارتی ثبت نشده است"
    with open("card.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

def save_card(card_text):
    with open("card.txt", "w", encoding="utf-8") as f:
        f.write(card_text.strip())

def get_admin_panel_data():
    current_card = get_card()
    markup = InlineKeyboardMarkup()
    for cat in categories:
        count = get_stock_count(cat)
        p_name = plan_details[cat]['name']
        markup.add(InlineKeyboardButton(f"➕ افزودن {p_name} ({count} عدد)", callback_data=f"add_{cat}"))
        markup.add(InlineKeyboardButton(f"🗑 خالی کردن انبار {p_name}", callback_data=f"clear_{cat}"))
    markup.add(InlineKeyboardButton("💳 تغییر شماره کارت بانکی", callback_data="edit_card"))
    markup.add(InlineKeyboardButton("❌ خروج از پنل", callback_data="exit_admin"))
    
    text_msg = "⚙️ **پنل مدیریت انبارها و کارت**\n\n📊 **موجودی انبارها:**\n"
    for cat in categories:
        text_msg += f"- {plan_details[cat]['name']}: `{get_stock_count(cat)}` کانفیگ\n"
    text_msg += f"\n💳 **شماره کارت فعلی:**\n`{current_card}`"
    return text_msg, markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user_pending_purchase.pop(message.from_user.id, None)
        markup = get_main_reply_markup(message.from_user.id)
        bot.send_message(message.chat.id, "به ربات **HyperConn** خوش آمدید. از دکمه‌های زیر استفاده کنید:", parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(e)

@bot.message_handler(func=lambda message: message.text in ["⚡ خرید کانفیگ", "👤 حساب کاربری و تعرفه‌ها", "📞 پشتیبانی HyperConn", "⚙️ پنل مدیریت ادمین"])
def handle_reply_buttons(message):
    user_id = message.from_user.id
    text = message.text
    
    if text == "⚡ خرید کانفیگ":
        user_pending_purchase.pop(user_id, None)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🛡 پکیج اقتصادی", callback_data="menu_eco"))
        markup.add(InlineKeyboardButton("⚡ پکیج حرفه‌ای", callback_data="menu_pro"))
        bot.send_message(message.chat.id, "لطفاً پکیج مورد نظر خود را انتخاب کنید:", reply_markup=markup)
        
    elif text == "👤 حساب کاربری و تعرفه‌ها":
        bot.send_message(message.chat.id, "اطلاعات حساب کاربری شما ثبت است.")
        
    elif text == "📞 پشتیبانی HyperConn":
        bot.send_message(message.chat.id, f"برای ارتباط با پشتیبانی به ادمین پیام دهید:\n@{ADMIN_USERNAME}")
        
    elif text == "⚙️ پنل مدیریت ادمین" and is_admin(user_id):
        text_msg, markup = get_admin_panel_data()
        bot.send_message(message.chat.id, text_msg, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "buy_menu")
def buy_menu(call):
    user_pending_purchase.pop(call.from_user.id, None)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛡 پکیج اقتصادی", callback_data="menu_eco"))
    markup.add(InlineKeyboardButton("⚡ پکیج حرفه‌ای", callback_data="menu_pro"))
    bot.edit_message_text("لطفاً پکیج مورد نظر خود را انتخاب کنید:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "menu_eco")
def menu_eco(call):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👤 ۱ کاربره (290 ت)", callback_data="price_eco_single"))
    markup.add(InlineKeyboardButton("👥 ۲ کاربره (380 ت)", callback_data="price_eco_double"))
    markup.add(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="buy_menu"))
    bot.edit_message_text("🛡 پکیج اقتصادی را انتخاب کردید، نوع کاربره را مشخص کنید:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "menu_pro")
def menu_pro(call):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👤 ۱ کاربره (390 ت)", callback_data="price_pro_single"))
    markup.add(InlineKeyboardButton("👥 ۲ کاربره (540 ت)", callback_data="price_pro_double"))
    markup.add(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="buy_menu"))
    bot.edit_message_text("⚡ پکیج حرفه‌ای را انتخاب کردید، نوع کاربره را مشخص کنید:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("price_"))
def show_price_and_confirm(call):
    category = call.data.replace("price_", "")
    
    if get_stock_count(category) <= 0:
        bot.answer_callback_query(call.id, "❌ متأسفانه موجودی این پلن در حال حاضر تمام شده است (انبار خالی است).", show_alert=True)
        return

    p_info = plan_details.get(category, {})
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ تایید و دریافت شماره کارت", callback_data=f"card_{category}"))
    markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
    
    text = (
        f"📋 **اطلاعات سرویس انتخابی:**\n\n"
        f"📦 پلن: **{p_info.get('name')}**\n"
        f"💰 قیمت نهایی: **{p_info.get('price')}**\n\n"
        f"آیا مایل به ادامه خرید و دریافت شماره کارت هستید؟"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("card_"))
def ask_for_receipt(call):
    category = call.data.replace("card_", "")
    
    if get_stock_count(category) <= 0:
        bot.answer_callback_query(call.id, "❌ متأسفانه در این فاصله موجودی این پلن تمام شد!", show_alert=True)
        return

    user_pending_purchase[call.from_user.id] = category
    card = get_card()
    p_info = plan_details.get(category, {})
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
    
    text = (
        f"💳 **شماره کارت برای واریز وجه:**\n`{card}`\n\n"
        f"🏷 پلن: **{p_info.get('name')}**\n"
        f"💰 مبلغ قابل پرداخت: **{p_info.get('price')}**\n\n"
        f"📸 **لطفاً عکس فیش واریزی خود را همینجا ارسال کنید** تا به همراه درخواست خرید برای ادمین ارسال شود:"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(content_types=['photo', 'text'])
def handle_user_receipt(message):
    if message.from_user.id == ADMIN_ID:
        return
    
    if message.text in ["⚡ خرید کانفیگ", "👤 حساب کاربری و تعرفه‌ها", "📞 پشتیبانی HyperConn", "⚙️ پنل مدیریت ادمین"]:
        return

    user_id = message.from_user.id
    if user_id not in user_pending_purchase:
        return
    
    category = user_pending_purchase.pop(user_id)
    p_info = plan_details.get(category, {})
    p_name = p_info.get('name', 'سرویس')
    
    user = message.from_user
    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(InlineKeyboardButton("✅ تایید و ارسال کانفیگ", callback_data=f"approve_{user.id}_{category}"))
    admin_markup.add(InlineKeyboardButton("❌ رد درخواست", callback_data=f"reject_{user.id}"))
    
    user_info = f"@{user.username}" if user.username else "بدون یوزرنیم"
    caption = (
        f"🚨 **درخواست خرید جدید و فیش واریزی!**\n\n"
        f"👤 کاربر: {user.first_name} ({user_info})\n"
        f"🆔 آیدی کاربر: `{user.id}`\n"
        f"📦 پلن درخواستی: `{p_name}`"
    )
    
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
            bot.send_photo(ADMIN_ID, file_id, caption=caption, parse_mode="Markdown", reply_markup=admin_markup)
        else:
            bot.send_message(ADMIN_ID, caption + f"\n\n💬 **متن کاربر:**\n{message.text}", parse_mode="Markdown", reply_markup=admin_markup)
        
        bot.send_message(message.chat.id, "✅ فیش واریزی شما با موفقیت برای ادمین ارسال شد. پس از بررسی و تایید، کانفیگ اختصاصی‌تان ارسال خواهد شد.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا در ارسال فیش: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def admin_action(call):
    if not is_admin(call.from_user.id):
        return
    
    parts = call.data.split("_")
    action = parts[0]
    target_user_id = int(parts[1])
    
    if action == "approve":
        # اصلاح کلیدی: چون نام دسته‌بندی خودش شامل زیرخط است (مثل eco_single)، تمام بخش‌های بعدی را به هم می‌چسبانیم
        category = "_".join(parts[2:])
        
        config = get_config(category)
        if not config:
            bot.answer_callback_query(call.id, f"❌ انبار این پلن ({plan_details.get(category, {}).get('name')}) خالی است!", show_alert=True)
            return
        
        try:
            bot.send_message(target_user_id, f"✅ فیش شما تایید شد! این هم کانفیگ اختصاصی شما:\n\n`{config}`", parse_mode="Markdown")
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ خطا در ارسال به کاربر: {e}", show_alert=True)
            return
        
        if call.message.photo:
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=f"✅ **تایید شد و کانفیگ ارسال گردید:**\n`{config}`", parse_mode="Markdown")
        else:
            bot.edit_message_text(f"✅ **تایید شد و کانفیگ ارسال گردید:**\n`{config}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "کانفیگ ارسال شد.")
        
    elif action == "reject":
        try:
            bot.send_message(target_user_id, "❌ فیش واریزی شما توسط ادمین رد شد یا نامعتبر بود. در صورت سوال به پشتیبانی پیام دهید.")
        except:
            pass
        if call.message.photo:
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption="❌ **این درخواست توسط شما رد شد.**", parse_mode="Markdown")
        else:
            bot.edit_message_text("❌ **این درخواست توسط شما رد شد.**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "درخواست رد شد.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("clear_"))
def handle_clear_warehouse(call):
    if not is_admin(call.from_user.id):
        return
    cat = call.data.replace("clear_", "")
    clear_warehouse(cat)
    bot.answer_callback_query(call.id, "✅ انبار پاک شد!", show_alert=True)
    
    text_msg, markup = get_admin_panel_data()
    bot.edit_message_text(text_msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "exit_admin")
def exit_admin(call):
    if not is_admin(call.from_user.id):
        return
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        bot.edit_message_text("❌ پنل مدیریت بسته شد.", call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.answer_callback_query(call.id, "از پنل مدیریت خارج شدید.")

@bot.callback_query_handler(func=lambda call: call.data == "edit_card")
def ask_for_card(call):
    if not is_admin(call.from_user.id):
        return
    msg = bot.send_message(call.message.chat.id, "لطفاً شماره کارت جدید را بفرستید:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_card_step)

def save_card_step(message):
    if not is_admin(message.from_user.id):
        return
    save_card(message.text)
    bot.send_message(message.chat.id, f"✅ شماره کارت ثبت شد:\n\n`{message.text}`", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_"))
def ask_for_config(call):
    if not is_admin(call.from_user.id):
        return
    cat = call.data.replace("add_", "")
    msg = bot.send_message(call.message.chat.id, f"کانفیگ‌های مربوط به **{plan_details[cat]['name']}** را بفرستید (هر خط یک کانفیگ):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_config_step, cat)

def save_config_step(message, category):
    if not is_admin(message.from_user.id):
        return
    text = message.text.strip()
    count = 0
    for line in text.split("\n"):
        if line.strip():
            add_config(category, line.strip())
            count += 1
    bot.send_message(message.chat.id, f"✅ تعداد {count} کانفیگ به **{plan_details[category]['name']}** اضافه شد!")

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    bot.infinity_polling(skip_pending=True)
