import os
import json
import time
import threading
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8226487699:AAGQdfgbudiw3FWIJsidwfvmJ5AhxaHvNLk"
ADMIN_ID = 666875325
ADMIN_USERNAME = "HyperConn"

bot = telebot.TeleBot(TOKEN)

# ==========================================
# وب سرور فوق سبک برای دور زدن گیرهای Render
# ==========================================
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running powerfully without Flask conflicts!")
    def log_message(self, format, *args):
        pass # جلوگیری از اسپم شدن لاگ‌ها

def run_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

# ==========================================
# توابع دیتابیس و فایل‌ها (بدون تغییرات ریسکی)
# ==========================================
def clean_md(text):
    if not text: return ""
    return str(text).replace("_", "\\_").replace("*", "\\*").replace("`", "").replace("[", "\\[").replace("]", "\\]")

DEFAULT_DATA = {
    "price_per_gb": 25000,
    "price_per_extra_user": 15000,
    "fixed_plans": {
        "eco_single": {"name": "پکیج اقتصادی - ۱ کاربره", "price": "290,000"},
        "eco_double": {"name": "پکیج اقتصادی - ۲ کاربره", "price": "380,000"},
        "pro_single": {"name": "پکیج حرفه‌ای - ۱ کاربره", "price": "390,000"},
        "pro_double": {"name": "پکیج حرفه‌ای - ۲ کاربره", "price": "540,000"}
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
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    try:
        with open("prices.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if "fixed_plans" not in data: data["fixed_plans"] = DEFAULT_DATA["fixed_plans"]
            if "vol_tiers" not in data: data["vol_tiers"] = DEFAULT_DATA["vol_tiers"]
            if "price_per_gb" not in data: data["price_per_gb"] = 25000
            if "price_per_extra_user" not in data: data["price_per_extra_user"] = 15000
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
            open(fname, "w", encoding="utf-8").close()

ensure_warehouse_files()

if not os.path.exists("card.txt"):
    open("card.txt", "w", encoding="utf-8").write("هنوز شماره کارتی ثبت نشده است")

def load_user_orders():
    if not os.path.exists("user_orders.json"): return {}
    try:
        with open("user_orders.json", "r", encoding="utf-8") as f: return json.load(f)
    except:
        return {}

def save_user_order(user_id, category, config):
    orders = load_user_orders()
    if str(user_id) not in orders: orders[str(user_id)] = []
    orders[str(user_id)].append({
        "category": category,
        "config": config,
        "purchase_date": datetime.now().isoformat()
    })
    with open("user_orders.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=4)

def format_price(amount):
    return f"{amount:,} تومان" if isinstance(amount, (int, float)) else str(amount)

def parse_price_int(price_str):
    try: return int(str(price_str).replace(",", "").replace("تومان", "").strip())
    except: return 0

def get_plan_info(full_cat):
    data = load_data()
    price_gb = data.get("price_per_gb", 25000)
    price_usr = data.get("price_per_extra_user", 15000)
    
    parts = full_cat.rsplit("_u", 1)
    base_cat = parts[0]
    users = int(parts[1]) if len(parts) > 1 else 1
    extra_cost = max(0, users - 1) * price_usr
    
    if base_cat.startswith("custom_"):
        try:
            gb = int(base_cat.replace("custom_", ""))
            base_p = gb * price_gb
            total = base_p + extra_cost
            return f"{gb} گیگابایت ({users} کاربره)", format_price(total), format_price(base_p), format_price(extra_cost), users
        except:
            return "نامشخص", "0 تومان", "0 تومان", "0 تومان", users
            
    elif base_cat in data.get("fixed_plans", {}):
        p = data["fixed_plans"][base_cat]
        base_p = parse_price_int(p["price"])
        total = base_p + extra_cost
        u_suffix = f" ({users} کاربره)" if users > 1 else ""
        return f"{p['name']}{u_suffix}", format_price(total), format_price(base_p), format_price(extra_cost), users
        
    elif base_cat in data.get("vol_tiers", {}):
        p = data["vol_tiers"][base_cat]
        base_p = p["gb"] * price_gb
        total = base_p + extra_cost
        return f"{p['name']} ({users} کاربره)", format_price(total), format_price(base_p), format_price(extra_cost), users
        
    return "سرویس", "0 تومان", "0 تومان", "0 تومان", users

def get_stock_count(category):
    base_cat = category.rsplit("_u", 1)[0]
    if base_cat.startswith("custom_"): return 0
    fname = f"{base_cat}.txt"
    if not os.path.exists(fname): return 0
    with open(fname, "r", encoding="utf-8") as f:
        return len([line for line in f.readlines() if line.strip()])

def get_config(category):
    base_cat = category.rsplit("_u", 1)[0]
    if base_cat.startswith("custom_"): return None
    fname = f"{base_cat}.txt"
    if not os.path.exists(fname): return None
    with open(fname, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    if not lines: return None
    config = lines[0]
    with open(fname, "w", encoding="utf-8") as f:
        f.write("\n".join(lines[1:]) + ("\n" if lines[1:] else ""))
    return config

def get_card():
    try: return open("card.txt", "r", encoding="utf-8").read().strip()
    except: return "ثبت نشده"

# ==========================================
# کیبوردها و پیام‌های اصلی
# ==========================================
def get_main_markup(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("⚡ خرید کانفیگ"), KeyboardButton("👤 حساب کاربری و تعرفه‌ها"))
    markup.add(KeyboardButton("📞 پشتیبانی HyperConn"))
    if user_id == ADMIN_ID: markup.add(KeyboardButton("⚙️ پنل مدیریت ادمین"))
    return markup

@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.clear_step_handler_by_chat_id(message.chat.id)
    bot.send_message(message.chat.id, "به ربات **HyperConn** خوش آمدید. از منوی زیر انتخاب کنید:", parse_mode="Markdown", reply_markup=get_main_markup(message.from_user.id))

# این هندلر حیاتی است: اگر کاربر وسط یه کاری بود و دکمه‌های اصلی رو زد، گیر نمیکنه
@bot.message_handler(func=lambda msg: msg.text in ["⚡ خرید کانفیگ", "👤 حساب کاربری و تعرفه‌ها", "📞 پشتیبانی HyperConn", "⚙️ پنل مدیریت ادمین"])
def main_menu_handler(message):
    bot.clear_step_handler_by_chat_id(message.chat.id) # خروج از هرگونه بن‌بست
    text = message.text
    user_id = message.from_user.id
    
    if text == "⚡ خرید کانفیگ":
        data = load_data()
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton(f"🌐 ➕ ساخت حجم دلخواه (گیگی {format_price(data.get('price_per_gb', 25000))})", callback_data="buy_custom"))
        markup.add(InlineKeyboardButton("➖➖➖➖➖➖➖➖➖➖", callback_data="none"))
        
        for cat, info in data.get("fixed_plans", {}).items():
            cnt = get_stock_count(cat)
            st = f"موجودی: {cnt}" if cnt > 0 else "ثبت سفارشی"
            markup.add(InlineKeyboardButton(f"📦 {info['name']} — {info['price']} ({st})", callback_data=f"plan_{cat}"))
            
        for cat, info in data.get("vol_tiers", {}).items():
            cnt = get_stock_count(cat)
            p_calc = format_price(info['gb'] * data.get('price_per_gb', 25000))
            st = f"موجودی: {cnt}" if cnt > 0 else "ثبت سفارشی"
            markup.add(InlineKeyboardButton(f"🌐 {info['name']} — {p_calc} ({st})", callback_data=f"plan_{cat}"))
            
        bot.send_message(message.chat.id, "لطفاً سرویس مورد نظر را انتخاب کنید:", reply_markup=markup)
        
    elif text == "👤 حساب کاربری و تعرفه‌ها":
        orders = load_user_orders().get(str(user_id), [])
        if not orders:
            bot.send_message(message.chat.id, "شما هنوز خریدی نداشته‌اید.", parse_mode="Markdown")
        else:
            txt = f"👤 **خرید‌های شما ({len(orders)} عدد):**\n\n"
            for i, ord in enumerate(orders, 1):
                p_name = get_plan_info(ord['category'])[0]
                txt += f"🔹 **سرویس {i}:** {p_name}\nلینک: `{ord['config']}`\n\n"
            bot.send_message(message.chat.id, txt, parse_mode="Markdown")
            
    elif text == "📞 پشتیبانی HyperConn":
        bot.send_message(message.chat.id, f"برای ارتباط با پشتیبانی به ادمین پیام دهید:\n@{ADMIN_USERNAME}")

# ==========================================
# مدیریت دکمه‌های شیشه‌ای (Callbacks) کاملا بدون متغیرهای سراسری
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if data == "none": return
    
    if data == "buy_menu":
        bot.delete_message(chat_id, msg_id)
        main_menu_handler(call.message) # شبیه سازی کلیک روی دکمه اصلی
        return

    # --- 1. انتخاب ساخت حجم دلخواه ---
    if data == "buy_custom":
        msg = bot.edit_message_text("تعداد گیگابایت مورد نظرتان را وارد کنید (فقط عدد، مثلا 30):", chat_id, msg_id)
        bot.register_next_step_handler(msg, process_custom_gb)
        
    # --- 2. انتخاب یکی از پلن‌های ثابت یا حجمی ---
    elif data.startswith("plan_"):
        base_cat = data.split("plan_", 1)[1]
        
        # اگر پلن از پیش تعیین شده است، یه راست میایم تعداد کاربر رو بپرسیم
        markup = InlineKeyboardMarkup(row_width=2)
        p_usr = load_data().get("price_per_extra_user", 15000)
        markup.add(
            InlineKeyboardButton("👤 ۱ کاربره", callback_data=f"usr_1_{base_cat}"),
            InlineKeyboardButton(f"👥 ۲ کاربره (+{format_price(p_usr)})", callback_data=f"usr_2_{base_cat}")
        )
        markup.add(
            InlineKeyboardButton(f"👥 ۳ کاربره (+{format_price(p_usr*2)})", callback_data=f"usr_3_{base_cat}"),
            InlineKeyboardButton(f"👥 ۴ کاربره (+{format_price(p_usr*3)})", callback_data=f"usr_4_{base_cat}")
        )
        markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
        bot.edit_message_text(f"سرویس انتخاب شد.\nحالا لطفاً تعداد کاربر همزمان را انتخاب کنید:", chat_id, msg_id, reply_markup=markup)

    # --- 3. انتخاب تعداد کاربر (محاسبه نهایی) ---
    elif data.startswith("usr_"):
        # فرمت: usr_2_eco_single یا usr_3_custom_15
        parts = data.split("_", 2)
        users_count = parts[1]
        base_cat = parts[2]
        full_cat = f"{base_cat}_u{users_count}"
        
        p_name, t_price, b_price, e_price, _ = get_plan_info(full_cat)
        cnt = get_stock_count(full_cat)
        st = "✅ آماده تحویل" if cnt > 0 else "⚠️ نیازمند ثبت سفارشی"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ تایید و دریافت شماره کارت", callback_data=f"crd_{full_cat}"))
        markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
        
        text = f"📋 **فاکتور نهایی:**\n\n📦 سرویس: {p_name}\n💵 قیمت پایه: {b_price}\n👥 هزینه کاربر اضافه: {e_price}\n💰 **مبلغ کل پرداخت: {t_price}**\nوضعیت: {st}"
        bot.edit_message_text(text, chat_id, msg_id, parse_mode="Markdown", reply_markup=markup)

    # --- 4. نمایش شماره کارت و دریافت فیش ---
    elif data.startswith("crd_"):
        full_cat = data.split("crd_", 1)[1]
        p_name, t_price, _, _, _ = get_plan_info(full_cat)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
        
        text = f"💳 **شماره کارت:**\n`{get_card()}`\n\n💰 مبلغ: **{t_price}**\n📦 سرویس: {p_name}\n\n📸 **همین الان عکس فیش واریزی خود را در چت ارسال کنید.**"
        msg = bot.edit_message_text(text, chat_id, msg_id, parse_mode="Markdown", reply_markup=markup)
        
        # تنها جایی که منتظر میمونیم مشتری عکس بده. متغیر full_cat تو خود تابع پاس داده میشه
        bot.register_next_step_handler(msg, process_receipt, full_cat)
        
    # --- 5. ادمین تایید/رد فیش ---
    elif data.startswith("app_") or data.startswith("rej_"):
        if call.from_user.id != ADMIN_ID: return
        
        action = data[:3]
        parts = data[4:].split("_", 1)
        target_uid = int(parts[0])
        full_cat = parts[1] if len(parts) > 1 else ""
        
        if action == "rej":
            bot.send_message(target_uid, "❌ فیش شما توسط ادمین رد شد.")
            try: bot.edit_message_caption("❌ رد شد.", chat_id, msg_id)
            except: bot.edit_message_text("❌ رد شد.", chat_id, msg_id)
            
        elif action == "app":
            config = get_config(full_cat)
            if config:
                save_user_order(target_uid, full_cat, config)
                bot.send_message(target_uid, f"✅ فیش تایید شد! کانفیگ شما:\n`{config}`", parse_mode="Markdown")
                try: bot.edit_message_caption("✅ تایید شد (تحویل خودکار از انبار).", chat_id, msg_id)
                except: bot.edit_message_text("✅ تایید شد (تحویل خودکار از انبار).", chat_id, msg_id)
            else:
                # انبار خالیه، از ادمین دستی میگیریم
                try: bot.edit_message_caption("⏳ منتظر ارسال دستی کانفیگ...", chat_id, msg_id)
                except: bot.edit_message_text("⏳ منتظر ارسال دستی کانفیگ...", chat_id, msg_id)
                msg = bot.send_message(chat_id, "موجودی انبار خالی بود! لطفا کانفیگ رو متنی همینجا بفرست تا تحویل مشتری بدم:")
                bot.register_next_step_handler(msg, admin_manual_config, target_uid, full_cat, msg_id)

# توابع کمکی برای Step Handler ها
def process_custom_gb(message):
    if message.text in ["⚡ خرید کانفیگ", "👤 حساب کاربری و تعرفه‌ها", "📞 پشتیبانی HyperConn", "⚙️ پنل مدیریت ادمین"]:
        return main_menu_handler(message) # جلوگیری از گیر کردن کاربر
        
    try:
        gb = int(message.text.strip())
        base_cat = f"custom_{gb}"
        
        markup = InlineKeyboardMarkup(row_width=2)
        p_usr = load_data().get("price_per_extra_user", 15000)
        markup.add(
            InlineKeyboardButton("👤 ۱ کاربره", callback_data=f"usr_1_{base_cat}"),
            InlineKeyboardButton(f"👥 ۲ کاربره (+{format_price(p_usr)})", callback_data=f"usr_2_{base_cat}")
        )
        markup.add(
            InlineKeyboardButton(f"👥 ۳ کاربره (+{format_price(p_usr*2)})", callback_data=f"usr_3_{base_cat}"),
            InlineKeyboardButton(f"👥 ۴ کاربره (+{format_price(p_usr*3)})", callback_data=f"usr_4_{base_cat}")
        )
        markup.add(InlineKeyboardButton("❌ انصراف", callback_data="buy_menu"))
        
        bot.send_message(message.chat.id, f"سرویس {gb} گیگ انتخاب شد. لطفاً تعداد کاربر را انتخاب کنید:", reply_markup=markup)
    except:
        msg = bot.send_message(message.chat.id, "❌ لطفاً فقط عدد انگلیسی وارد کنید (مثلا 20):")
        bot.register_next_step_handler(msg, process_custom_gb)

def process_receipt(message, full_cat):
    if message.text in ["⚡ خرید کانفیگ", "👤 حساب کاربری و تعرفه‌ها", "📞 پشتیبانی HyperConn", "⚙️ پنل مدیریت ادمین"]:
        return main_menu_handler(message)

    p_name, t_price, _, _, _ = get_plan_info(full_cat)
    user = message.from_user
    
    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(InlineKeyboardButton("✅ تایید", callback_data=f"app_{user.id}_{full_cat}"))
    admin_markup.add(InlineKeyboardButton("❌ رد", callback_data=f"rej_{user.id}"))
    
    caption = f"🚨 **درخواست خرید جدید**\n👤 {user.first_name} | `{user.id}`\n📦 سرویس: {p_name}\n💰 مبلغ: {t_price}"
    
    try:
        if message.photo:
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, parse_mode="Markdown", reply_markup=admin_markup)
        else:
            bot.send_message(ADMIN_ID, caption + f"\n\n💬 متن ارسالی:\n{message.text}", parse_mode="Markdown", reply_markup=admin_markup)
            
        bot.send_message(message.chat.id, "✅ فیش شما برای پشتیبانی ارسال شد. منتظر تایید باشید.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ خطا در ارسال فیش. لطفا دوباره تلاش کنید.")

def admin_manual_config(message, target_uid, full_cat, original_msg_id):
    if message.text in ["⚡ خرید کانفیگ", "👤 حساب کاربری و تعرفه‌ها", "📞 پشتیبانی HyperConn", "⚙️ پنل مدیریت ادمین"]:
        return main_menu_handler(message)
        
    if not message.text:
        msg = bot.send_message(ADMIN_ID, "❌ لطفاً کانفیگ رو به صورت متن بفرستید:")
        return bot.register_next_step_handler(msg, admin_manual_config, target_uid, full_cat, original_msg_id)
        
    config = message.text.strip()
    save_user_order(target_uid, full_cat, config)
    
    bot.send_message(target_uid, f"✅ فیش تایید شد! کانفیگ اختصاصی شما:\n`{config}`", parse_mode="Markdown")
    bot.send_message(ADMIN_ID, "✅ کانفیگ دستی به کاربر تحویل داده شد.")
    try: bot.edit_message_caption(f"✅ ارسال دستی انجام شد.\n{config}", ADMIN_ID, original_msg_id)
    except: pass

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    
    try:
        bot.remove_webhook()
        time.sleep(1)
    except: pass
    
    print("Bot is polling...")
    # تایم‌اوت‌های استاندارد تا اگر تلگرام قطع شد، پایتون کرش نکنه و دوباره تلاش کنه
    bot.infinity_polling(timeout=20, long_polling_timeout=15)
