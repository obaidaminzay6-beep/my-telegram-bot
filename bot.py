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
import qrcode
import PyPDF2
from fpdf import FPDF
from googletrans import Translator
import jdatetime

# =============== NEXORA BOT CONFIG ===============
TOKEN = os.getenv("TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("TOKEN is missing. Set it in your environment.")

BOT_NAME = "NEXORA BOT"
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/DarkVenom404")
ADMIN_IDS = {7210433916}

DB_FILE = Path("user_data.json")
REMINDERS_FILE = Path("reminders.json")
RATINGS_FILE = Path("ratings.json")
MAINTENANCE_FILE = Path("maintenance.json")
MAX_FILE_MB = 20

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)
logger = logging.getLogger("nexora")
bot = telebot.TeleBot(TOKEN, threaded=True)

lock = threading.RLock()
user_modes = {}
user_text = {}

# =============== LANGUAGE TEXTS ===============
TEXT = {
    "fa": {
        "welcome": (
            "✨ سلام {name} عزیز!\n\n"
            "به NEXORA BOT خوش آمدی.\n"
            "جعبه‌ابزار دیجیتالی تو برای کارهای روزمره.\n\n"
            "یکی از ابزارهای زیر را انتخاب کن:"
        ),
        "language": "🌍 تغییر زبان",
        "support": "💬 پشتیبانی",
        "home": "🏠 خانه",
        "help_btn": "ℹ️ راهنما",
        "img_pdf": "🖼️ عکس به PDF",
        "text_pdf": "📝 متن به PDF",
        "pdf_text": "📄 PDF به متن",
        "compress": "🗜️ فشرده‌سازی عکس",
        "qr": "📱 ساخت QR",
        "translate": "🌐 ترجمه متن",
        "date": "📅 تاریخ و ساعت",
        "profile": "👤 پروفایل من",
        "about": "ℹ️ درباره ربات",
        "prompt_img_pdf": "🖼️ عکس خود را بفرست تا به PDF تبدیل کنم.",
        "prompt_text_pdf": "📝 متن خود را بفرست تا به PDF تبدیل کنم.",
        "prompt_pdf_text": "📄 فایل PDF خود را بفرست.",
        "prompt_compress": "🗜️ عکس خود را بفرست تا فشرده شود.",
        "prompt_qr": "📱 متن یا لینک را بفرست تا QR بسازم.",
        "prompt_translate": "🌐 متن خود را برای ترجمه بفرست.",
        "processing": "⏳ در حال پردازش؛ لطفاً صبر کن.",
        "done": "✅ عملیات با موفقیت انجام شد.",
        "error": "❌ عملیات انجام نشد. دوباره امتحان کن.",
        "bad_file": "❌ لطفاً فایل مناسب این ابزار را بفرست.",
        "too_large": "❌ حجم فایل بیش از حد مجاز است.",
        "text_options": "متن دریافت شد. انتخاب کن چه کاری انجام بدهم:",
        "opt_qr": "📱 ساخت QR",
        "opt_translate": "🌐 ترجمه",
        "opt_pdf": "📝 تبدیل به PDF",
        "back": "🔙 بازگشت به منو",
        "choose_lang": "زبان را انتخاب کن:",
        "help": (
            "📖 راهنمای NEXORA BOT\n\n"
            "۱. از منو یک ابزار انتخاب کن.\n"
            "۲. متن یا فایل مورد نیاز را بفرست.\n"
            "۳. برای بازگشت از دکمه خانه استفاده کن.\n\n"
            "یادآوری:\n/remind 10m به مادرم زنگ بزنم\n"
            "لغو عملیات: /cancel"
        ),
        "about_text": (
            "✨ NEXORA BOT\n"
            "نسخه 6.0 (نهایی)\n"
            "ابزارهای فایل، QR، ترجمه، یادآوری، پروفایل و امتیازدهی."
        ),
        "remind_help": (
            "فرمت یادآوری:\n"
            "/remind 10m متن یادآوری\n\n"
            "واحدها: s ثانیه، m دقیقه، h ساعت، d روز"
        ),
        "remind_bad": "❌ فرمت اشتباه است. مثال: /remind 10m تماس بگیر",
        "remind_ok": "✅ یادآوری برای {when} دیگر تنظیم شد.",
        "profile_text": (
            "👤 پروفایل شما\n\nنام: {name}\n"
            "شناسه: {id}\nزبان: {lang}\n"
            "تاریخ عضویت: {joined}\nیادآورهای فعال: {reminders}"
        ),
        "admin_only": "این فرمان مخصوص مدیر ربات است.",
        "admin_stats": "📊 کاربران: {users}\nیادآورهای فعال: {reminders}",
        "translated": "🌐 ترجمه:\n\n{result}",
        "no_pdf_text": "❌ متنی پیدا نشد؛ ممکن است PDF اسکن‌شده باشد.",
        "rate_prompt": "⭐ لطفاً به این ابزار امتیاز بده (۱ تا ۵):",
        "rate_thanks": "🙏 ممنون از امتیاز شما!",
        "maintenance_msg": "🛠️ ربات موقتاً در حال تعمیر است. لطفاً بعداً مراجعه کنید.",
        "broadcast_prompt": "📢 لطفاً پیام خود را برای ارسال همگانی بنویسید:",
        "broadcast_done": "✅ پیام شما به {count} کاربر ارسال شد.",
        "lock_done": "🔒 ربات قفل شد (حالت تعمیر).",
        "unlock_done": "🔓 ربات از حالت تعمیر خارج شد."
    },
    "en": {
        "welcome": (
            "✨ Hello {name}!\n\nWelcome to NEXORA BOT.\n"
            "Your digital toolbox for everyday tasks.\n\nChoose a tool:"
        ),
        "language": "🌍 Change language",
        "support": "💬 Support",
        "home": "🏠 Home",
        "help_btn": "ℹ️ Help",
        "img_pdf": "🖼️ Image to PDF",
        "text_pdf": "📝 Text to PDF",
        "pdf_text": "📄 PDF to Text",
        "compress": "🗜️ Compress Image",
        "qr": "📱 Create QR",
        "translate": "🌐 Translate Text",
        "date": "📅 Date & Time",
        "profile": "👤 My Profile",
        "about": "ℹ️ About Bot",
        "prompt_img_pdf": "🖼️ Send an image to convert to PDF.",
        "prompt_text_pdf": "📝 Send text to convert to PDF.",
        "prompt_pdf_text": "📄 Send a PDF file.",
        "prompt_compress": "🗜️ Send an image to compress.",
        "prompt_qr": "📱 Send text or a link to create a QR code.",
        "prompt_translate": "🌐 Send text to translate.",
        "processing": "⏳ Processing. Please wait.",
        "done": "✅ Completed successfully.",
        "error": "❌ Operation failed. Please try again.",
        "bad_file": "❌ Please send a supported file.",
        "too_large": "❌ File exceeds the size limit.",
        "text_options": "Text received. Choose an action:",
        "opt_qr": "📱 Create QR",
        "opt_translate": "🌐 Translate",
        "opt_pdf": "📝 Convert to PDF",
        "back": "🔙 Back to menu",
        "choose_lang": "Choose your language:",
        "help": (
            "📖 NEXORA BOT Help\n\n"
            "1. Choose a tool from the menu.\n"
            "2. Send the requested text or file.\n"
            "Reminder: /remind 10m Call mom\n"
            "Cancel current operation: /cancel"
        ),
        "about_text": (
            "✨ NEXORA BOT\nVersion 6.0 (Final)\n"
            "File tools, QR, translation, reminders, profile and rating."
        ),
        "remind_help": (
            "Reminder format:\n/remind 10m reminder text\n"
            "Units: s seconds, m minutes, h hours, d days"
        ),
        "remind_bad": "❌ Invalid format. Example: /remind 10m Call back",
        "remind_ok": "✅ Reminder set for {when} from now.",
        "profile_text": (
            "👤 Your Profile\n\nName: {name}\nID: {id}\n"
            "Language: {lang}\nJoined: {joined}\n"
            "Active reminders: {reminders}"
        ),
        "admin_only": "This command is for the bot administrator.",
        "admin_stats": "📊 Users: {users}\nActive reminders: {reminders}",
        "translated": "🌐 Translation:\n\n{result}",
        "no_pdf_text": "❌ No text found. The PDF may contain scanned pages.",
        "rate_prompt": "⭐ Please rate this tool (1 to 5):",
        "rate_thanks": "🙏 Thanks for your rating!",
        "maintenance_msg": "🛠️ Bot is under maintenance. Please try again later.",
        "broadcast_prompt": "📢 Please enter your broadcast message:",
        "broadcast_done": "✅ Message sent to {count} users.",
        "lock_done": "🔒 Bot locked (maintenance mode).",
        "unlock_done": "🔓 Bot unlocked."
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
    if key not in db:
        db[key] = {
            "joined": datetime.datetime.now().strftime("%Y-%m-%d"),
            "first_name": user.first_name or "",
            "lang": "fa",
        }
    else:
        db[key]["first_name"] = user.first_name or ""
    save_json(DB_FILE, db)

def set_language(chat_id, lang):
    db = load_json(DB_FILE)
    record = db.setdefault(str(chat_id), {
        "joined": datetime.datetime.now().strftime("%Y-%m-%d")
    })
    record["lang"] = lang
    save_json(DB_FILE, db)

# =============== MAINTENANCE ===============
def is_locked():
    return load_json(MAINTENANCE_FILE).get("locked", False)

# =============== MENUS ===============
def main_menu(chat_id):
    labels = TEXT[language(chat_id)]
    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.row(
        types.InlineKeyboardButton(labels["img_pdf"], callback_data="img_to_pdf"),
        types.InlineKeyboardButton(labels["text_pdf"], callback_data="text_to_pdf")
    )
    markup.row(
        types.InlineKeyboardButton(labels["pdf_text"], callback_data="pdf_to_text"),
        types.InlineKeyboardButton(labels["compress"], callback_data="compress")
    )
    markup.row(
        types.InlineKeyboardButton(labels["qr"], callback_data="qr"),
        types.InlineKeyboardButton(labels["translate"], callback_data="translate")
    )
    markup.row(
        types.InlineKeyboardButton(labels["date"], callback_data="date"),
        types.InlineKeyboardButton(labels["profile"], callback_data="profile")
    )
    markup.row(
        types.InlineKeyboardButton(labels["language"], callback_data="language"),
        types.InlineKeyboardButton(labels["support"], url=SUPPORT_LINK)
    )
    markup.row(
        types.InlineKeyboardButton(labels["about"], callback_data="about")
    )
    return markup

def persistent_keyboard(chat_id):
    labels = TEXT[language(chat_id)]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton(labels["home"]),
        types.KeyboardButton(labels["help_btn"])
    )
    return markup

def back_menu(chat_id):
    return types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(
            tr(chat_id, "back"), callback_data="home"
        )
    )

def show_home(chat_id, name=""):
    user_modes.pop(str(chat_id), None)
    user_text.pop(str(chat_id), None)
    bot.send_message(
        chat_id,
        tr(chat_id, "welcome", name=name or "دوست عزیز"),
        reply_markup=main_menu(chat_id)
    )
    bot.send_message(chat_id, "👇", reply_markup=persistent_keyboard(chat_id))

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
        raise RuntimeError(
            "برای PDF فارسی فونت Unicode نصب کن و PDF_UNICODE_FONT را تنظیم کن."
        )

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
                            bot.send_message(
                                int(chat_id),
                                "⏰ " + item.get("text", "یادآوری")
                            )
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

threading.Thread(
    target=reminder_worker, daemon=True, name="reminder-worker"
).start()

@bot.message_handler(commands=["remind"])
def reminder_command(message):
    register_user(message.from_user)
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
    reminders.setdefault(key, []).append({
        "text": parts[2],
        "time": time.time() + seconds
    })
    save_json(REMINDERS_FILE, reminders)
    bot.reply_to(
        message, tr(message.chat.id, "remind_ok", when=parts[1])
    )

# =============== LOCK CHECK ===============
def check_lock(chat_id, user_id):
    """بررسی می‌کند که آیا ربات قفل است یا نه. اگر قفل بود، پیام می‌دهد."""
    if is_locked() and user_id not in ADMIN_IDS:
        bot.send_message(chat_id, tr(chat_id, "maintenance_msg"))
        return False
    return True

# =============== COMMANDS ===============
@bot.message_handler(commands=["start"])
def start_command(message):
    register_user(message.from_user)
    if not check_lock(message.chat.id, message.from_user.id):
        return
    show_home(message.chat.id, message.from_user.first_name)

@bot.message_handler(commands=["help"])
def help_command(message):
    register_user(message.from_user)
    if not check_lock(message.chat.id, message.from_user.id):
        return
    bot.send_message(
        message.chat.id, tr(message.chat.id, "help"),
        reply_markup=back_menu(message.chat.id)
    )

@bot.message_handler(commands=["cancel"])
def cancel_command(message):
    if not check_lock(message.chat.id, message.from_user.id):
        return
    user_modes.pop(str(message.chat.id), None)
    user_text.pop(str(message.chat.id), None)
    bot.send_message(
        message.chat.id, "✅ " + tr(message.chat.id, "back"),
        reply_markup=main_menu(message.chat.id)
    )
    bot.send_message(message.chat.id, "👇", reply_markup=persistent_keyboard(message.chat.id))

@bot.message_handler(commands=["admin"])
def admin_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, tr(message.chat.id, "admin_only"))
        return
    users = load_json(DB_FILE)
    reminders = load_json(REMINDERS_FILE)
    count = sum(len(x) for x in reminders.values() if isinstance(x, list))
    bot.send_message(
        message.chat.id,
        tr(message.chat.id, "admin_stats",
           users=len(users), reminders=count)
    )

@bot.message_handler(commands=["broadcast"])
def broadcast_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, tr(message.chat.id, "admin_only"))
        return
    msg = bot.reply_to(message, tr(message.chat.id, "broadcast_prompt"))
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    users = load_json(DB_FILE)
    count = 0
    for chat_id in users.keys():
        try:
            bot.send_message(chat_id, message.text)
            count += 1
        except:
            pass
    bot.reply_to(message, tr(message.chat.id, "broadcast_done", count=count))

@bot.message_handler(commands=["lock"])
def lock_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, tr(message.chat.id, "admin_only"))
        return
    save_json(MAINTENANCE_FILE, {"locked": True})
    bot.reply_to(message, tr(message.chat.id, "lock_done"))

@bot.message_handler(commands=["unlock"])
def unlock_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, tr(message.chat.id, "admin_only"))
        return
    save_json(MAINTENANCE_FILE, {"locked": False})
    bot.reply_to(message, tr(message.chat.id, "unlock_done"))

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
    register_user(call.from_user)
    bot.answer_callback_query(call.id)

    if call.data != "home":
        if not check_lock(chat_id, call.from_user.id):
            return

    data = call.data

    if data == "home":
        show_home(chat_id, call.from_user.first_name)
        return

    if data == "language":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.row(
            types.InlineKeyboardButton("دری / فارسی", callback_data="lang_fa"),
            types.InlineKeyboardButton("English", callback_data="lang_en")
        )
        markup.row(
            types.InlineKeyboardButton("🏠 Home", callback_data="home")
        )
        bot.send_message(
            chat_id, tr(chat_id, "choose_lang"), reply_markup=markup
        )
        return

    if data.startswith("lang_"):
        set_language(chat_id, data.split("_", 1)[1])
        show_home(chat_id, call.from_user.first_name)
        return

    if data == "about":
        bot.send_message(
            chat_id, tr(chat_id, "about_text"),
            reply_markup=back_menu(chat_id)
        )
        return

    if data == "profile":
        db = load_json(DB_FILE)
        record = db.get(str(chat_id), {})
        reminders = load_json(REMINDERS_FILE).get(str(chat_id), [])
        bot.send_message(
            chat_id,
            tr(
                chat_id, "profile_text",
                name=call.from_user.first_name or "—",
                id=chat_id,
                lang=language(chat_id),
                joined=record.get("joined", "—"),
                reminders=len(reminders)
            ),
            reply_markup=back_menu(chat_id)
        )
        return

    if data == "date":
        now = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=4, minutes=30))
        )
        shamsi = jdatetime.datetime.fromgregorian(
            datetime=now.replace(tzinfo=None)
        )
        bot.send_message(
            chat_id,
            f"📅 تاریخ افغانستان\n\n"
            f"شمسی: {shamsi.strftime('%Y/%m/%d')}\n"
            f"میلادی: {now.strftime('%Y-%m-%d')}\n"
            f"ساعت: {now.strftime('%H:%M:%S')}\n"
            f"روز: {shamsi.strftime('%A')}",
            reply_markup=back_menu(chat_id)
        )
        return

    modes = {
        "img_to_pdf": "prompt_img_pdf",
        "text_to_pdf": "prompt_text_pdf",
        "pdf_to_text": "prompt_pdf_text",
        "compress": "prompt_compress",
        "qr": "prompt_qr",
        "translate": "prompt_translate",
    }
    if data in modes:
        user_modes[str(chat_id)] = data
        bot.send_message(
            chat_id, tr(chat_id, modes[data]),
            reply_markup=back_menu(chat_id)
        )
        return

    if data in {"do_qr", "do_translate", "do_pdf"}:
        text = user_text.get(str(chat_id))
        if not text:
            bot.send_message(chat_id, tr(chat_id, "error"))
            return

        if data == "do_qr":
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "qr.png"
                qrcode.make(text).save(path)
                with path.open("rb") as f:
                    bot.send_photo(chat_id, f, caption=tr(chat_id, "done"))
            ask_rating(chat_id)
        elif data == "do_translate":
            try:
                dest = "fa" if language(chat_id) == "fa" else "en"
                result = Translator().translate(text, dest=dest)
                bot.send_message(
                    chat_id, tr(chat_id, "translated", result=result.text)
                )
                ask_rating(chat_id)
            except Exception:
                logger.exception("Translation error")
                bot.send_message(chat_id, tr(chat_id, "error"))
        elif data == "do_pdf":
            try:
                with tempfile.TemporaryDirectory() as td:
                    path = Path(td) / "text.pdf"
                    make_pdf(text, path)
                    with path.open("rb") as f:
                        bot.send_document(chat_id, f, caption=tr(chat_id, "done"))
                ask_rating(chat_id)
            except Exception:
                logger.exception("Text to PDF error")
                bot.send_message(chat_id, tr(chat_id, "error"))
        return

# =============== TEXT HANDLER ===============
@bot.message_handler(
    func=lambda m: bool(m.text) and not m.text.startswith("/")
)
def text_handler(message):
    chat_id = message.chat.id
    register_user(message.from_user)
    
    if not check_lock(chat_id, message.from_user.id):
        return

    mode = user_modes.get(str(chat_id))
    text = message.text

    if text in {"🏠 خانه", "🏠 Home", "Start", "شروع"}:
        show_home(chat_id, message.from_user.first_name)
        return

    if text in {"ℹ️ راهنما", "ℹ️ Help", "راهنما", "Help"}:
        bot.send_message(
            chat_id, tr(chat_id, "help"),
            reply_markup=back_menu(chat_id)
        )
        return

    if mode == "qr":
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "qr.png"
            qrcode.make(text).save(path)
            with path.open("rb") as f:
                bot.send_photo(
                    chat_id, f, caption=tr(chat_id, "done"),
                    reply_markup=back_menu(chat_id)
                )
        user_modes.pop(str(chat_id), None)
        ask_rating(chat_id)
        return

    if mode == "translate":
        try:
            dest = "fa" if language(chat_id) == "fa" else "en"
            result = Translator().translate(text, dest=dest)
            bot.send_message(
                chat_id, tr(chat_id, "translated", result=result.text),
                reply_markup=back_menu(chat_id)
            )
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
                    bot.send_document(
                        chat_id, f, caption=tr(chat_id, "done"),
                        reply_markup=back_menu(chat_id)
                    )
            ask_rating(chat_id)
        except Exception:
            logger.exception("Text to PDF error")
            bot.send_message(chat_id, tr(chat_id, "error"))
        user_modes.pop(str(chat_id), None)
        return

    user_text[str(chat_id)] = text
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.row(types.InlineKeyboardButton(
        tr(chat_id, "opt_qr"), callback_data="do_qr"))
    markup.row(types.InlineKeyboardButton(
        tr(chat_id, "opt_translate"), callback_data="do_translate"))
    markup.row(types.InlineKeyboardButton(
        tr(chat_id, "opt_pdf"), callback_data="do_pdf"))
    markup.row(types.InlineKeyboardButton(
        tr(chat_id, "back"), callback_data="home"))
    bot.send_message(
        chat_id, tr(chat_id, "text_options"), reply_markup=markup
    )

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
    
    if not check_lock(chat_id, message.from_user.id):
        return

    mode = user_modes.get(str(chat_id))

    is_photo = message.content_type == "photo"
    is_pdf = (
        message.content_type == "document"
        and (
            (message.document.mime_type or "") == "application/pdf"
            or (message.document.file_name or "").lower().endswith(".pdf")
        )
    )

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
                    bot.send_document(
                        chat_id, f, caption=tr(chat_id, "done"),
                        reply_markup=back_menu(chat_id)
                    )
                user_modes.pop(str(chat_id), None)
                ask_rating(chat_id)
                return

            if is_photo and mode == "compress":
                raw = get_file_bytes(message.photo[-1].file_id)
                source = td / "input.jpg"
                output = td / "compressed.jpg"
                source.write_bytes(raw)
                with Image.open(source) as img:
                    img = ImageOps.exif_transpose(img).convert("RGB")
                    img.thumbnail((1600, 1600))
                    img.save(output, "JPEG", quality=68, optimize=True)
                with output.open("rb") as f:
                    bot.send_document(
                        chat_id, f, caption=tr(chat_id, "done"),
                        reply_markup=back_menu(chat_id)
                    )
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
                    extracted = "\n\n".join(
                        page.extract_text() or "" for page in reader.pages
                    )
                if not extracted.strip():
                    bot.send_message(
                        chat_id, tr(chat_id, "no_pdf_text"),
                        reply_markup=back_menu(chat_id)
                    )
                else:
                    output.write_text(extracted, encoding="utf-8")
                    with output.open("rb") as f:
                        bot.send_document(
                            chat_id, f, caption=tr(chat_id, "done"),
                            reply_markup=back_menu(chat_id)
                        )
                user_modes.pop(str(chat_id), None)
                ask_rating(chat_id)
                return

        bot.send_message(
            chat_id, tr(chat_id, "bad_file"),
            reply_markup=back_menu(chat_id)
        )

    except ValueError:
        bot.send_message(chat_id, tr(chat_id, "too_large"))
    except Exception:
        logger.exception("Media processing error")
        bot.send_message(
            chat_id, tr(chat_id, "error"),
            reply_markup=back_menu(chat_id)
        )

# =============== START BOT ===============
if __name__ == "__main__":
    logger.info("%s is starting...", BOT_NAME)
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
