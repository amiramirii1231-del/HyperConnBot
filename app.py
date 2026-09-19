import os
import threading
import json
import time
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
user_custom_gb_state = {}
user_selected_plan_temp = {}

# تابعی برای خنثی کردن کاراکترهای حساس مارک‌داون
def clean_md(text):
    if not text:
        return ""
    return str(text).replace("_", "\\_").replace("*", "\\*").replace("`", "").replace("[", "\\[").replace("]", "\\]")

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

DEFAULT_DATA = {
    "price_per_gb": 25000,
    "price_per_extra_user": 15000,
    "fixed_plans": {
        "eco_single": {"name": "پکیج اقتصادی - ۱ کاربره", "price": "290,000 تومان"},
        "eco_double": {"name": "پکیج اقتصادی - ۲ کاربره", "price": "380,000 تومان"},
        "pro_single": {"name": "پکیج حرفه‌ای - ۱ کاربره", "price": "390,000 تومان"},
        "pro_double": {"name": "پکیج حرفه‌ای - ۲ کاربره", "price": "540,000 تومان"}
    },
    "vol_tiers": {
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
            if not isinstance(data, dict):
                return DEFAULT_DATA
            if "fixed_plans" not in data:
                data["fixed_plans"] = DEFAULT_DATA["fixed_plans"]
            if "vol_tiers" not in data:
                data["vol_tiers"] = DEFAULT_DATA["vol_tiers"]
            if "price_per_gb" not in data:
                data["price_per_gb"] = 25000
            if "price_per_extra_user" not in data:
                data["price_per_extra_user"] = 15000
            return data
    except:
        return DEFAULT_DATA

def save_data(data):
    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def ensure_warehouse_files():
    data = load_data()
    all_cats = list(data.get("fixed_plans", {}).keys()) + list(data.get("vol_tiers", {}).keys())
    for cat in all_cats:
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
    if isinstance(amount, (int, float)):
        return f"{amount:,} تومان"
    return str(amount)

def parse_price_int(price_str):
    if isinstance(price_str, (int, float)):
        return int(price_str)
    try:
        clean = str(price_str).replace(",", "").replace("تومان", "").strip()
        return int(clean)
    except:
        return 0

def get_plan_info(category):
    data = load_data()
    price_per_gb = data.get("price_per_gb", 25000)
    price_per_extra_user = data.get("price_per_extra_user", 15000)
    
    parts = category.rsplit("_u", 1)
    base_cat = parts[0]
    user_count = int(parts[1]) if len(parts) > 1 else 1
    extra_users = max(0, user_count - 1)
    extra_cost = extra_users * price_per_extra_user
    
    if base_cat.startswith("custom_"):
        try:
            gb_val = int(base_cat.replace("custom_", ""))
            base_price = gb_val * price_per_gb
            total = base_price + extra_cost
            return f"{gb_val} گیگابایت ({user_count} کاربره)", format_price(total), base_price, extra_cost, user_count
        except:
            return "حجم دلخواه", "0 تومان", 0, 0, user_count
            
    if base_cat in data.get("fixed_plans", {}):
        p = data["fixed_plans"][base_cat]
        base_p_int = parse_price_int(p["price"])
        total = base_p_int + extra_cost
        user_suffix = f" ({user_count} کاربره)" if user_count > 1 else ""
        return f"{p['name']}{user_suffix}", format_price(total), base_p_int, extra_cost, user_count
        
    elif base_cat in data.get("vol_tiers", {}):
        p = data["vol_tiers"][base_cat]
        base_price = p["gb"] * price_per_gb
        total = base_price + extra_cost
        return f"{p['name']} ({user_count} کاربره)", format_price(total), base_price, extra_cost, user_count
        
    return "سرویس", "0 تومان", 0, 0, user_count

def get_user_account_info(user_id):
    orders = load_user_orders()
    user_configs = orders.get(str(user_id), [])
    data = load_data()
    
    if not user_configs:
        price_per_gb = data.get("price_per_gb", 25000)
        price_per_extra_user = data.get("price_per_extra_user", 15000)
        
        tariffs_text = "📦 **پکیج‌های ثابت:**\n"
        for p_info in data.get("fixed_plans", {}).values():
            tariffs_text += f"🔹 {p_info['name']}: **{p_info['price']}**\n"
        
        tariffs_text += f"\n🌐 **پکیج‌های حجمی آماده (قیمت هر گیگ: {format_price(price_per_gb)}):**\n"
        for t_info in data.get("vol_tiers", {}).values():
            p_calc = t_info['gb'] * price_per_gb
            tariffs_text += f"🔹 {t_info['name']}: **{format_price(p_calc)}**\n"
            
        tariffs_text += f"\n👥 **هزینه هر کاربر اضافه همزمان:** **{format_price(price_per_extra_user)}**"
            
        return (
            "👤 **اطلاعات حساب کاربری شما**\n\n"
            "شما تاکنون هیچ کانفیگی خریداری نکرده‌اید.\n\n"
            "📋 **تعرفه‌های فعال ربات:**\n\n" + tariffs_text
        )
    
    text = f"👤 **اطلاعات حساب کاربری شما**\n\n📦 کل کانفیگ‌های خریداری شده: **{len(user_configs)} عدد**\n\n"
    now = datetime.now()
    
    for idx, item in enumerate(user_configs, 1):
        cat = item.get("category")
        p_name, _, _, _, _ = get_plan_info(cat)
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
    base_cat = category.rsplit("_u", 1)[0]
    if base_cat.startswith("custom_"):
        return None
    filename = f"{base_cat}.txt"
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
    base_cat = category.rsplit("_u", 1)[0]
    filename = f"{base_cat}.txt"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(config_text.strip() + "\n")

def get_stock_count(category):
    base_cat = category.rsplit("_u", 1)[0]
    if base_cat.startswith("custom_"):
        return 0
    filename = f"{base_cat}.txt"
    if not os.path.exists(filename):
        return 0
    with open(filename, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return len(lines)

def clear_warehouse(category):
    base_cat = category.rsplit("_u", 1)[0]
    filename = f"{base_cat}.txt"
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
    price_per_extra_user = data.get("price_per_extra_user", 15000)
    fixed_plans = data.get("fixed_plans", {})
    vol_tiers = data.get("vol_tiers", {})
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"💵 تنظیم قیمت هر گیگ ({format_price(price_per_gb)})", callback_data="edit_price_per_gb"))
    markup.add(InlineKeyboardButton(f"👥 تنظیم قیمت کاربر اضافه ({format_price(price_per_extra_user)})", callback_data="edit_price_per_user"))
    markup.add(InlineKeyboardButton("➖➖➖➖➖➖➖➖➖➖", callback_data="none"))
    
    markup.add(InlineKeyboardButton("📌 --- مدیریت پکیج‌های ثابت ---", callback_data="none"))
    for cat, info in fixed_plans.items():
        count = get_stock_count(cat)
        stock_status = f"{count} عدد" if count > 0 else "⚠️ خالی (ثبت سفارشی)"
        markup.add(InlineKeyboardButton(f"➕ افزودن به {info['name']} ({stock_status}) — {info['price']}", callback_data=f"add_{cat}"))
        markup.add(InlineKeyboardButton(f"✏️ تغییر نام", callback_data=f"editname_{cat}"), InlineKeyboardButton(f"💰 تغییر قیمت", callback_data=f"editprice_{cat}"))
        markup.add(InlineKeyboardButton(f"🗑 خالی کردن انبار", callback_data=f"clear_{cat}"), InlineKeyboardButton(f"❌ حذف پکیج", callback_data=f"deleteplan_{cat}"))
        markup.add(InlineKeyboardButton("➖➖➖➖➖➖➖➖➖➖", callback_data="none"))
        
    markup.add(InlineKeyboardButton("➕ ساخت پکیج ثابت جدید", callback_data="create_fixed_plan"))
    markup.add(InlineKeyboardButton("➖➖➖➖➖➖➖➖➖➖", callback_data="none"))
    
    markup.add(InlineKeyboardButton("📌 --- مدیریت پکیج‌های حجمی آماده ---", callback_data="none"))
    for cat, info in vol_tiers.items():
        count = get_stock_count(cat)
        calc_price = info['gb'] * price_per_gb
        stock_status = f"{count} عدد" if count > 0 else "⚠️ خالی (ثبت سفارشی)"
        markup.add(InlineKeyboardButton(f"➕ افزودن به {info['name']} ({stock_status}) — {format_price(calc_price)}", callback_data=f"add_{cat}"))
        markup.add(InlineKeyboardButton(f"✏️ تغییر نام", callback_data=f"editname_{cat}"), InlineKeyboardButton(f"🗑 خالی انبار", callback_data=f"clear_{cat}"))
        markup.add(InlineKeyboardButton(f"❌ حذف حجم", callback_data=f"deleteplan_{cat}"))
        markup.add(InlineKeyboardButton("➖➖➖➖➖➖➖➖➖➖", callback_data="none"))
        
    markup.add(InlineKeyboardButton("➕ ساخت حجم گیگابایتی جدید", callback_data="create_vol_plan"))
    markup.add(InlineKeyboardButton("💳 تغییر شماره کارت بانکی", callback_data="edit_card"))
    markup.add(InlineKeyboardButton("❌ خروج از پنل", callback_data="exit_admin"))
    
    text_msg = (
        f"⚙️ **پنل مدیریت جامع**\n\n"
        f"💵 قیمت پایه هر گیگ: **{format_price(price_per_gb)}**\n"
        f"👥 قیمت هر کاربر اضافه: **{format_price(price_per_extra_user)}**\n\n"
        f"📊 **پکیج‌های ثابت:**\n"
    )
    for cat, info in fixed_plans.items():
        cnt = get_stock_count(cat)
        cnt_str = f"`{cnt} عدد`" if cnt > 0 else "⚠️ `خالی`"
        text_msg += f"- {info['name']}: موجودی: {cnt_str} | قیمت: `{info['price']}`\n"
        
    text_msg += f"\n🌐 **پکیج‌های حجمی آماده:**\n"
    for cat, info in vol_tiers.items():
        p_calc = info['gb'] * price_per_gb
        cnt = get_stock_count(cat)
        cnt_str = f"`{cnt} عدد`" if cnt > 0 else "⚠️ `خالی`"
        text_msg += f"- {info['name']}: موجودی: {cnt_str} | قیمت پایه تک‌کاربره: `{format_price(p_calc)}`\n"
        
    text_msg += f"\n💳 **شماره کارت فعلی:**\n`{current_card}`"
    return text_msg, markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user_pending_purchase.pop(message.from_user.id, None)
        user_custom_gb_state.pop(message.from_user.id, None)
        user_selected_plan_temp.pop(message.from_user.id, None)
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
        user_custom_gb_state.pop(user_id, None)
        user_selected_plan_temp.pop(user_id, None)
        
        data = load_data()
        price_per_gb = data.get("price_per_gb", 25000)
        fixed_plans = data.get("fixed_plans", {})
        vol_tiers = data.get("vol_tiers", {})
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton(f"🌐 ➕ ساخت حجم دلخواه (هر گیگ: {format_price(price_per_gb)})", callback_data="buy_custom_gb"))
        markup.add(InlineKeyboardButton("➖➖➖➖➖➖➖➖➖➖", callback_data="none"))
        
        if fixed_plans:
            markup.add(InlineKeyboardButton("📌 --- پکیج‌های ثابت ---", callback_data="none"))
            for cat, info in fixed_plans.items():
                count = get_stock_count(cat)
                stock_label = f"موجودی: {count}" if count > 0 else "⚠️ ثبت سفارشی"
                markup.add(InlineKeyboardButton(f"📦 {info['name']} — {info['price']} ({stock_label})", callback_data=f"selplan_{cat}"))
                
        if vol_tiers:
            markup.add(InlineKeyboardButton("📌 --- پکیج‌های حجمی آماده ---", callback_data="none"))
            for cat, info in vol_tiers.items():
                count = get_stock_count(cat)
                p_calc = info['gb'] * price_per_gb
                stock_label = f"موجودی: {count}" if count > 0 else "⚠️ ثبت سفارشی"
                markup.add(InlineKeyboardButton(f"🌐 {info['name']} — {format_price(p_calc)} ({stock_label})", callback_data=f"selplan_{cat}"))
                
        bot.send_message(message.chat.id, "لطفاً پکیج یا ساخت حجم دلخواه خود را انتخاب کنید:", reply_markup=markup)
        
    elif text == "👤 حساب کاربری و تعرفه‌ها":
        info_text = get_user_account_info(user_id)
        bot.send_message(message.chat.id, info_text, parse_mode="Markdown")
        
    elif text == "📞 پشتیبانی HyperConn":
        bot.send_message(message.chat.id, f"برای ارتباط با پشتیبانی به ادمین پیام دهید:\n@{ADMIN_USERNAME}")
        
    elif text == "⚙️ پنل مدیریت ادمین" and is_admin(user_id):
        text_msg, markup = get_admin_panel_data()
        bot.send_message(message.chat.id, text_msg, parse_mode="Markdown", reply_markup=markup)

# مهم: این تابع برای جلوگیری از فریز شدن دکمه‌های "بدون اکشن" است.
@bot.callback_query_handler(func=lambda call: call.data == "none")
def handle_none_callback(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "buy_custom_gb")
def ask_custom_gb_amount(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    user_custom_gb_state[call.from_user.id] = True
    data = load_data()
    price_per_gb = data.get("price_per_gb", 25000)
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
    
    text = (
        f"🌐 **ساخت حجم دلخواه**\n\n"
        f"💵 **قیمت پایه هر یک گیگابایت:** **{format_price(price_per_gb)}**\n\n"
        f"لطفاً تعداد گیگابایت مورد نظرتان را وارد کنید (فقط عدد، مثلاً: `3` یا `10` یا `25`):"
    )
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "buy_menu")
def buy_menu(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    user_pending_purchase.pop(call.from_user.id, None)
    user_custom_gb_state.pop(call.from_user.id, None)
    user_selected_plan_temp.pop(call.from_user.id, None)
    
    data = load_data()
    price_per_gb = data.get("price_per_gb", 25000)
    fixed_plans = data.get("fixed_plans", {})
    vol_tiers = data.get("vol_tiers", {})
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(f"🌐 ➕ ساخت حجم دلخواه (هر گیگ: {format_price(price_per_gb)})", callback_data="buy_custom_gb"))
    markup.add(InlineKeyboardButton("➖➖➖➖➖➖➖➖➖➖", callback_data="none"))
    
    if fixed_plans:
        markup.add(InlineKeyboardButton("📌 --- پکیج‌های ثابت ---", callback_data="none"))
        for cat, info in fixed_plans.items():
            count = get_stock_count(cat)
            stock_label = f"موجودی: {count}" if count > 0 else "⚠️ ثبت سفارشی"
            markup.add(InlineKeyboardButton(f"📦 {info['name']} — {info['price']} ({stock_label})", callback_data=f"selplan_{cat}"))
            
    if vol_tiers:
        markup.add(InlineKeyboardButton("📌 --- پکیج‌های حجمی آماده ---", callback_data="none"))
        for cat, info in vol_tiers.items():
            count = get_stock_count(cat)
            p_calc = info['gb'] * price_per_gb
            stock_label = f"موجودی: {count}" if count > 0 else "⚠️ ثبت سفارشی"
            markup.add(InlineKeyboardButton(f"🌐 {info['name']} — {format_price(p_calc)} ({stock_label})", callback_data=f"selplan_{cat}"))
            
    try:
        bot.edit_message_text("لطفاً پکیج یا حجم مورد نظر خود را انتخاب کنید:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("selplan_"))
def handle_plan_selection(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    base_cat = call.data.replace("selplan_", "")
    data = load_data()
    
    if base_cat in data.get("fixed_plans", {}):
        p_name, total_price, base_p, extra_cost, _ = get_plan_info(base_cat)
        count = get_stock_count(base_cat)
        
        status_note = "✅ موجودی انبار آماده تحویل آنی" if count > 0 else "⚠️ ثبت سفارشی (پس از واریز، لینک توسط ادمین ارسال می‌شود)"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ تایید و دریافت شماره کارت", callback_data=f"card_{base_cat}"))
        markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
        
        text = (
            f"📋 **اطلاعات نهایی سرویس انتخابی:**\n\n"
            f"📦 پکیج: **{p_name}**\n"
            f"💰 **مبلغ کل قابل پرداخت:** **{total_price}**\n"
            f"وضعیت: {status_note}\n\n"
            f"آیا مایل به ادامه خرید و دریافت شماره کارت هستید؟"
        )
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        except Exception as e:
            print(e)
        return

    user_selected_plan_temp[call.from_user.id] = base_cat
    price_per_extra_user = data.get("price_per_extra_user", 15000)
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👤 ۱ کاربره (پایه)", callback_data=f"setusers_1"),
        InlineKeyboardButton(f"👥 ۲ کاربره (+{format_price(price_per_extra_user)})", callback_data=f"setusers_2")
    )
    markup.add(
        InlineKeyboardButton(f"👥 ۳ کاربره (+{format_price(price_per_extra_user*2)})", callback_data=f"setusers_3"),
        InlineKeyboardButton(f"👥 ۴ کاربره (+{format_price(price_per_extra_user*3)})", callback_data=f"setusers_4")
    )
    markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
    
    p_name, _, _, _, _ = get_plan_info(base_cat)
    text = (
        f"📋 **سرویس انتخابی:** **{p_name}**\n\n"
        f"👥 **تعداد کاربر همزمان:**\n"
        f"لطفاً تعداد کاربر همزمانی که برای این سرویس می‌خواهید را انتخاب کنید:"
    )
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(e)

@bot.callback_query_handler(func=lambda call: call.data.startswith("setusers_"))
def finalize_plan_selection(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    user_cnt = int(call.data.replace("setusers_", ""))
    user_id = call.from_user.id
    
    base_cat = user_selected_plan_temp.get(user_id)
    if not base_cat:
        try:
            bot.answer_callback_query(call.id, "❌ خطایی رخ داد، لطفاً دوباره تلاش کنید.", show_alert=True)
        except:
            pass
        return
        
    full_cat = f"{base_cat}_u{user_cnt}"
    p_name, total_price, base_p, extra_cost, _ = get_plan_info(full_cat)
    count = get_stock_count(base_cat)
    
    status_note = "✅ موجودی انبار آماده تحویل آنی" if count > 0 else "⚠️ ثبت سفارشی (پس از واریز، لینک توسط ادمین ارسال می‌شود)"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ تایید و دریافت شماره کارت", callback_data=f"card_{full_cat}"))
    markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
    
    breakdown = f"💵 قیمت پایه: **{format_price(base_p)}**\n"
    if extra_cost > 0:
        breakdown += f"👥 کاربر اضافه ({user_cnt-1} عدد): **+{format_price(extra_cost)}**\n"
        
    text = (
        f"📋 **اطلاعات نهایی سرویس انتخابی:**\n\n"
        f"📦 پکیج: **{p_name}**\n"
        f"{breakdown}"
        f"💰 **مبلغ کل قابل پرداخت:** **{total_price}**\n"
        f"وضعیت: {status_note}\n\n"
        f"آیا مایل به ادامه خرید و دریافت شماره کارت هستید؟"
    )
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(e)

@bot.callback_query_handler(func=lambda call: call.data.startswith("card_"))
def ask_for_receipt(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    category = call.data.replace("card_", "")

    user_pending_purchase[call.from_user.id] = category
    card = get_card()
    p_name, p_price, _, _, _ = get_plan_info(category)
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
    
    text = (
        f"💳 **شماره کارت برای واریز وجه:**\n`{card}`\n\n"
        f"📦 پکیج: **{p_name}**\n"
        f"💰 مبلغ قابل پرداخت: **{p_price}**\n\n"
        f"📸 **لطفاً عکس فیش واریزی خود را همینجا ارسال کنید** تا به همراه درخواست خرید برای ادمین ارسال شود:"
    )
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(e)

@bot.message_handler(content_types=['photo', 'text'])
def handle_user_messages(message):
    if message.from_user.id == ADMIN_ID:
        return
    
    if message.text in ["⚡ خرید کانفیگ", "👤 حساب کاربری و تعرفه‌ها", "📞 پشتیبانی HyperConn", "⚙️ پنل مدیریت ادمین"]:
        return

    user_id = message.from_user.id
    
    if user_custom_gb_state.get(user_id):
        # جلوگیری از کرش وقتی کاربر به جای عدد برای حجم، عکس می‌فرستد
        if not message.text:
            bot.send_message(message.chat.id, "❌ لطفاً فقط یک عدد معتبر برای تعداد گیگ وارد کنید (عکس مجاز نیست):")
            return
            
        text_val = message.text.strip().replace(",", "")
        try:
            gb_val = int(text_val)
            if gb_val <= 0:
                raise ValueError()
                
            user_custom_gb_state.pop(user_id, None)
            base_cat = f"custom_{gb_val}"
            user_selected_plan_temp[user_id] = base_cat
            
            data = load_data()
            price_per_extra_user = data.get("price_per_extra_user", 15000)
            
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("👤 ۱ کاربره (پایه)", callback_data=f"setusers_1"),
                InlineKeyboardButton(f"👥 ۲ کاربره (+{format_price(price_per_extra_user)})", callback_data=f"setusers_2")
            )
            markup.add(
                InlineKeyboardButton(f"👥 ۳ کاربره (+{format_price(price_per_extra_user*2)})", callback_data=f"setusers_3"),
                InlineKeyboardButton(f"👥 ۴ کاربره (+{format_price(price_per_extra_user*3)})", callback_data=f"setusers_4")
            )
            markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
            
            p_name, _, base_p, _, _ = get_plan_info(f"{base_cat}_u1")
            text = (
                f"🌐 **حجم دلخواه:** **{gb_val} گیگابایت** (قیمت پایه: {format_price(base_p)})\n\n"
                f"👥 **تعداد کاربر همزمان:**\n"
                f"لطفاً تعداد کاربر همزمان مورد نظر خود را انتخاب کنید:"
            )
            bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
            return
        except ValueError:
            bot.send_message(message.chat.id, "❌ لطفاً فقط یک عدد صحیح معتبر برای تعداد گیگ وارد کنید (مثلا 5):")
            return

    if user_id not in user_pending_purchase:
        return
    
    category = user_pending_purchase.pop(user_id)
    p_name, p_price, _, _, _ = get_plan_info(category)
    stock_cnt = get_stock_count(category)
    
    user = message.from_user
    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(InlineKeyboardButton("✅ تایید و ارسال کانفیگ", callback_data=f"approve_{user.id}_{category}"))
    admin_markup.add(InlineKeyboardButton("❌ رد درخواست", callback_data=f"reject_{user.id}"))
    
    safe_first_name = clean_md(user.first_name)
    safe_username = clean_md(user.username)
    user_info = f"@{safe_username}" if user.username else "بدون یوزرنیم"
    
    stock_status_admin = f"موجودی انبار: {stock_cnt} عدد" if stock_cnt > 0 else "⚠️ ثبت سفارشی / نیازمند ارسال دستی"
    
    caption = (
        f"🚨 **درخواست خرید جدید و فیش واریزی!**\n\n"
        f"👤 کاربر: {safe_first_name} ({user_info})\n"
        f"🆔 آیدی کاربر: `{user.id}`\n"
        f"📦 پکیج و کاربران: `{p_name}`\n"
        f"💰 مبلغ پرداختی: `{p_price}`\n"
        f"📊 وضعیت: {stock_status_admin}"
    )
    
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
            user_caption = clean_md(message.caption) if message.caption else "بدون متن"
            bot.send_photo(ADMIN_ID, file_id, caption=caption + f"\n\n💬 **متن کاربر:**\n{user_caption}", parse_mode="Markdown", reply_markup=admin_markup)
        else:
            safe_text_msg = clean_md(message.text) if message.text else "بدون متن"
            bot.send_message(ADMIN_ID, caption + f"\n\n💬 **متن کاربر:**\n{safe_text_msg}", parse_mode="Markdown", reply_markup=admin_markup)
        
        bot.send_message(message.chat.id, "✅ فیش واریزی شما با موفقیت برای ادمین ارسال شد. پس از بررسی و تایید، کانفیگ اختصاصی‌تان ارسال خواهد شد.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا در ارسال فیش: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def admin_action(call):
    if not is_admin(call.from_user.id):
        try:
            bot.answer_callback_query(call.id, "شما ادمین نیستید!", show_alert=True)
        except:
            pass
        return
    
    parts = call.data.split("_")
    action = parts[0]
    target_user_id = int(parts[1])
    
    if action == "approve":
        category = "_".join(parts[2:])
        config = get_config(category)
        p_name, _, _, _, _ = get_plan_info(category)
        
        if not config:
            try:
                bot.answer_callback_query(call.id, "⚠️ نیاز به ارسال دستی لینک ساب.", show_alert=True)
            except:
                pass
            admin_pending_manual_config[ADMIN_ID] = {
                "target_user_id": target_user_id,
                "category": category,
                "msg_id": call.message.message_id,
                "chat_id": call.message.chat.id
            }
            
            try:
                if call.message.photo:
                    bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=f"⏳ **در حال انتظار برای ارسال دستی کانفیگ...**\n\n(پکیج: {p_name})", parse_mode="Markdown")
                else:
                    bot.edit_message_text(f"⏳ **در حال انتظار برای ارسال دستی کانفیگ...**\n\n(پکیج: {p_name})", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            except:
                pass
            
            msg = bot.send_message(
                call.message.chat.id,
                f"⚠️ **سفارش برای پکیج ({p_name}) موجودی ندارد یا سفارشی است.**\n\nلطفاً لینک کانفیگ اختصاصی را برای این کاربر ارسال کنید (همینجا متن یا لینک را بفرستید):",
                parse_mode="Markdown"
            )
            bot.register_next_step_handler(msg, process_manual_config_input)
            return
        
        try:
            bot.answer_callback_query(call.id, "✅ کانفیگ با موفقیت ارسال شد.")
        except:
            pass
        save_user_order(target_user_id, category, config)
        
        try:
            bot.send_message(target_user_id, f"✅ فیش شما تایید شد! این هم کانفیگ اختصاصی شما:\n\n`{config}`", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ خطا در ارسال به کاربر.")
            return
        
        try:
            if call.message.photo:
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=f"✅ **تایید شد و کانفیگ خودکار از انبار ارسال گردید:**\n`{config}`", parse_mode="Markdown")
            else:
                bot.edit_message_text(f"✅ **تایید شد و کانفیگ خودکار از انبار ارسال گردید:**\n`{config}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except Exception:
            pass
        
    elif action == "reject":
        try:
            bot.answer_callback_query(call.id, "درخواست رد شد.")
        except:
            pass
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

def process_manual_config_input(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    # جلوگیری از کرش کردن سیستم در صورتی که ادمین به جای متن یا لینک، عکس ارسال کند
    if not message.text:
        bot.send_message(message.chat.id, "❌ لطفاً لینک یا متن کانفیگ را به صورت متنی ارسال کنید (عکس مجاز نیست).")
        bot.register_next_step_handler(message, process_manual_config_input)
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
        bot.send_message(message.chat.id, f"✅ لینک کانفیگ با موفقیت ثبت و برای کاربر ارسال شد.", parse_mode="Markdown")
        
        try:
            bot.edit_message_caption(chat_id=state["chat_id"], message_id=state["msg_id"], caption=f"✅ **تایید شد و کانفیگ دستی ارسال گردید:**\n`{config}`", parse_mode="Markdown")
        except:
            try:
                bot.edit_message_text(f"✅ **تایید شد و کانفیگ دستی ارسال گردید:**\n`{config}`", state["chat_id"], state["msg_id"], parse_mode="Markdown")
            except:
                pass

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا در ارسال به کاربر: {e}")
        # برگرداندن وضعیت به حالت قبل تا ادمین بتواند دوباره تلاش کند
        admin_pending_manual_config[ADMIN_ID] = state

@bot.callback_query_handler(func=lambda call: call.data.startswith("clear_"))
def handle_clear_warehouse(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    if not is_admin(call.from_user.id):
        return
    cat = call.data.replace("clear_", "")
    clear_warehouse(cat)
    try:
        bot.answer_callback_query(call.id, "✅ انبار این پکیج پاک شد!", show_alert=True)
    except:
        pass
    
    text_msg, markup = get_admin_panel_data()
    try:
        bot.edit_message_text(text_msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "exit_admin")
def exit_admin(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    if not is_admin(call.from_user.id):
        return
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    try:
        bot.answer_callback_query(call.id, "از پنل مدیریت خارج شدید.")
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "edit_card")
def ask_for_card(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
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
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
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
        bot.send_message(message.chat.id, "❌ لطفاً فقط یک عدد معتبر وارد کنید.")

@bot.callback_query_handler(func=lambda call: call.data == "edit_price_per_user")
def ask_for_price_per_user(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    if not is_admin(call.from_user.id):
        return
    msg = bot.send_message(call.message.chat.id, "لطفاً **قیمت اضافه شدن هر کاربر همزمان** را به تومان وارد کنید (مثلاً `15000`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_price_per_user_step)

def save_price_per_user_step(message):
    if not is_admin(message.from_user.id):
        return
    try:
        clean_text = message.text.replace(",", "").replace("تومان", "").strip()
        new_price = int(clean_text)
        data = load_data()
        data["price_per_extra_user"] = new_price
        save_data(data)
        bot.send_message(message.chat.id, f"✅ هزینه اضافه شدن هر کاربر با موفقیت به **{format_price(new_price)}** تغییر یافت!")
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً فقط یک عدد معتبر وارد کنید.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("editname_"))
def ask_for_new_name(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    if not is_admin(call.from_user.id):
        return
    cat = call.data.replace("editname_", "")
    p_name, _, _, _, _ = get_plan_info(cat)
    msg = bot.send_message(call.message.chat.id, f"لطفاً نام جدید برای **{p_name}** را وارد کنید:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_new_name_step, cat)

def save_new_name_step(message, category):
    if not is_admin(message.from_user.id):
        return
    new_name = message.text.strip()
    data = load_data()
    if category in data.get("fixed_plans", {}):
        data["fixed_plans"][category]["name"] = new_name
    elif category in data.get("vol_tiers", {}):
        data["vol_tiers"][category]["name"] = new_name
    save_data(data)
    bot.send_message(message.chat.id, f"✅ نام پکیج با موفقیت به **{new_name}** تغییر یافت!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("editprice_"))
def ask_for_new_price(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    if not is_admin(call.from_user.id):
        return
    cat = call.data.replace("editprice_", "")
    data = load_data()
    if cat in data.get("fixed_plans", {}):
        p_name = data["fixed_plans"][cat]["name"]
        msg = bot.send_message(call.message.chat.id, f"لطفاً قیمت ثابت جدید برای **{p_name}** را وارد کنید (مثلاً `320,000 تومان`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_new_price_step, cat)

def save_new_price_step(message, category):
    if not is_admin(message.from_user.id):
        return
    new_price = message.text.strip()
    data = load_data()
    if category in data.get("fixed_plans", {}):
        data["fixed_plans"][category]["price"] = new_price
        save_data(data)
        bot.send_message(message.chat.id, f"✅ قیمت ثابت پکیج با موفقیت به **{new_price}** تغییر یافت!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("deleteplan_"))
def delete_plan(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    if not is_admin(call.from_user.id):
        return
    cat = call.data.replace("deleteplan_", "")
    data = load_data()
    
    p_name, _, _, _, _ = get_plan_info(cat)
    if cat in data.get("fixed_plans", {}):
        data["fixed_plans"].pop(cat, None)
    elif cat in data.get("vol_tiers", {}):
        data["vol_tiers"].pop(cat, None)
        
    save_data(data)
    
    try:
        if os.path.exists(f"{cat}.txt"):
            os.remove(f"{cat}.txt")
    except:
        pass
        
    try:
        bot.answer_callback_query(call.id, f"✅ پکیج {p_name} حذف شد.", show_alert=True)
    except:
        pass
    text_msg, markup = get_admin_panel_data()
    try:
        bot.edit_message_text(text_msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "create_fixed_plan")
def ask_fixed_plan_key(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    if not is_admin(call.from_user.id):
        return
    msg = bot.send_message(call.message.chat.id, "یک شناسه انگلیسی کوتاه برای پکیج ثابت بفرستید (مثلاً: `vip_single`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_fixed_plan_name)

def ask_fixed_plan_name(message):
    if not is_admin(message.from_user.id):
        return
    key = message.text.strip().lower().replace(" ", "_")
    data = load_data()
    if key in data.get("fixed_plans", {}) or key in data.get("vol_tiers", {}):
        bot.send_message(message.chat.id, "❌ این شناسه قبلاً استفاده شده است.")
        return
    msg = bot.send_message(message.chat.id, "نام نمایشی پکیج را بفرستید (مثلاً: `پکیج ویژه - ۱ کاربره`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_fixed_plan_price, key)

def ask_fixed_plan_price(message, key):
    if not is_admin(message.from_user.id):
        return
    name = message.text.strip()
    msg = bot.send_message(message.chat.id, "قیمت ثابت پکیج را بفرستید (مثلاً `450,000 تومان`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, finalize_fixed_plan, key, name)

def finalize_fixed_plan(message, key, name):
    if not is_admin(message.from_user.id):
        return
    price = message.text.strip()
    data = load_data()
    data["fixed_plans"][key] = {"name": name, "price": price}
    save_data(data)
    ensure_warehouse_files()
    bot.send_message(message.chat.id, f"✅ پکیج ثابت **{name}** با قیمت **{price}** ساخته شد!")

@bot.callback_query_handler(func=lambda call: call.data == "create_vol_plan")
def ask_vol_plan_key(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    if not is_admin(call.from_user.id):
        return
    msg = bot.send_message(call.message.chat.id, "یک شناسه انگلیسی کوتاه برای پکیج حجمی آماده بفرستید (مثلاً: `vol_30`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_vol_plan_name)

def ask_vol_plan_name(message):
    if not is_admin(message.from_user.id):
        return
    key = message.text.strip().lower().replace(" ", "_")
    data = load_data()
    if key in data.get("fixed_plans", {}) or key in data.get("vol_tiers", {}):
        bot.send_message(message.chat.id, "❌ این شناسه قبلاً استفاده شده است.")
        return
    msg = bot.send_message(message.chat.id, "نام نمایشی حجم را بفرستید (مثلاً: `۳۰ گیگابایت`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_vol_plan_gb, key)

def ask_vol_plan_gb(message, key):
    if not is_admin(message.from_user.id):
        return
    name = message.text.strip()
    msg = bot.send_message(message.chat.id, "تعداد گیگابایت (فقط عدد، مثلاً `30`) را وارد کنید تا قیمت اتوماتیک محاسبه شود:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, finalize_vol_plan, key, name)

def finalize_vol_plan(message, key, name):
    if not is_admin(message.from_user.id):
        return
    try:
        gb_amount = int(message.text.strip().replace(",", ""))
        data = load_data()
        data["vol_tiers"][key] = {"name": name, "gb": gb_amount}
        save_data(data)
        ensure_warehouse_files()
        calc_price = gb_amount * data.get("price_per_gb", 25000)
        bot.send_message(message.chat.id, f"✅ پکیج حجمی آماده **{name}** با قیمت خودکار **{format_price(calc_price)}** ساخته شد!")
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً تعداد گیگ را به صورت عدد صحیح وارد کنید.")

@bot.callback_query_handler(func=lambda data: data.data.startswith("add_"))
def ask_for_config(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    if not is_admin(call.from_user.id):
        return
    cat = call.data.replace("add_", "")
    p_name, _, _, _, _ = get_plan_info(cat)
    msg = bot.send_message(call.message.chat.id, f"کانفیگ‌های مربوط به **{p_name}** را بفرستید (هر خط یک کانفیگ):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_config_step, cat)

def save_config_step(message, category):
    if not is_admin(message.from_user.id):
        return
    text = message.text.strip()
    p_name, _, _, _, _ = get_plan_info(category)
    count = 0
    for line in text.split("\n"):
        if line.strip():
            add_config(category, line.strip())
            count += 1
    bot.send_message(message.chat.id, f"✅ تعداد {count} کانفیگ به **{p_name}** اضافه شد!")

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    # اطمینان از پاک شدن وب‌هوک و فرصت دادن به تلگرام
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception as e:
        print(f"Error removing webhook: {e}")
    
    # اجرای پولینگ بی‌نهایت با تایم‌اوت مشخص برای جلوگیری از قطع شدن
    bot.infinity_polling(timeout=10, long_polling_timeout=5, skip_pending=True)
