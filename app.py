import os
import threading
import json
from datetime import datetime, timedelta
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask

TOKEN = "8226487699:AAGQdfgbudiw3FWIJsidwfvmJ5AhxaHvNLk"
ADMIN_ID = 666875325
ADMIN_USERNAME = "HyperConn"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_pending_purchase = {}
admin_pending_manual_config = {}

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

# تنظیمات پیش‌فرض گیگ‌ها و قیمت هر گیگ
DEFAULT_DATA = {
    "price_per_gb": 25000,
    "tiers": {
        "vol_5": {"name": "۵ گیگابایت", "gb": 5},
        "vol_10": {"name": "۱۰ گیگابایت", "gb": 10},
        "vol_20": {"name": "۲۰ گیگابایت", "gb": 20},
        "vol_50": {"name": "۵۰ گیگابایت", "gb": 50}
    }
}

def load_data():
    if not os.path.exists("prices.json"):
        with open("prices.json", "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=4)
        return DEFAULT_DATA
    try:
        with open("prices.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict) or "tiers" not in data:
                return DEFAULT_DATA
            return data
    except:
        return DEFAULT_DATA

def save_data(data):
    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def ensure_warehouse_files():
    data = load_data()
    for cat in data["tiers"].keys():
        fname = f"{cat}.txt"
        if not os.path.exists(fname):
            with open(fname, "w", encoding="utf-8") as f:
                f.write("")

ensure_warehouse_files()

if not os.path.exists("card.txt"):
    with open("card.txt", "w", encoding="utf-8") as f:
        f.write("هنوز شماره کارتی ثبت نشده است")

def load_user_orders():
    if not os.path.exists("user_orders.json"):
        return {}
    try:
        with open("user_orders.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_user_order(user_id, category, config):
    orders = load_user_orders()
    if str(user_id) not in orders:
        orders[str(user_id)] = []
    orders[str(user_id)].append({
        "category": category,
        "config": config,
        "purchase_date": datetime.now().isoformat()
    })
    with open("user_orders.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=4)

def format_price(amount):
    return f"{amount:,} تومان"

def get_user_account_info(user_id):
    orders = load_user_orders()
    user_configs = orders.get(str(user_id), [])
    data = load_data()
    tiers = data["tiers"]
    
    if not user_configs:
        price_per_gb = data.get("price_per_gb", 25000)
        tariffs_text = f"🔹 قیمت هر گیگابایت: **{format_price(price_per_gb)}**\n\n"
        for t_info in tiers.values():
            p_calc = t_info['gb'] * price_per_gb
            tariffs_text += f"🔹 {t_info['name']}: **{format_price(p_calc)}**\n"
            
        return (
            "👤 **اطلاعات حساب کاربری شما**\n\n"
            "شما تاکنون هیچ کانفیگی خریداری نکرده‌اید.\n\n"
            "📋 **تعرفه‌های حجمی فعال:**\n" + tariffs_text
        )
    
    text = f"👤 **اطلاعات حساب کاربری شما**\n\n📦 کل کانفیگ‌های خریداری شده: **{len(user_configs)} عدد**\n\n"
    now = datetime.now()
    
    for idx, item in enumerate(user_configs, 1):
        cat = item.get("category")
        p_name = tiers.get(cat, {}).get("name", "سرویس حجمی")
        purchase_date_str = item.get("purchase_date")
        
        try:
            p_date = datetime.fromisoformat(purchase_date_str)
            expiry_date = p_date + timedelta(days=30)
            remaining_days = (expiry_date - now).days
            
            if remaining_days < 0:
                status = "🔴 منقضی شده"
                days_text = "0 روز"
            else:
                status = "🟢 فعال"
                days_text = f"{remaining_days} روز"
        except Exception:
            status = "🟢 فعال"
            days_text = "نامشخص"
            
        text += f"🔹 **سرویس شماره {idx}:** {p_name}\n"
        text += f"   وضعیت: {status} (مانده: {days_text})\n"
        text += f"   لینک ساب: `{item.get('config')}`\n\n"
        
    return text

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
    data = load_data()
    price_per_gb = data.get("price_per_gb", 25000)
    tiers = data["tiers"]
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"💵 تنظیم قیمت هر گیگ ({format_price(price_per_gb)})", callback_data="edit_price_per_gb"))
    markup.add(InlineKeyboardButton("➖➖➖➖➖➖➖➖➖➖", callback_data="none"))
    
    for cat, info in tiers.items():
        count = get_stock_count(cat)
        calc_price = info['gb'] * price_per_gb
        stock_status = f"{count} عدد" if count > 0 else "⚠️ خالی (ثبت سفارشی)"
        markup.add(InlineKeyboardButton(f"➕ افزودن به {info['name']} ({stock_status}) — {format_price(calc_price)}", callback_data=f"add_{cat}"))
        markup.add(InlineKeyboardButton(f"✏️ تغییر نام حجم", callback_data=f"editname_{cat}"))
        markup.add(InlineKeyboardButton(f"🗑 خالی کردن انبار", callback_data=f"clear_{cat}"))
        markup.add(InlineKeyboardButton(f"❌ حذف این حجم", callback_data=f"deleteplan_{cat}"))
        markup.add(InlineKeyboardButton("➖➖➖➖➖➖➖➖➖➖", callback_data="none"))
        
    markup.add(InlineKeyboardButton("➕ ساخت حجم گیگابایتی جدید", callback_data="create_new_plan"))
    markup.add(InlineKeyboardButton("💳 تغییر شماره کارت بانکی", callback_data="edit_card"))
    markup.add(InlineKeyboardButton("❌ خروج از پنل", callback_data="exit_admin"))
    
    text_msg = (
        f"⚙️ **پنل مدیریت فروش حجمی (گیگابایتی)**\n\n"
        f"💵 قیمت پایه هر گیگ: **{format_price(price_per_gb)}**\n\n"
        f"📊 **وضعیت حجم‌ها و موجودی انبار:**\n"
    )
    for cat, info in tiers.items():
        p_calc = info['gb'] * price_per_gb
        cnt = get_stock_count(cat)
        cnt_str = f"`{cnt} عدد`" if cnt > 0 else "⚠️ `خالی`"
        text_msg += f"- {info['name']}: موجودی: {cnt_str} | قیمت: `{format_price(p_calc)}`\n"
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
        data = load_data()
        price_per_gb = data.get("price_per_gb", 25000)
        tiers = data["tiers"]
        
        markup = InlineKeyboardMarkup(row_width=1)
        for cat, info in tiers.items():
            count = get_stock_count(cat)
            p_calc = info['gb'] * price_per_gb
            stock_label = f"موجودی: {count}" if count > 0 else "⚠️ ثبت سفارشی (بدون محدودیت)"
            markup.add(InlineKeyboardButton(f"🌐 {info['name']} — {format_price(p_calc)} ({stock_label})", callback_data=f"buyplan_{cat}"))
        bot.send_message(message.chat.id, "لطفاً حجم مورد نظر خود را انتخاب کنید:", reply_markup=markup)
        
    elif text == "👤 حساب کاربری و تعرفه‌ها":
        info_text = get_user_account_info(user_id)
        bot.send_message(message.chat.id, info_text, parse_mode="Markdown")
        
    elif text == "📞 پشتیبانی HyperConn":
        bot.send_message(message.chat.id, f"برای ارتباط با پشتیبانی به ادمین پیام دهید:\n@{ADMIN_USERNAME}")
        
    elif text == "⚙️ پنل مدیریت ادمین" and is_admin(user_id):
        text_msg, markup = get_admin_panel_data()
        bot.send_message(message.chat.id, text_msg, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "none")
def handle_none_callback(call):
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "buy_menu")
def buy_menu(call):
    bot.answer_callback_query(call.id)
    user_pending_purchase.pop(call.from_user.id, None)
    data = load_data()
    price_per_gb = data.get("price_per_gb", 25000)
    tiers = data["tiers"]
    
    markup = InlineKeyboardMarkup(row_width=1)
    for cat, info in tiers.items():
        count = get_stock_count(cat)
        p_calc = info['gb'] * price_per_gb
        stock_label = f"موجودی: {count}" if count > 0 else "⚠️ ثبت سفارشی"
        markup.add(InlineKeyboardButton(f"🌐 {info['name']} — {format_price(p_calc)} ({stock_label})", callback_data=f"buyplan_{cat}"))
    try:
        bot.edit_message_text("لطفاً حجم مورد نظر خود را انتخاب کنید:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("buyplan_"))
def show_price_and_confirm(call):
    bot.answer_callback_query(call.id)
    category = call.data.replace("buyplan_", "")
    
    data = load_data()
    price_per_gb = data.get("price_per_gb", 25000)
    tiers = data["tiers"]
    p_info = tiers.get(category, {})
    p_calc = p_info.get('gb', 0) * price_per_gb
    count = get_stock_count(category)
    
    status_note = "✅ موجودی انبار آماده تحویل آنی" if count > 0 else "⚠️ انبار موقتاً خالی است (پس از واریز، ادمین دستی ارسال می‌کند)"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ تایید و دریافت شماره کارت", callback_data=f"card_{category}"))
    markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
    
    text = (
        f"📋 **اطلاعات سرویس انتخابی:**\n\n"
        f"🌐 حجم: **{p_info.get('name')}**\n"
        f"💰 مبلغ نهایی: **{format_price(p_calc)}**\n"
        f"وضعیت: {status_note}\n\n"
        f"آیا مایل به ادامه خرید و دریافت شماره کارت هستید؟"
    )
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(e)

@bot.callback_query_handler(func=lambda call: call.data.startswith("card_"))
def ask_for_receipt(call):
    bot.answer_callback_query(call.id)
    category = call.data.replace("card_", "")

    user_pending_purchase[call.from_user.id] = category
    card = get_card()
    data = load_data()
    price_per_gb = data.get("price_per_gb", 25000)
    tiers = data["tiers"]
    p_info = tiers.get(category, {})
    p_calc = p_info.get('gb', 0) * price_per_gb
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
    
    text = (
        f"💳 **شماره کارت برای واریز وجه:**\n`{card}`\n\n"
        f"🌐 حجم: **{p_info.get('name')}**\n"
        f"💰 مبلغ قابل پرداخت: **{format_price(p_calc)}**\n\n"
        f"📸 **لطفاً عکس فیش واریزی خود را همینجا ارسال کنید** تا به همراه درخواست خرید برای ادمین ارسال شود:"
    )
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(e)

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
    data = load_data()
    tiers = data["tiers"]
    p_info = tiers.get(category, {})
    p_name = p_info.get('name', 'سرویس حجمی')
    stock_cnt = get_stock_count(category)
    
    user = message.from_user
    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(InlineKeyboardButton("✅ تایید و ارسال کانفیگ", callback_data=f"approve_{user.id}_{category}"))
    admin_markup.add(InlineKeyboardButton("❌ رد درخواست", callback_data=f"reject_{user.id}"))
    
    user_info = f"@{user.username}" if user.username else "بدون یوزرنیم"
    stock_status_admin = f"موجودی انبار: {stock_cnt} عدد" if stock_cnt > 0 else "⚠️ انبار خالی است (نیاز به ارسال دستی لینک)"
    
    caption = (
        f"🚨 **درخواست خرید جدید و فیش واریزی!**\n\n"
        f"👤 کاربر: {user.first_name} ({user_info})\n"
        f"🆔 آیدی کاربر: `{user.id}`\n"
        f"🌐 حجم درخواستی: `{p_name}`\n"
        f"📊 وضعیت: {stock_status_admin}"
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
    bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        return
    
    parts = call.data.split("_")
    action = parts[0]
    target_user_id = int(parts[1])
    
    if action == "approve":
        category = "_".join(parts[2:])
        config = get_config(category)
        data = load_data()
        tiers = data["tiers"]
        p_name = tiers.get(category, {}).get("name", category)
        
        if not config:
            # انبار خالی است! از ادمین دستی لینک می‌گیریم
            admin_pending_manual_config[ADMIN_ID] = {
                "target_user_id": target_user_id,
                "category": category,
                "msg_id": call.message.message_id,
                "chat_id": call.message.chat.id
            }
            bot.answer_callback_query(call.id, "⚠️ انبار این حجم خالی است. لطفاً لینک ساب را ارسال کنید.", show_alert=True)
            msg = bot.send_message(
                call.message.chat.id,
                f"⚠️ **انبار حجم ({p_name}) خالی است!**\n\nلطفاً لینک کانفیگ یا ساب‌مکرایب اختصاصی را برای این کاربر ارسال کنید (همینجا متن یا لینک را بفرستید):",
                parse_mode="Markdown"
            )
            bot.register_next_step_handler(msg, process_manual_config_input)
            return
        
        # انبار موجودی داشت، اتوماتیک ارسال می‌شود
        save_user_order(target_user_id, category, config)
        
        try:
            bot.send_message(target_user_id, f"✅ فیش شما تایید شد! این هم کانفیگ اختصاصی شما:\n\n`{config}`", parse_mode="Markdown")
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ خطا در ارسال به کاربر: {e}", show_alert=True)
            return
        
        try:
            if call.message.photo:
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=f"✅ **تایید شد و کانفیگ خودکار ارسال گردید:**\n`{config}`", parse_mode="Markdown")
            else:
                bot.edit_message_text(f"✅ **تایید شد و کانفیگ خودکار ارسال گردید:**\n`{config}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except Exception:
            pass
        bot.answer_callback_query(call.id, "کانفیگ ارسال شد.")
        
    elif action == "reject":
        try:
            bot.send_message(target_user_id, "❌ فیش واریزی شما توسط ادمین رد شد یا نامعتبر بود. در صورت سوال به پشتیبانی پیام دهید.")
        except:
            pass
        try:
            if call.message.photo:
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption="❌ **این درخواست توسط شما رد شد.**", parse_mode="Markdown")
            else:
                bot.edit_message_text("❌ **این درخواست توسط شما رد شد.**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except Exception:
            pass
        bot.answer_callback_query(call.id, "درخواست رد شد.")

def process_manual_config_input(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    state = admin_pending_manual_config.pop(ADMIN_ID, None)
    if not state:
        return
    
    config = message.text.strip()
    target_user_id = state["target_user_id"]
    category = state["category"]
    
    save_user_order(target_user_id, category, config)
    
    try:
        bot.send_message(target_user_id, f"✅ فیش شما تایید شد! این هم کانفیگ اختصاصی شما:\n\n`{config}`", parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ لینک کانفیگ دستی با موفقیت ثبت و برای کاربر ارسال شد:\n\n`{config}`", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا در ارسال به کاربر: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("clear_"))
def handle_clear_warehouse(call):
    bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        return
    cat = call.data.replace("clear_", "")
    clear_warehouse(cat)
    bot.answer_callback_query(call.id, "✅ انبار این حجم پاک شد!", show_alert=True)
    
    text_msg, markup = get_admin_panel_data()
    try:
        bot.edit_message_text(text_msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "exit_admin")
def exit_admin(call):
    bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        return
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    bot.answer_callback_query(call.id, "از پنل مدیریت خارج شدید.")

@bot.callback_query_handler(func=lambda call: call.data == "edit_card")
def ask_for_card(call):
    bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        return
    msg = bot.send_message(call.message.chat.id, "لطفاً شماره کارت جدید را بفرستید:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_card_step)

def save_card_step(message):
    if not is_admin(message.from_user.id):
        return
    save_card(message.text)
    bot.send_message(message.chat.id, f"✅ شماره کارت ثبت شد:\n\n`{message.text}`", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "edit_price_per_gb")
def ask_for_price_per_gb(call):
    bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        return
    msg = bot.send_message(call.message.chat.id, "لطفاً **قیمت جدید هر یک گیگابایت** را به تومان وارد کنید (مثلاً `25000`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_price_per_gb_step)

def save_price_per_gb_step(message):
    if not is_admin(message.from_user.id):
        return
    try:
        clean_text = message.text.replace(",", "").replace("تومان", "").strip()
        new_price = int(clean_text)
        data = load_data()
        data["price_per_gb"] = new_price
        save_data(data)
        bot.send_message(message.chat.id, f"✅ قیمت هر گیگابایت با موفقیت به **{format_price(new_price)}** تغییر یافت!")
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً فقط یک عدد معتبر (مثلا 30000) وارد کنید.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("editname_"))
def ask_for_new_name(call):
    bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        return
    cat = call.data.replace("editname_", "")
    data = load_data()
    p_name = data["tiers"][cat]["name"]
    msg = bot.send_message(call.message.chat.id, f"لطفاً نام جدید برای **{p_name}** را وارد کنید:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_new_name_step, cat)

def save_new_name_step(message, category):
    if not is_admin(message.from_user.id):
        return
    new_name = message.text.strip()
    data = load_data()
    if category in data["tiers"]:
        data["tiers"][category]["name"] = new_name
        save_data(data)
        bot.send_message(message.chat.id, f"✅ نام حجم با موفقیت به **{new_name}** تغییر یافت!")
    else:
        bot.send_message(message.chat.id, "❌ حجم مورد نظر یافت نشد.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("deleteplan_"))
def delete_plan(call):
    bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        return
    cat = call.data.replace("deleteplan_", "")
    data = load_data()
    if len(data["tiers"]) <= 1:
        bot.answer_callback_query(call.id, "❌ حداقل یک حجم باید باقی بماند!", show_alert=True)
        return
    
    p_name = data["tiers"].get(cat, {}).get("name", cat)
    data["tiers"].pop(cat, None)
    save_data(data)
    
    try:
        if os.path.exists(f"{cat}.txt"):
            os.remove(f"{cat}.txt")
    except:
        pass
        
    bot.answer_callback_query(call.id, f"✅ حجم {p_name} به طور کامل حذف شد.", show_alert=True)
    text_msg, markup = get_admin_panel_data()
    try:
        bot.edit_message_text(text_msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "create_new_plan")
def ask_new_plan_key(call):
    bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        return
    msg = bot.send_message(call.message.chat.id, "یک شناسه انگلیسی کوتاه بفرستید (مثلاً: `vol_30` یا `special_15gb`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_new_plan_name)

def ask_new_plan_name(message):
    if not is_admin(message.from_user.id):
        return
    key = message.text.strip().lower().replace(" ", "_")
    data = load_data()
    if key in data["tiers"]:
        bot.send_message(message.chat.id, "❌ این شناسه قبلاً استفاده شده است. لطفاً شناسه دیگری وارد کنید.")
        return
    msg = bot.send_message(message.chat.id, f"حالا نام نمایشی حجم را بفرستید (مثلاً: `۳۰ گیگابایت`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_new_plan_gb, key)

def ask_new_plan_gb(message, key):
    if not is_admin(message.from_user.id):
        return
    name = message.text.strip()
    msg = bot.send_message(message.chat.id, f"حالا **تعداد گیگابایت** (فقط عدد، مثلاً `30`) را وارد کنید:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, finalize_new_plan, key, name)

def finalize_new_plan(message, key, name):
    if not is_admin(message.from_user.id):
        return
    try:
        gb_amount = int(message.text.strip().replace(",", ""))
        data = load_data()
        data["tiers"][key] = {"name": name, "gb": gb_amount}
        save_data(data)
        ensure_warehouse_files()
        
        calc_price = gb_amount * data.get("price_per_gb", 25000)
        bot.send_message(message.chat.id, f"✅ حجم جدید **{name}** با قیمت خودکار **{format_price(calc_price)}** با موفقیت ساخته شد!")
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً تعداد گیگ را به صورت عدد صحیح وارد کنید (مثلا 25).")

@bot.callback_query_handler(func=lambda data: data.data.startswith("add_"))
def ask_for_config(call):
    bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        return
    cat = call.data.replace("add_", "")
    data = load_data()
    p_name = data["tiers"].get(cat, {}).get("name", cat)
    msg = bot.send_message(call.message.chat.id, f"کانفیگ‌های مربوط به **{p_name}** را بفرستید (هر خط یک کانفیگ):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_config_step, cat)

def save_config_step(message, category):
    if not is_admin(message.from_user.id):
        return
    text = message.text.strip()
    data = load_data()
    p_name = data["tiers"].get(category, {}).get("name", category)
    count = 0
    for line in text.split("\n"):
        if line.strip():
            add_config(category, line.strip())
            count += 1
    bot.send_message(message.chat.id, f"✅ تعداد {count} کانفیگ به **{p_name}** اضافه شد!")

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    bot.infinity_polling(skip_pending=True)
