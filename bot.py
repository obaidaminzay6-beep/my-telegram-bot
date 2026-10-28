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
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import jdatetime
import requests

# =============== CONFIG ===============
TOKEN = os.getenv("TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("TOKEN is missing.")

BOT_NAME = "NEXORA BOT v10.0"
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/DarkVenom404")
ADMIN_IDS = {7210433916}

DB_FILE = Path("user_data.json")
MAINTENANCE_FILE = Path("maintenance.json")
MAX_FILE_MB = 20

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("nexora")
bot = telebot.TeleBot(TOKEN, threaded=True)

user_modes = {}
admin_broadcast_mode = set()

# =============== TEXTS ===============
TEXT = {
    "fa": {
        "choose_lang": "🌍 لطفاً زبان خود را انتخاب کنید:",
        "welcome": "✨ سلام {name} عزیز!\n\nبه NEXORA BOT خوش آمدی. 👋\n\n⚡️ ابزارهای من:\n📄 مدیریت PDF\n🤖 هوش مصنوعی و ترجمه\n⏰ یادآور و تقویم\n\n👇 یکی از گزینه‌ها را انتخاب کن:",
        "language": "🌍 تغییر زبان",
        "support": "💬 پشتیبانی",
        "img_pdf": "🖼️ عکس به PDF",
        "text_pdf": "📝 متن به PDF",
        "pdf_text": "📄 PDF به متن",
        "ai_assistant": "🤖 دستیار هوش مصنوعی",
        "translate": "🌐 ترجمه متن",
        "date": "📅 تاریخ و ساعت",
        "about": "ℹ️ درباره ربات",
        "prompt_img_pdf": "🖼️ عکس خود را بفرست تا به PDF تبدیل کنم.",
        "prompt_text_pdf": "📝 متن خود را بفرست تا به PDF تبدیل کنم.",
        "prompt_pdf_text": "📄 فایل PDF خود را بفرست.",
        "prompt_translate": "🌐 متن خود را برای ترجمه بفرست.",
        "prompt_ai": "🤖 سوال خود را بنویسید. (برای خروج روی بازگشت بزنید)",
        "done": "✅ انجام شد.",
        "error": "❌ خطا! دوباره تلاش کنید.",
        "back": "🔙 بازگشت به منو",
        "about_text": "✨ NEXORA BOT v10.0\nتوسعه‌دهنده: @DarkVenom404",
        "admin_stats": "📊 آمار:\n\n👥 کاربران: {users}\n✅ تایید شده: {approved}\n⏳ در انتظار: {pending}",
        "broadcast_prompt": "📢 متن پیام همگانی را بنویسید:",
        "broadcast_done": "✅ به {count} کاربر ارسال شد.",
        "lock_done": "🔒 ربات قفل شد.",
        "unlock_done": "🔓 ربات باز شد و به کاربران اطلاع داده شد.",
        "unlock_broadcast": "🔔 ربات دوباره فعال شد! می‌توانید از ابزارهای آن استفاده کنید.",
        "wait_approval": "⏳ در انتظار تایید مدیر.",
        "user_approved": "✅ حساب شما تایید شد!",
        "user_rejected": "❌ دسترسی شما رد شد.",
        "admin_new_user": "👤 کاربر جدید:\n\nنام: {name}\nآیدی: {id}\n\nاجازه می‌دهید؟",
        "approved_btn": "✅ تایید",
        "rejected_btn": "❌ رد",
        "admin_panel": "👑 پنل مدیریت:",
        "btn_broadcast": "📢 ارسال همگانی",
        "btn_stats": "📊 آمار",
        "btn_lock": "🔒 قفل",
        "btn_unlock": "🔓 باز کردن",
        "trans_ans": "🌐 ترجمه:\n\n{ans}",
        "ai_ans": "🤖 پاسخ:\n\n{ans}",
        "maintenance_msg": "🛠️ ربات موقتاً در حال تعمیر است. لطفاً بعداً تلاش کنید."
    },
    "en": {
        "choose_lang": "🌍 Please choose your language:",
        "welcome": "✨ Hello {name}!\n\nWelcome to NEXORA BOT. 👋\n\n⚡️ My Tools:\n📄 PDF Management\n🤖 AI & Translation\n⏰ Reminders & Calendar\n\n👇 Choose an option:",
        "language": "🌍 Change Language",
        "support": "💬 Support",
        "img_pdf": "🖼️ Image to PDF",
        "text_pdf": "📝 Text to PDF",
        "pdf_text": "📄 PDF to Text",
        "ai_assistant": "🤖 AI Assistant",
        "translate": "🌐 Translate Text",
        "date": "📅 Date & Time",
        "about": "ℹ️ About",
        "prompt_img_pdf": "🖼️ Send an image to convert to PDF.",
        "prompt_text_pdf": "📝 Send text to convert to PDF.",
        "prompt_pdf_text": "📄 Send a PDF file.",
        "prompt_translate": "🌐 Send text to translate.",
        "prompt_ai": "🤖 Write your question. (Click Back to exit)",
        "done": "✅ Done.",
        "error": "❌ Error! Try again.",
        "back": "🔙 Back to menu",
        "about_text": "✨ NEXORA BOT v10.0\nDeveloper: @DarkVenom404",
        "admin_stats": "📊 Stats:\n\n👥 Users: {users}\n✅ Approved: {approved}\n⏳ Pending: {pending}",
        "broadcast_prompt": "📢 Enter broadcast message:",
        "broadcast_done": "✅ Sent to {count} users.",
        "lock_done": "🔒 Bot locked.",
        "unlock_done": "🔓 Bot unlocked and users notified.",
        "unlock_broadcast": "🔔 The bot is active again! You can use its tools now.",
        "wait_approval": "⏳ Waiting for admin approval.",
        "user_approved": "✅ Your account approved!",
        "user_rejected": "❌ Access denied.",
        "admin_new_user": "👤 New user:\n\nName: {name}\nID: {id}\n\nAllow?",
        "approved_btn": "✅ Approve",
        "rejected_btn": "❌ Reject",
        "admin_panel": "👑 Admin Panel:",
        "btn_broadcast": "📢 Broadcast",
        "btn_stats": "📊 Stats",
        "btn_lock": "🔒 Lock",
        "btn_unlock": "🔓 Unlock",
        "trans_ans": "🌐 Translation:\n\n{ans}",
        "ai_ans": "🤖 Answer:\n\n{ans}",
        "maintenance_msg": "🛠️ Bot is under maintenance. Please try again later."
    }
}

def tr(cid, key, **kw):
    lang = get_lang(cid)
    return TEXT[lang].get(key, TEXT["en"][key]).format(**kw)

# =============== DB ===============
def load_db():
    if DB_FILE.exists():
        try:
            with DB_FILE.open("r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}

def save_db(d):
    with DB_FILE.open("w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=2)

def get_user(cid):
    db = load_db()
    if str(cid) not in db:
        db[str(cid)] = {"lang": "fa", "approved": cid in ADMIN_IDS, "joined": str(datetime.date.today())}
        save_db(db)
    return db[str(cid)]

def get_lang(cid): return get_user(cid).get("lang", "fa")
def is_approved(cid): return cid in ADMIN_IDS or get_user(cid).get("approved", False)

def check_lock(cid, uid):
    if uid in ADMIN_IDS: return True
    if MAINTENANCE_FILE.exists():
        try:
            with MAINTENANCE_FILE.open("r") as f:
                if json.load(f).get("locked"): 
                    bot.send_message(cid, tr(cid, "maintenance_msg")); return False
        except: pass
    return True

# =============== MENUS ===============
def lang_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.row(types.InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
          types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
    return m

def main_menu(cid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.row(types.InlineKeyboardButton(tr(cid,"img_pdf"), callback_data="mode_img"),
          types.InlineKeyboardButton(tr(cid,"text_pdf"), callback_data="mode_text"))
    m.row(types.InlineKeyboardButton(tr(cid,"pdf_text"), callback_data="mode_pdf"),
          types.InlineKeyboardButton(tr(cid,"translate"), callback_data="mode_trans"))
    m.row(types.InlineKeyboardButton(tr(cid,"ai_assistant"), callback_data="mode_ai"),
          types.InlineKeyboardButton(tr(cid,"date"), callback_data="date"))
    m.row(types.InlineKeyboardButton(tr(cid,"language"), callback_data="lang"),
          types.InlineKeyboardButton(tr(cid,"support"), url=SUPPORT_LINK))
    m.row(types.InlineKeyboardButton(tr(cid,"about"), callback_data="about"))
    return m

def back_menu(cid):
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(tr(cid,"back"), callback_data="home"))

def show_home(cid, name=""):
    user_modes.pop(str(cid), None)
    bot.send_message(cid, tr(cid,"welcome", name=name or "User"), reply_markup=main_menu(cid))

# =============== PDF SUPPORT ===============
def make_pdf(text, out):
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if os.path.isfile(font_path):
            pdfmetrics.registerFont(TTFont('DejaVu', font_path))
            font_name = 'DejaVu'
        else:
            font_name = 'Helvetica'

        c = canvas.Canvas(str(out))
        c.setFont(font_name, 12)
        
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            text = get_display(arabic_reshaper.reshape(text))
        except: pass
        
        y = 800
        for line in text.splitlines() or [""]:
            c.drawString(50, y, line)
            y -= 20
            if y < 50:
                c.showPage()
                c.setFont(font_name, 12)
                y = 800
        c.save()
    except Exception as e:
        logger.error(f"PDF Error: {e}")
        raise e

# =============== COMMANDS ===============
@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    is_new = str(uid) not in load_db()
    get_user(uid)
    if not check_lock(m.chat.id, uid): return
    
    if is_new and uid not in ADMIN_IDS:
        bot.send_message(m.chat.id, tr(m.chat.id,"choose_lang"), reply_markup=lang_menu())
        for admin_id in ADMIN_IDS:
            m2 = types.InlineKeyboardMarkup()
            m2.add(types.InlineKeyboardButton(tr(admin_id,"approved_btn"), callback_data=f"appr_{uid}"),
                   types.InlineKeyboardButton(tr(admin_id,"rejected_btn"), callback_data=f"rej_{uid}"))
            try: bot.send_message(admin_id, tr(admin_id,"admin_new_user", name=m.from_user.first_name, id=uid), reply_markup=m2)
            except: pass
        return
    
    if not is_approved(uid):
        bot.send_message(m.chat.id, tr(m.chat.id,"wait_approval")); return
    
    show_home(m.chat.id, m.from_user.first_name)

@bot.message_handler(commands=['panel'])
def cmd_panel(m):
    if m.from_user.id not in ADMIN_IDS: return
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(types.InlineKeyboardButton(tr(m.chat.id,"btn_broadcast"), callback_data="adm_bcast"),
           types.InlineKeyboardButton(tr(m.chat.id,"btn_stats"), callback_data="adm_stats"))
    kb.row(types.InlineKeyboardButton(tr(m.chat.id,"btn_lock"), callback_data="adm_lock"),
           types.InlineKeyboardButton(tr(m.chat.id,"btn_unlock"), callback_data="adm_unlock"))
    kb.row(types.InlineKeyboardButton(tr(m.chat.id,"back"), callback_data="home"))
    bot.send_message(m.chat.id, tr(m.chat.id,"admin_panel"), reply_markup=kb)

# =============== CALLBACKS ===============
@bot.callback_query_handler(func=lambda c: True)
def on_cb(c):
    cid = c.message.chat.id
    uid = c.from_user.id
    data = c.data
    bot.answer_callback_query(c.id)

    if data.startswith("appr_") and uid in ADMIN_IDS:
        t_uid = data.split("_")[1]
        db = load_db()
        if t_uid in db:
            db[t_uid]["approved"] = True; save_db(db)
            try: bot.send_message(t_uid, tr(t_uid,"user_approved"))
            except: pass
            bot.edit_message_text("✅ Approved.", cid, c.message.message_id)
        return
    if data.startswith("rej_") and uid in ADMIN_IDS:
        t_uid = data.split("_")[1]
        db = load_db()
        if t_uid in db:
            db[t_uid]["approved"] = False; save_db(db)
            try: bot.send_message(t_uid, tr(t_uid,"user_rejected"))
            except: pass
            bot.edit_message_text("❌ Rejected.", cid, c.message.message_id)
        return

    if data.startswith("lang_"):
        lang = data.split("_")[1]
        db = load_db(); db[str(cid)]["lang"] = lang; save_db(db)
        bot.delete_message(cid, c.message.message_id)
        if is_approved(uid): show_home(cid, c.from_user.first_name)
        else: bot.send_message(cid, tr(cid,"wait_approval"))
        return

    if not check_lock(cid, uid): return
    if not is_approved(uid):
        bot.send_message(cid, tr(cid,"wait_approval")); return

    if data == "home":
        show_home(cid, c.from_user.first_name); return
    if data == "lang":
        bot.send_message(cid, tr(cid,"choose_lang"), reply_markup=lang_menu()); return
    if data == "about":
        bot.send_message(cid, tr(cid,"about_text"), reply_markup=back_menu(cid)); return
    if data == "date":
        # تاریخ جدید با ساعت 12 ساعته و روز هفته
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=4, minutes=30)))
        sh = jdatetime.datetime.fromgregorian(datetime=now.replace(tzinfo=None))
        
        lang = get_lang(cid)
        days_fa = {"Saturday": "شنبه", "Sunday": "یکشنبه", "Monday": "دوشنبه", "Tuesday": "سه‌شنبه", "Wednesday": "چهارشنبه", "Thursday": "پنجشنبه", "Friday": "جمعه"}
        
        day_name = days_fa.get(sh.strftime('%A'), sh.strftime('%A')) if lang == "fa" else sh.strftime('%A')
        
        # ساعت 12 ساعته
        time_12 = now.strftime('%I:%M:%S %p')
        
        if lang == "fa":
            txt = f"📅 تاریخ امروز:\n\n🔹 شمسی: {sh.strftime('%Y/%m/%d')}\n🔸 میلادی: {now.strftime('%Y-%m-%d')}\n⏰ ساعت: {time_12}\n📆 روز هفته: {day_name}"
        else:
            txt = f"📅 Today's Date:\n\n🔹 Shamsi: {sh.strftime('%Y/%m/%d')}\n🔸 Gregorian: {now.strftime('%Y-%m-%d')}\n⏰ Time: {time_12}\n📆 Day: {day_name}"
        
        bot.send_message(cid, txt, reply_markup=back_menu(cid))
        return

    if data == "adm_bcast" and uid in ADMIN_IDS:
        admin_broadcast_mode.add(uid)
        bot.send_message(cid, tr(cid,"broadcast_prompt")); return
    if data == "adm_stats" and uid in ADMIN_IDS:
        db = load_db()
        appr = sum(1 for u in db.values() if u.get("approved"))
        bot.send_message(cid, tr(cid,"admin_stats", users=len(db), approved=appr, pending=len(db)-appr)); return
    if data == "adm_lock" and uid in ADMIN_IDS:
        with MAINTENANCE_FILE.open("w") as f: json.dump({"locked":True}, f)
        bot.send_message(cid, tr(cid,"lock_done")); return
    if data == "adm_unlock" and uid in ADMIN_IDS:
        with MAINTENANCE_FILE.open("w") as f: json.dump({"locked":False}, f)
        bot.send_message(cid, tr(cid,"unlock_done"))
        
        # ارسال پیام خودکار به کاربران بعد از باز شدن ربات
        db = load_db()
        for u in db.keys():
            try: 
                bot.send_message(u, tr(u, "unlock_broadcast"))
                time.sleep(0.05)
            except: pass
        return

    modes_map = {
        "mode_img": ("prompt_img_pdf", "img"),
        "mode_text": ("prompt_text_pdf", "text"),
        "mode_pdf": ("prompt_pdf_text", "pdf"),
        "mode_trans": ("prompt_translate", "trans"),
        "mode_ai": ("prompt_ai", "ai")
    }
    if data in modes_map:
        user_modes[str(cid)] = modes_map[data][1]
        bot.send_message(cid, tr(cid, modes_map[data][0]), reply_markup=back_menu(cid))
        return

# =============== MESSAGE HANDLERS ===============
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def on_text(m):
    cid = m.chat.id
    uid = m.from_user.id
    
    if uid in admin_broadcast_mode:
        admin_broadcast_mode.discard(uid)
        db = load_db()
        cnt = 0
        for u in db.keys():
            try: bot.send_message(u, m.text); cnt += 1; time.sleep(0.05)
            except: pass
        bot.reply_to(m, tr(cid,"broadcast_done", count=cnt)); return

    if not check_lock(cid, uid): return
    if not is_approved(uid):
        bot.send_message(cid, tr(cid,"wait_approval")); return

    mode = user_modes.get(str(cid))
    if not mode:
        show_home(cid, m.from_user.first_name)
        return

    if mode == "ai":
        try:
            r = requests.post("https://text.pollinations.ai/", json={"messages": [{"role": "user", "content": m.text}]}, timeout=30)
            ans = r.text
            bot.send_message(cid, tr(cid,"ai_ans", ans=ans), reply_markup=back_menu(cid))
        except:
            bot.send_message(cid, tr(cid,"error"), reply_markup=back_menu(cid))
        return

    if mode == "trans":
        try:
            dest = "fa" if get_lang(cid) == "fa" else "en"
            url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(m.text)}&langpair=en|{dest}" if dest=="fa" else f"https://api.mymemory.translated.net/get?q={requests.utils.quote(m.text)}&langpair=fa|en"
            r = requests.get(url, timeout=15).json()
            ans = r["responseData"]["translatedText"]
            bot.send_message(cid, tr(cid,"trans_ans", ans=ans), reply_markup=back_menu(cid))
        except:
            bot.send_message(cid, tr(cid,"error"), reply_markup=back_menu(cid))
        return

    if mode == "text":
        try:
            with tempfile.TemporaryDirectory() as td:
                p = Path(td) / "out.pdf"
                make_pdf(m.text, p)
                with p.open("rb") as f:
                    bot.send_document(cid, f, caption=tr(cid,"done"), reply_markup=back_menu(cid))
        except Exception as e:
            logger.error(f"PDF Error: {e}")
            bot.send_message(cid, tr(cid,"error"), reply_markup=back_menu(cid))
        user_modes.pop(str(cid), None)
        return

@bot.message_handler(content_types=['photo', 'document'])
def on_media(m):
    cid = m.chat.id
    uid = m.from_user.id
    if not check_lock(cid, uid): return
    if not is_approved(uid):
        bot.send_message(cid, tr(cid,"wait_approval")); return

    mode = user_modes.get(str(cid))
    
    if mode == "img" and m.content_type == 'photo':
        try:
            info = bot.get_file(m.photo[-1].file_id)
            data = bot.download_file(info.file_path)
            with tempfile.TemporaryDirectory() as td:
                src = Path(td) / "in.jpg"; out = Path(td) / "out.pdf"
                src.write_bytes(data)
                with Image.open(src) as img: img.convert("RGB").save(out, "PDF")
                with out.open("rb") as f: bot.send_document(cid, f, caption=tr(cid,"done"), reply_markup=back_menu(cid))
        except:
            bot.send_message(cid, tr(cid,"error"), reply_markup=back_menu(cid))
        user_modes.pop(str(cid), None)
        return

    if mode == "pdf" and m.content_type == 'document':
        try:
            info = bot.get_file(m.document.file_id)
            data = bot.download_file(info.file_path)
            with tempfile.TemporaryDirectory() as td:
                src = Path(td) / "in.pdf"; out = Path(td) / "out.txt"
                src.write_bytes(data)
                with src.open("rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    txt = "\n".join(p.extract_text() or "" for p in reader.pages)
                out.write_text(txt, encoding="utf-8")
                with out.open("rb") as f: bot.send_document(cid, f, caption=tr(cid,"done"), reply_markup=back_menu(cid))
        except:
            bot.send_message(cid, tr(cid,"error"), reply_markup=back_menu(cid))
        user_modes.pop(str(cid), None)
        return

# =============== START BOT ===============
if __name__ == "__main__":
    logger.info("Starting...")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
