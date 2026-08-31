import json
import os
from threading import Thread
import telebot
from flask import Flask

TOKEN = "8689876289:AAFtWxe-M3JkgHW1x3A5LYXfzQ_q7uI4Az4"
ADMIN_ID = 666875325

bot = telebot.TeleBot(TOKEN)
user_state = {}
DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "card_number": "6037-9971-xxxx-xxxx",
        "card_holder": "نام صاحب حساب",
        "configs": {
            "VIP - تک‌کاربره": [],
            "VIP - دوکاربره": [],
            "CIP - تک‌کاربره": [],
            "CIP - دوکاربره": []
        }
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

app = Flask(__name__)

@app.route("/")
def home():
    return "HyperConn Bot is running 24/7!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🚀 خرید کانفیگ (CIP / VIP)", callback_data="buy_plans"),
        telebot.types.InlineKeyboardButton("👤 حساب کاربری و تعرفه‌ها", callback_data="account")
    )
    markup.add(telebot.types.InlineKeyboardButton("📞 پشتیبانی HyperConn", callback_data="support"))
    
    text = (
        "به ربات رسمی **HyperConn** خوش آمدید.\n\n"
        "برای تجربه اتصال پرسرعت، امن و پایدار، یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    data = load_data()
    total_configs = sum(len(lst) for lst in data["configs"].values())
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("📊 موجودی انبار کانفیگ‌ها", callback_data="admin_inventory"),
        telebot.types.InlineKeyboardButton("💳 تغییر شماره کارت و صاحب حساب", callback_data="admin_set_card"),
        telebot.types.InlineKeyboardButton("➕ افزودن کانفیگ جدید به انبار", callback_data="admin_add_config")
    )
    
    text = (
        "⚙️ **پنل مدیریت اختصاصی HyperConn**\n\n"
        f"💳 شماره کارت فعلی: `{data['card_number']}`\n"
        f"👤 صاحب حساب: {data['card_holder']}\n"
        f"📦 مجموع کانفیگ‌های آماده در انبار: {total_configs} عدد"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = load_data()
    
    if call.data == "buy_plans":
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("🌟 پلن VIP (مخصوص گیم و ترید)", callback_data="select_vip"),
            telebot.types.InlineKeyboardButton("⚡ پلن CIP (سرعت و ترافیک نامحدود)", callback_data="select_cip"),
            telebot.types.InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_home")
        )
        bot.edit_message_text("لطفاً نوع پلن مورد نظر خود را انتخاب کنید:", chat_id, message_id, reply_markup=markup)
        
    elif call.data == "select_vip":
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("👤 VIP تک‌کاربره", callback_data="order_VIP - تک‌کاربره"),
            telebot.types.InlineKeyboardButton("👥 VIP دوکاربره", callback_data="order_VIP - دوکاربره"),
            telebot.types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_plans")
        )
        bot.edit_message_text("🌟 **پلن VIP**\nلطفاً تعداد کاربر (دستگاه‌های متصل) را انتخاب کنید:", chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
        
    elif call.data == "select_cip":
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("👤 CIP تک‌کاربره", callback_data="order_CIP - تک‌کاربره"),
            telebot.types.InlineKeyboardButton("👥 CIP دوکاربره", callback_data="order_CIP - دوکاربره"),
            telebot.types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_plans")
        )
        bot.edit_message_text("⚡ **پلن CIP**\nلطفاً تعداد کاربر (دستگاه‌های متصل) را انتخاب کنید:", chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
        
    elif call.data.startswith("order_"):
        full_plan_name = call.data.replace("order_", "")
        user_state[chat_id] = {"selected_plan": full_plan_name}
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔙 بازگشت به انتخاب پلن", callback_data="buy_plans"))
        
        text = (
            f"شما **پلن {full_plan_name}** را انتخاب کردید.\n\n"
            "💳 **مبلغ را به شماره کارت زیر واریز کنید:**\n"
            f"`{data['card_number']}`\n"
            f"به نام: {data['card_holder']}\n\n"
            "📸 پس از پرداخت، **تصویر فیش واریزی** را همینجا ارسال کنید تا سفارش شما بررسی و کانفیگ ارسال شود.\n\n"
            "⚡ Brand: **HyperConn**"
        )
        bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "account":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_home"))
        bot.edit_message_text("👤 اطلاعات حساب کاربری شما در **HyperConn**:\n\nوضعیت اشتراک: آزاد\nحجم مصرفی: نامحدود", chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "support":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_home"))
        bot.edit_message_text("📞 برای ارتباط با پشتیبانی:\nمستقیماً به ادمین پیام دهید.\n\n⚡ **HyperConn**", chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "back_home":
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("🚀 خرید کانفیگ (CIP / VIP)", callback_data="buy_plans"),
            telebot.types.InlineKeyboardButton("👤 حساب کاربری و تعرفه‌ها", callback_data="account")
        )
        markup.add(telebot.types.InlineKeyboardButton("📞 پشتیبانی HyperConn", callback_data="support"))
        bot.edit_message_text("به منوی اصلی **HyperConn** برگشتید:", chat_id, message_id, reply_markup=markup)

    elif call.data == "admin_inventory":
        inv_text = "📊 **موجودی انبار کانفیگ‌ها:**\n\n"
        for plan, lst in data["configs"].items():
            inv_text += f"• **{plan}**: {len(lst)} عدد آماده\n"
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="back_admin"))
        bot.edit_message_text(inv_text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "admin_set_card":
        user_state[chat_id] = {"action": "waiting_card_info"}
        bot.edit_message_text("💳 لطفاً شماره کارت جدید و نام صاحب حساب را به این صورت ارسال کنید:\n\n`6037xxxxxxxxxxxx*نام صاحب حساب`", chat_id, message_id, parse_mode="Markdown")

    elif call.data == "admin_add_config":
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for plan in data["configs"].keys():
            markup.add(telebot.types.InlineKeyboardButton(f"افزودن به {plan}", callback_data=f"addto_{plan}"))
        markup.add(telebot.types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_admin"))
        bot.edit_message_text("لطفاً پلنی که می‌خواهید کانفیگ جدید به آن اضافه شود را انتخاب کنید:", chat_id, message_id, reply_markup=markup)

    elif call.data.startswith("addto_"):
        selected_plan = call.data.replace("addto_", "")
        user_state[chat_id] = {"action": "waiting_config_link", "plan": selected_plan}
        bot.edit_message_text(f"➕ لینک کانفیگ VLESS را برای پلن **{selected_plan}** بفرستید:", chat_id, message_id, parse_mode="Markdown")

    elif call.data == "back_admin":
        total_configs = sum(len(lst) for lst in data["configs"].values())
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("📊 موجودی انبار کانفیگ‌ها", callback_data="admin_inventory"),
            telebot.types.InlineKeyboardButton("💳 تغییر شماره کارت و صاحب حساب", callback_data="admin_set_card"),
            telebot.types.InlineKeyboardButton("➕ افزودن کانفیگ جدید به انبار", callback_data="admin_add_config")
        )
        text = (
            "⚙️ **پنل مدیریت اختصاصی HyperConn**\n\n"
            f"💳 شماره کارت فعلی: `{data['card_number']}`\n"
            f"👤 صاحب حساب: {data['card_holder']}\n"
            f"📦 مجموع کانفیگ‌های آماده در انبار: {total_configs} عدد"
        )
        bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data.startswith("approve_"):
        parts = call.data.split("_")
        target_user_id = int(parts[1])
        plan_name = parts[2]
        
        if data["configs"].get(plan_name) and len(data["configs"][plan_name]) > 0:
            assigned_config = data["configs"][plan_name].pop(0)
            save_data(data)
            
            bot.send_message(target_user_id, f"✅ فیش واریزی شما تایید شد!\n\nکانفیگ اختصاصی شما:\n`{assigned_config}`\n\nبا تشکر از انتخاب **HyperConn**", parse_mode="Markdown")
            bot.edit_message_caption(f"✅ این فیش تایید شد و کانفیگ زیر با موفقیت به کاربر ارسال گردید:\n`{assigned_config}`", chat_id, message_id, parse_mode="Markdown")
            bot.answer_callback_query(call.id, "کانفیگ با موفقیت از انبار کسر و ارسال شد.")
        else:
            bot.answer_callback_query(call.id, "❌ خطا: موجودی کانفیگ برای این پلن در انبار تمام شده است!", show_alert=True)

    elif call.data.startswith("reject_"):
        target_user_id = int(call.data.split("_")[1])
        bot.send_message(target_user_id, "❌ متأسفانه فیش واریزی شما رد شد. لطفاً جهت پیگیری با پشتیبانی ارتباط بگیرید.")
        bot.edit_message_caption("❌ این فیش توسط شما رد شد.", chat_id, message_id)
        bot.answer_callback_query(call.id, "فیش رد شد.")

@bot.message_handler(content_types=['text', 'photo'])
def handle_admin_inputs_and_receipts(message):
    chat_id = message.chat.id
    data = load_data()
    
    if chat_id == ADMIN_ID and chat_id in user_state:
        state = user_state[chat_id]
        
        if state.get("action") == "waiting_card_info":
            try:
                parts = message.text.split("*")
                new_card = parts[0].strip()
                new_holder = parts[1].strip()
                data["card_number"] = new_card
                data["card_holder"] = new_holder
                save_data(data)
                del user_state[chat_id]
                bot.reply_to(message, "✅ شماره کارت و نام صاحب حساب با موفقیت بروزرسانی شد!")
                return
            except:
                bot.reply_to(message, "❌ فرمت اشتباه است. لطفاً به صورت `شماره‌کارت*نام صاحب حساب` ارسال کنید.")
                return
                
        elif state.get("action") == "waiting_config_link":
            plan = state.get("plan")
            config_link = message.text.strip()
            data["configs"][plan].append(config_link)
            save_data(data)
            del user_state[chat_id]
            bot.reply_to(message, f"✅ کانفیگ جدید با موفقیت به انبار **{plan}** اضافه شد.\nموجودی فعلی این پلن: {len(data['configs'][plan])} عدد", parse_mode="Markdown")
            return

    if message.content_type == 'photo':
        username = message.from_user.username or "ندارد"
        file_id = message.photo[-1].file_id
        plan_info = user_state.get(chat_id, {}).get("selected_plan", "VIP - تک‌کاربره")
        
        admin_markup = telebot.types.InlineKeyboardMarkup()
        admin_markup.add(
            telebot.types.InlineKeyboardButton("✅ تایید و ارسال کانفیگ", callback_data=f"approve_{chat_id}_{plan_info}"),
            telebot.types.InlineKeyboardButton("❌ رد فیش", callback_data=f"reject_{chat_id}")
        )
        
        bot.send_photo(
            ADMIN_ID,
            file_id,
            caption=(
                f"🔔 **فیش جدید برای HyperConn**\n\n"
                f"کاربر: @{username}\n"
                f"آیدی: `{chat_id}`\n"
                f"پلن درخواستی: **{plan_info}**\n\n"
                f"موجودی انبار این پلن: {len(data['configs'].get(plan_info, []))} عدد"
            ),
            parse_mode="Markdown",
            reply_markup=admin_markup
        )
        bot.reply_to(message, "✅ فیش شما دریافت شد و برای بررسی به ادمین **HyperConn** ارسال گردید. به زودی کانفیگ شما تحویل داده می‌شود.")

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    t = Thread(target=run_bot)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
