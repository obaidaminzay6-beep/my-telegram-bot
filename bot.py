import os
import re
import json
import time
import logging
import threading
import tempfile
import datetime
from pathlib import Path

import telebot
from telebot import types
from PIL import Image, ImageOps
import PyPDF2
from fpdf import FPDF
import jdatetime
import requests

# =============== NEXORA BOT CONFIG ===============
TOKEN = os.getenv("TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("TOKEN is missing.")

BOT_NAME = "NEXORA BOT v9.5"
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/DarkVenom404")
ADMIN_IDS = {7210433916}

DB_FILE = Path("user_data.json")
REMINDERS_FILE = Path("reminders.json")
RATINGS_FILE = Path("ratings.json")
MAINTENANCE_FILE = Path("maintenance.json")
MAX_FILE_MB = 20

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("nexora")
bot = telebot.TeleBot(TOKEN, threaded=True)

lock = threading.RLock()
user_modes = {}
user_text = {}
admin_broadcast_mode = set()

# =============== LANGUAGE TEXTS ===============
TEXT = {
    "fa": {
        "choose_lang": "🌍 لطفاً زبان خود را انتخاب کنید:",
        "welcome": "✨ **سلام {name} عزیز!**\n\nبه **NEXORA BOT** خوش آمدی. 👋\nمن جعبه‌ابزار دیجیتال همه‌کاره تو هستم!\n\n⚡️ **ابزارهای من:**\n📄 مدیریت فایل‌های PDF\n🤖 هوش مصنوعی و ترجمه\n⏰ یادآور هوشمند و تقویم\n\n👇 **برای شروع، یکی از گزینه‌های زیر را انتخاب کن:**",
        "language": "🌍 تغییر زبان",
        "support": "💬 پشتیبانی",
        "img_pdf": "🖼️ عکس به PDF",
        "text_pdf": "📝 متن به PDF",
        "pdf_text": "📄 PDF به متن",
        "ai_assistant": "🤖 دستیار هوش مصنوعی",
        "translate": "🌐 ترجمه متن",
        "date": "📅 تاریخ و ساعت",
        "about": "ℹ️ درباره ربات",
        "profile": "👤 پروفایل من",
        "prompt_img_pdf": "🖼️ عکس خود را بفرست تا به PDF تبدیل کنم.",
        "prompt_text_pdf": "📝 متن خود را بفرست تا به PDF تبدیل کنم.",
        "prompt_pdf_text": "📄 فایل PDF خود را بفرست.",
        "prompt_translate": "🌐 متن خود را برای ترجمه بفرست.",
        "prompt_ai": "🤖 لطفاً سوال خود را بنویسید.\n(برای خروج روی بازگشت به منو بزنید)",
        "processing": "⏳ در حال پردازش؛ لطفاً صبر کن.",
        "done": "✅ عملیات با موفقیت انجام شد.",
        "error": "❌ عملیات انجام نشد. دوباره امتحان کن.",
        "bad_file": "❌ لطفاً فایل مناسب این ابزار را بفرست.",
        "too_large": "❌ حجم فایل بیش از حد مجاز است.",
        "text_options": "متن دریافت شد. انتخاب کن چه کاری انجام بدهم:",
        "opt_translate": "🌐 ترجمه",
        "opt_pdf": "📝 تبدیل به PDF",
        "back": "🔙 بازگشت به منو",
        "help": "📖 راهنمای NEXORA BOT\n\n۱. از منو یک ابزار انتخاب کن.\n۲. متن یا فایل مورد نیاز را بفرست.\n۳. برای بازگشت از دکمه خانه استفاده کن.",
        "about_text": "✨ **NEXORA BOT**\nنسخه 9.5\nجعبه‌ابزار دیجیتال شما.\n\n👨‍💻 توسعه‌دهنده: @DarkVenom404",
        "remind_help": "فرمت یادآوری:\n/remind 10m متن یادآوری\n\nواحدها: s ثانیه، m دقیقه، h ساعت، d روز",
        "remind_bad": "❌ فرمت اشتباه است. مثال: /remind 10m تماس بگیر",
        "remind_ok": "✅ یادآوری برای {when} دیگر تنظیم شد.",
        "profile_text": "👤 پروفایل شما\n\nنام: {name}\nشناسه: {id}\nزبان: {lang}\nتاریخ عضویت: {joined}\nیادآورهای فعال: {reminders}",
        "admin_only": "این فرمان مخصوص مدیر ربات است.",
        "admin_stats": "📊 **آمار ربات**\n\n👥 کل کاربران: {users}\n✅ تایید شده: {approved}\n⏳ در انتظار تایید: {pending}\n⏰ یادآورهای فعال: {reminders}",
        "translated": "🌐 ترجمه:\n\n{result}",
        "no_pdf_text": "❌ متنی پیدا نشد؛ ممکن است PDF اسکن‌شده باشد.",
        "rate_prompt": "⭐ لطفاً به این ابزار امتیاز بده (۱ تا ۵):",
        "rate_thanks": "🙏 ممنون از امتیاز شما!",
        "maintenance_msg": "🛠️ ربات موقتاً در حال تعمیر است. لطفاً بعداً مراجعه کنید.",
        "broadcast_prompt": "📢 لطفاً پیام خود را برای ارسال همگانی بنویسید:",
        "broadcast_done": "✅ پیام شما به {count} کاربر ارسال شد.",
        "lock_done": "🔒 ربات قفل شد (حالت تعمیر).",
        "unlock_done": "🔓 ربات از حالت تعمیر خارج شد.",
        "wait_approval": "⏳ حساب شما در حال بررسی است.\nلطفاً منتظر تایید مدیر ربات بمانید.",
        "user_approved": "✅ حساب شما تایید شد! اکنون می‌توانید از ربات استفاده کنید.",
        "user_rejected": "❌ متاسفانه دسترسی شما به ربات رد شد.",
        "admin_new_user": "👤 **درخواست دسترسی جدید**\n\nنام: {name}\nآیدی: `{id}`\n\nآیا اجازه استفاده می‌دهید؟",
        "approved_btn": "✅ تایید",
        "rejected_btn": "❌ رد",
        "admin_panel": "👑 **پنل مدیریت**\nلطفاً یک گزینه را انتخاب کنید:",
        "btn_broadcast": "📢 ارسال همگانی",
        "btn_stats": "📊 آمار ربات",
        "btn_lock": "🔒 قفل ربات",
        "btn_unlock": "🔓 باز کردن ربات"
    },
    "en": {
        "choose_lang": "🌍 Please choose your language:",
        "welcome": "✨ **Hello {name}!**\n\nWelcome to **NEXORA BOT**. 👋\nI am your all-in-one digital toolkit!\n\n⚡️ **My Tools:**\n📄 PDF Management\n🤖 AI & Translation\n⏰ Smart Reminders & Calendar\n\n👇 **Select an option below to start:**",
        "language": "🌍 Change language",
        "support": "💬 Support",
        "img_pdf": "🖼️ Image to PDF",
        "text_pdf": "📝 Text to PDF",
        "pdf_text": "📄 PDF to Text",
        "ai_assistant": "🤖 AI Assistant",
        "translate": "🌐 Translate Text",
        "date": "📅 Date & Time",
        "about": "ℹ️ About Bot",
        "profile": "👤 My Profile",
        "prompt_img_pdf": "🖼️ Send an image to convert to PDF.",
        "prompt_text_pdf": "📝 Send text to convert to PDF.",
        "prompt_pdf_text": "📄 Send a PDF file.",
        "prompt_translate": "🌐 Send text to translate.",
        "prompt_ai": "🤖 Please type your question.\n(Click Back to Menu to exit)",
        "processing": "⏳ Processing. Please wait.",
        "done": "✅ Completed successfully.",
        "error": "❌ Operation failed. Please try again.",
        "bad_file": "❌ Please send a supported file.",
        "too_large": "❌ File exceeds the size limit.",
        "text_options": "Text received. Choose an action:",
        "opt_translate": "🌐 Translate",
        "opt_pdf": "📝 Convert to PDF",
        "back": "🔙 Back to menu",
        "help": "📖 NEXORA BOT Help\n\n1. Choose a tool from the menu.\n2. Send the requested text or file.",
        "about_text": "✨ **NEXORA BOT**\nVersion 9.5\nYour digital toolkit.\n\n👨‍💻 Developer: @DarkVenom404",
        "remind_help": "Reminder format:\n/remind 10m reminder text",
        "remind_bad": "❌ Invalid format. Example: /remind 10m Call back",
        "remind_ok": "✅ Reminder set for {when} from now.",
        "profile_text": "👤 Your Profile\n\nName: {name}\nID: {id}\nLanguage: {lang}\nJoined: {joined}\nActive reminders: {reminders}",
        "admin_only": "This command is for the bot administrator.",
        "admin_stats": "📊 **Bot Stats**\n\n👥 Total Users: {users}\n✅ Approved: {approved}\n⏳ Pending: {pending}\n⏰ Active Reminders: {reminders}",
        "translated": "🌐 Translation:\n\n{result}",
        "no_pdf_text": "❌ No text found. The PDF may contain scanned pages.",
        "rate_prompt": "⭐ Please rate this tool (1 to 5):",
        "rate_thanks": "🙏 Thanks for your rating!",
        "maintenance_msg": "🛠️ Bot is under maintenance. Please try again later.",
        "broadcast_prompt": "📢 Please enter your broadcast message:",
        "broadcast_done": "✅ Message sent to {count} users.",
        "lock_done": "🔒 Bot locked (maintenance mode).",
        "unlock_done": "🔓 Bot unlocked.",
        "wait_approval": "⏳ Your account is pending review.\nPlease wait for admin approval.",
        "user_approved": "✅ Your account has been approved! You can now use the bot.",
        "user_rejected": "❌ Unfortunately, your access has been denied.",
        "admin_new_user": "👤 **New Access Request**\n\nName: {name}\nID: `{id}`\n\nDo you allow access?",
        "approved_btn": "✅ Approve",
        "rejected_btn": "❌ Reject",
        "admin_panel": "👑 **Admin Panel**\nPlease select an option:",
        "btn_broadcast": "📢 Broadcast",
        "btn_stats": "📊 Bot Stats",
        "btn_lock": "🔒 Lock Bot",
        "btn_unlock": "🔓 Unlock Bot"
    },
}

# =============== DATABASE ===============
def load_json(path):
    try:
        with lock:
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    result = json.load(f)
                    return result if isinstance(result, dict) else {}
    except Exception:
        logger.exception("Database read error: %s", path)
    return {}

def save_json(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    try:
        with lock:
            with temp.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp, path)
    except Exception:
        logger.exception("Database write error: %s", path)

def language(chat_id):
    db = load_json(DB_FILE)
    return db.get(str(chat_id), {}).get("lang", "fa")

def tr(chat_id, key, **kwargs):
    lang = language(chat_id)
    return TEXT.get(lang, TEXT["fa"]).get(key, TEXT["fa"].get(key, key)).format(**kwargs)

def register_user(user):
    db = load_json(DB_FILE)
    key = str(user.id)
    is_new = key not in db
    if is_new:
        db[key] = {
            "joined": datetime.datetime.now().strftime("%Y-%m-%d"),
            "first_name": user.first_name or "",
            "lang": "fa",
            "approved": False if user.id not in ADMIN_IDS else True
        }
        save_json(DB_FILE, db)
    else:
        if db[key].get("first_name") != (user.first_name or ""):
            db[key]["first_name"] = user.first_name or ""
            save_json(DB_FILE, db)
    return is_new

def is_approved(user_id):
    if user_id in ADMIN_IDS:
        return True
    db = load_json(DB_FILE)
    return db.get(str(user_id), {}).get("approved", False)

def set_language(chat_id, lang):
    db = load_json(DB_FILE)
    record = db.setdefault(str(chat_id), {
        "joined": datetime.datetime.now().strftime("%Y-%m-%d"),
        "approved": chat_id in ADMIN_IDS
    })
    record["lang"] = lang
    save_json(DB_FILE, db)

# =============== MAINTENANCE ===============
def is_locked():
    return load_json(MAINTENANCE_FILE).get("locked", False)

# =============== MENUS ===============
def lang_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("🇮🇷 فارسی", callback_data="setlang_fa"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="setlang_en")
    )
    return markup

def main_menu(chat_id):
    labels = TEXT[language(chat_id)]
    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.row(
        types.InlineKeyboardButton(labels["img_pdf"], callback_data="img_to_pdf"),
        types.InlineKeyboardButton(labels["text_pdf"], callback_data="text_to_pdf")
    )
    markup.row(
        types.InlineKeyboardButton(labels["pdf_text"], callback_data="pdf_to_text"),
        types.InlineKeyboardButton(labels["translate"], callback_data="translate")
    )
    markup.row(
        types.InlineKeyboardButton(labels["ai_assistant"], callback_data="ai_assistant"),
        types.InlineKeyboardButton(labels["date"], callback_data="date")
    )
    markup.row(
        types.InlineKeyboardButton(labels["language"], callback_data="language"),
        types.InlineKeyboardButton(labels["support"], url=SUPPORT_LINK)
    )
    markup.row(
        types.InlineKeyboardButton(labels["about"], callback_data="about")
    )
    return markup

def back_menu(chat_id):
    return types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(tr(chat_id, "back"), callback_data="home")
    )

def show_home(chat_id, name=""):
    user_modes.pop(str(chat_id), None)
    user_text.pop(str(chat_id), None)
    bot.send_message(
        chat_id,
        tr(chat_id, "welcome", name=name or "دوست عزیز"),
        reply_markup=main_menu(chat_id),
        parse_mode="Markdown"
    )

# =============== PDF SUPPORT ===============
def make_pdf(text, output):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    font_path = os.getenv("PDF_UNICODE_FONT", "").strip()

    candidates = [
        font_path,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    font = next((p for p in candidates if p and os.path.isfile(p)), None)
    needs_unicode = any(ord(ch) > 127 for ch in text)

    if needs_unicode and not font:
        raise RuntimeError("Unicode font missing.")

    pdf.add_page()
    if font:
        pdf.add_font("Nexora", fname=font)
        pdf.set_font("Nexora", size=12)
    else:
        pdf.set_font("Helvetica", size=12)

    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        shape = lambda s: get_display(arabic_reshaper.reshape(s))
    except ImportError:
        shape = lambda s: s

    for line in text.splitlines() or [""]:
        pdf.multi_cell(0, 8, shape(line))
    pdf.output(str(output))

# =============== REMINDERS ===============
def reminder_worker():
    while True:
        try:
            reminders = load_json(REMINDERS_FILE)
            now = time.time()
            changed = False
            for chat_id, items in list(reminders.items()):
                pending = []
                for item in items if isinstance(items, list) else []:
                    if now >= float(item.get("time", 0)):
                        try:
                            bot.send_message(int(chat_id), "⏰ " + item.get("text", "یادآوری"))
                            changed = True
                        except Exception:
                            pending.append(item)
                    else:
                        pending.append(item)
                reminders[chat_id] = pending
            if changed:
                save_json(REMINDERS_FILE, reminders)
        except Exception:
            logger.exception("Reminder worker error")
        time.sleep(10)

threading.Thread(target=reminder_worker, daemon=True, name="reminder-worker").start()

@bot.message_handler(commands=["remind"])
def reminder_command(message):
    register_user(message.from_user)
    if not check_lock(message.chat.id, message.from_user.id): return
    if not is_approved(message.from_user.id):
        bot.reply_to(message, tr(message.chat.id, "wait_approval"))
        return
        
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, tr(message.chat.id, "remind_help"))
        return
    match = re.fullmatch(r"([1-9]\d{0,5})([smhd])", parts[1].lower())
    if not match:
        bot.reply_to(message, tr(message.chat.id, "remind_bad"))
        return
    amount = int(match.group(1))
    unit = match.group(2)
    multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    seconds = amount * multiplier[unit]
    if seconds > 365 * 86400:
        bot.reply_to(message, tr(message.chat.id, "remind_bad"))
        return
    reminders = load_json(REMINDERS_FILE)
    key = str(message.chat.id)
    reminders.setdefault(key, []).append({"text": parts[2], "time": time.time() + seconds})
    save_json(REMINDERS_FILE, reminders)
    bot.reply_to(message, tr(message.chat.id, "remind_ok", when=parts[1]))

# =============== LOCK CHECK ===============
def check_lock(chat_id, user_id):
    if is_locked() and user_id not in ADMIN_IDS:
        bot.send_message(chat_id, tr(chat_id, "maintenance_msg"))
        return False
    return True

# =============== COMMANDS ===============
@bot.message_handler(commands=["start"])
def start_command(message):
    is_new = register_user(message.from_user)
    if not check_lock(message.chat.id, message.from_user.id): return
    
    if is_new and message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, tr(message.chat.id, "choose_lang"), reply_markup=lang_menu())
        for admin_id in ADMIN_IDS:
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(tr(admin_id, "approved_btn"), callback_data=f"approve_{message.from_user.id}"),
                types.InlineKeyboardButton(tr(admin_id, "rejected_btn"), callback_data=f"reject_{message.from_user.id}")
            )
            try:
                bot.send_message(admin_id, tr(admin_id, "admin_new_user", name=message.from_user.first_name, id=message.from_user.id), reply_markup=markup, parse_mode="Markdown")
            except Exception:
                pass
        return

    if not is_approved(message.from_user.id):
        bot.send_message(message.chat.id, tr(message.chat.id, "wait_approval"))
        return
        
    show_home(message.chat.id, message.from_user.first_name)

@bot.message_handler(commands=["language"])
def language_command(message):
    register_user(message.from_user)
    bot.send_message(message.chat.id, tr(message.chat.id, "choose_lang"), reply_markup=lang_menu())

@bot.message_handler(commands=["panel"])
def admin_panel(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, tr(message.chat.id, "admin_only"))
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton(tr(message.chat.id, "btn_broadcast"), callback_data="admin_broadcast"),
        types.InlineKeyboardButton(tr(message.chat.id, "btn_stats"), callback_data="admin_stats")
    )
    markup.row(
        types.InlineKeyboardButton(tr(message.chat.id, "btn_lock"), callback_data="admin_lock"),
        types.InlineKeyboardButton(tr(message.chat.id, "btn_unlock"), callback_data="admin_unlock")
    )
    markup.row(types.InlineKeyboardButton(tr(message.chat.id, "back"), callback_data="home"))
    bot.send_message(message.chat.id, tr(message.chat.id, "admin_panel"), reply_markup=markup)

@bot.message_handler(commands=["help"])
def help_command(message):
    register_user(message.from_user)
    if not check_lock(message.chat.id, message.from_user.id): return
    if not is_approved(message.from_user.id):
        bot.send_message(message.chat.id, tr(message.chat.id, "wait_approval"))
        return
    bot.send_message(message.chat.id, tr(message.chat.id, "help"), reply_markup=back_menu(message.chat.id))

@bot.message_handler(commands=["cancel"])
def cancel_command(message):
    if not check_lock(message.chat.id, message.from_user.id): return
    user_modes.pop(str(message.chat.id), None)
    user_text.pop(str(message.chat.id), None)
    admin_broadcast_mode.discard(message.from_user.id)
    bot.send_message(message.chat.id, "✅ " + tr(message.chat.id, "back"), reply_markup=main_menu(message.chat.id))

# =============== BROADCAST ===============
def send_broadcast(message):
    admin_broadcast_mode.discard(message.from_user.id)
    if message.from_user.id not in ADMIN_IDS: return
    users = load_json(DB_FILE)
    count = 0
    for chat_id in users.keys():
        try:
            bot.send_message(chat_id, message.text)
            count += 1
            time.sleep(0.05)
        except Exception:
            pass
    bot.reply_to(message, tr(message.chat.id, "broadcast_done", count=count))

# =============== RATING ===============
def ask_rating(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=5)
    for i in range(1, 6):
        markup.add(types.InlineKeyboardButton("⭐" * i, callback_data=f"rate_{i}"))
    bot.send_message(chat_id, tr(chat_id, "rate_prompt"), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rate_"))
def handle_rating(call):
    chat_id = call.message.chat.id
    rating = int(call.data.split("_")[1])
    ratings = load_json(RATINGS_FILE)
    ratings.setdefault(str(chat_id), []).append(rating)
    save_json(RATINGS_FILE, ratings)
    bot.answer_callback_query(call.id, tr(chat_id, "rate_thanks"))
    bot.edit_message_text(tr(chat_id, "rate_thanks"), chat_id, call.message.message_id)

# =============== BUTTON HANDLER ===============
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    user = call.from_user
    register_user(user)
    bot.answer_callback_query(call.id)

    if call.data.startswith("approve_") and user.id in ADMIN_IDS:
        uid = call.data.split("_")[1]
        db = load_json(DB_FILE)
        if uid in db:
            db[uid]["approved"] = True
            save_json(DB_FILE, db)
            try: bot.send_message(uid, tr(uid, "user_approved"))
            except: pass
            bot.edit_message_text(f"✅ User {uid} approved.", chat_id, call.message.message_id)
        return
    if call.data.startswith("reject_") and user.id in ADMIN_IDS:
        uid = call.data.split("_")[1]
        db = load_json(DB_FILE)
        if uid in db:
            db[uid]["approved"] = False
            save_json(DB_FILE, db)
            try: bot.send_message(uid, tr(uid, "user_rejected"))
            except: pass
            bot.edit_message_text(f"❌ User {uid} rejected.", chat_id, call.message.message_id)
        return

    if call.data.startswith("setlang_"):
        lang = call.data.split("_")[1]
        set_language(chat_id, lang)
        bot.delete_message(chat_id, call.message.message_id)
        if is_approved(user.id):
            show_home(chat_id, user.first_name)
        else:
            bot.send_message(chat_id, tr(chat_id, "wait_approval"))
        return

    if not check_lock(chat_id, user.id): return
    if not is_approved(user.id):
        bot.send_message(chat_id, tr(chat_id, "wait_approval"))
        return

    data = call.data

    if data == "admin_broadcast" and user.id in ADMIN_IDS:
        admin_broadcast_mode.add(user.id)
        bot.send_message(chat_id, tr(chat_id, "broadcast_prompt"))
        return
    if data == "admin_stats" and user.id in ADMIN_IDS:
        db = load_json(DB_FILE)
        approved_count = sum(1 for u in db.values() if u.get("approved"))
        pending_count = len(db) - approved_count
        rem = load_json(REMINDERS_FILE)
        rem_count = sum(len(x) for x in rem.values() if isinstance(x, list))
        bot.send_message(chat_id, tr(chat_id, "admin_stats", users=len(db), approved=approved_count, pending=pending_count, reminders=rem_count), parse_mode="Markdown")
        return
    if data == "admin_lock" and user.id in ADMIN_IDS:
        save_json(MAINTENANCE_FILE, {"locked": True})
        bot.send_message(chat_id, tr(chat_id, "lock_done"))
        return
    if data == "admin_unlock" and user.id in ADMIN_IDS:
        save_json(MAINTENANCE_FILE, {"locked": False})
        bot.send_message(chat_id, tr(chat_id, "unlock_done"))
        return

    if data == "home":
        show_home(chat_id, user.first_name)
        return
    if data == "language":
        bot.send_message(chat_id, tr(chat_id, "choose_lang"), reply_markup=lang_menu())
        return
    if data == "about":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(TEXT[language(chat_id)]["profile"], callback_data="profile"))
        markup.add(types.InlineKeyboardButton(tr(chat_id, "back"), callback_data="home"))
        bot.send_message(chat_id, tr(chat_id, "about_text"), reply_markup=markup, parse_mode="Markdown")
        return
    if data == "profile":
        db = load_json(DB_FILE)
        record = db.get(str(chat_id), {})
        reminders = load_json(REMINDERS_FILE).get(str(chat_id), [])
        bot.send_message(chat_id, tr(chat_id, "profile_text", name=user.first_name or "—", id=chat_id, lang=language(chat_id), joined=record.get("joined", "—"), reminders=len(reminders)), reply_markup=back_menu(chat_id))
        return
    if data == "date":
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=4, minutes=30)))
        shamsi = jdatetime.datetime.fromgregorian(datetime=now.replace(tzinfo=None))
        
        lang = language(chat_id)
        if lang == "fa":
            days_fa = {"Saturday": "شنبه", "Sunday": "یکشنبه", "Monday": "دوشنبه", "Tuesday": "سه‌شنبه", "Wednesday": "چهارشنبه", "Thursday": "پنجشنبه", "Friday": "جمعه"}
            day_name = days_fa.get(shamsi.strftime('%A'), shamsi.strftime('%A'))
            txt = f"📅 تاریخ افغانستان\n\nشمسی: {shamsi.strftime('%Y/%m/%d')}\nمیلادی: {now.strftime('%Y-%m-%d')}\nساعت: {now.strftime('%H:%M:%S')}\nروز: {day_name}"
        else:
            txt = f"📅 Date & Time\n\nShamsi: {shamsi.strftime('%Y/%m/%d')}\nGregorian: {now.strftime('%Y-%m-%d')}\nTime: {now.strftime('%H:%M:%S')}\nDay: {shamsi.strftime('%A')}"
        bot.send_message(chat_id, txt, reply_markup=back_menu(chat_id))
        return

    modes = {
        "img_to_pdf": "prompt_img_pdf",
        "text_to_pdf": "prompt_text_pdf",
        "pdf_to_text": "prompt_pdf_text",
        "translate": "prompt_translate",
        "ai_assistant": "prompt_ai"
    }
    if data in modes:
        user_modes[str(chat_id)] = data
        bot.send_message(chat_id, tr(chat_id, modes[data]), reply_markup=back_menu(chat_id))
        return

    if data == "do_pdf":
        text = user_text.get(str(chat_id))
        if not text:
            bot.send_message(chat_id, tr(chat_id, "error"))
            return
        try:
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "text.pdf"
                make_pdf(text, path)
                with path.open("rb") as f: bot.send_document(chat_id, f, caption=tr(chat_id, "done"))
            ask_rating(chat_id)
        except Exception:
            logger.exception("Text to PDF error")
            bot.send_message(chat_id, tr(chat_id, "error"))
        return

# =============== TEXT HANDLER ===============
@bot.message_handler(func=lambda m: bool(m.text) and not m.text.startswith("/"))
def text_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    register_user(message.from_user)
    
    if user_id in admin_broadcast_mode:
        send_broadcast(message)
        return

    if not check_lock(chat_id, user_id): return
    if not is_approved(user_id):
        bot.send_message(chat_id, tr(chat_id, "wait_approval"))
        return
        
    mode = user_modes.get(str(chat_id))
    text = message.text
    labels = TEXT[language(chat_id)]

    if text in {labels["help_btn"], "ℹ️ راهنما", "ℹ️ Help", "راهنما", "Help"}:
        bot.send_message(chat_id, tr(chat_id, "help"), reply_markup=back_menu(chat_id))
        return

    if mode == "translate":
        try:
            dest = "fa" if language(chat_id) == "fa" else "en"
            url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair=en|{dest}" if dest=="fa" else f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair=fa|en"
            response = requests.get(url, timeout=15)
            data = response.json()
            result_text = data["responseData"]["translatedText"]
            
            bot.send_message(chat_id, tr(chat_id, "translated", result=result_text), reply_markup=back_menu(chat_id))
            ask_rating(chat_id)
        except Exception:
            logger.exception("Translation error")
            bot.send_message(chat_id, tr(chat_id, "error"))
        user_modes.pop(str(chat_id), None)
        return

    if mode == "text_to_pdf":
        try:
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "text.pdf"
                make_pdf(text, path)
                with path.open("rb") as f:
                    bot.send_document(chat_id, f, caption=tr(chat_id, "done"), reply_markup=back_menu(chat_id))
            ask_rating(chat_id)
        except Exception:
            logger.exception("Text to PDF error")
            bot.send_message(chat_id, tr(chat_id, "error"))
        user_modes.pop(str(chat_id), None)
        return

    if mode == "ai_assistant":
        try:
            response = requests.post(
                "https://text.pollinations.ai/",
                json={"messages": [
                    {"role": "system", "content": "You are a helpful, smart AI assistant. Answer clearly and accurately in the user's language."},
                    {"role": "user", "content": text}
                ]},
                timeout=30
            )
            answer = response.text
            bot.send_message(chat_id, f"🤖 پاسخ هوش مصنوعی:\n\n{answer}", reply_markup=back_menu(chat_id))
        except Exception:
            logger.exception("AI error")
            bot.send_message(chat_id, tr(chat_id, "error"), reply_markup=back_menu(chat_id))
        return

    user_text[str(chat_id)] = text
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.row(types.InlineKeyboardButton(tr(chat_id, "opt_translate"), callback_data="do_translate"))
    markup.row(types.InlineKeyboardButton(tr(chat_id, "opt_pdf"), callback_data="do_pdf"))
    markup.row(types.InlineKeyboardButton(tr(chat_id, "back"), callback_data="home"))
    bot.send_message(chat_id, tr(chat_id, "text_options"), reply_markup=markup)

# =============== MEDIA HANDLER ===============
def get_file_bytes(file_id):
    info = bot.get_file(file_id)
    if info.file_size and info.file_size > MAX_FILE_MB * 1024 * 1024:
        raise ValueError("too_large")
    data = bot.download_file(info.file_path)
    if len(data) > MAX_FILE_MB * 1024 * 1024:
        raise ValueError("too_large")
    return data

@bot.message_handler(content_types=["photo", "document"])
def media_handler(message):
    chat_id = message.chat.id
    register_user(message.from_user)
    if not check_lock(chat_id, message.from_user.id): return
    if not is_approved(message.from_user.id):
        bot.send_message(chat_id, tr(chat_id, "wait_approval"))
        return

    mode = user_modes.get(str(chat_id))
    is_photo = message.content_type == "photo"
    
    is_pdf = False
    if message.content_type == "document":
        mime = message.document.mime_type or ""
        fname = (message.document.file_name or "").lower()
        if "pdf" in mime or fname.endswith(".pdf") or "pdf" in fname:
            is_pdf = True

    try:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)

            if is_photo and mode == "img_to_pdf":
                raw = get_file_bytes(message.photo[-1].file_id)
                source = td / "input.jpg"
                output = td / "image.pdf"
                source.write_bytes(raw)
                with Image.open(source) as img:
                    img = ImageOps.exif_transpose(img).convert("RGB")
                    img.save(output, "PDF", resolution=150)
                with output.open("rb") as f:
                    bot.send_document(chat_id, f, caption=tr(chat_id, "done"), reply_markup=back_menu(chat_id))
                user_modes.pop(str(chat_id), None)
                ask_rating(chat_id)
                return

            if is_pdf and mode == "pdf_to_text":
                raw = get_file_bytes(message.document.file_id)
                source = td / "input.pdf"
                output = td / "extracted.txt"
                source.write_bytes(raw)
                with source.open("rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    extracted = "\n\n".join(page.extract_text() or "" for page in reader.pages)
                if not extracted.strip():
                    bot.send_message(chat_id, tr(chat_id, "no_pdf_text"), reply_markup=back_menu(chat_id))
                else:
                    output.write_text(extracted, encoding="utf-8")
                    with output.open("rb") as f:
                        bot.send_document(chat_id, f, caption=tr(chat_id, "done"), reply_markup=back_menu(chat_id))
                user_modes.pop(str(chat_id), None)
                ask_rating(chat_id)
                return

        bot.send_message(chat_id, tr(chat_id, "bad_file"), reply_markup=back_menu(chat_id))
    except ValueError:
        bot.send_message(chat_id, tr(chat_id, "too_large"))
    except Exception:
        logger.exception("Media processing error")
        bot.send_message(chat_id, tr(chat_id, "error"), reply_markup=back_menu(chat_id))

# =============== START BOT ===============
if __name__ == "__main__":
    logger.info("%s is starting...", BOT_NAME)
    
    try:
        bot.set_my_commands([
            types.BotCommand("start", "شروع ربات / Start Bot"),
            types.BotCommand("language", "تغییر زبان / Change Language")
        ])
        
        for admin_id in ADMIN_IDS:
            try:
                bot.set_my_commands([
                    types.BotCommand("start", "شروع ربات / Start Bot"),
                    types.BotCommand("panel", "پنل مدیریت / Admin Panel"),
                    types.BotCommand("language", "تغییر زبان / Change Language")
                ], scope=types.BotCommandScopeChat(admin_id))
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Failed to set commands: {e}")

    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
