


import telebot
from telebot import types
import qrcode
from fpdf import FPDF
import os
from PIL import Image
import PyPDF2
from googletrans import Translator
import datetime
import jdatetime
import json
import threading
import time
import shutil

# ⚠️ توکن به صورت خودکار از تنظیمات امن گیت‌هاب خوانده می‌شود
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- تنظیمات شخصی‌سازی ---
LOGO_URL = "https://i.imgur.com/8QO9R3n.jpeg" 
SUPPORT_LINK = "https://t.me/DarkVenom404" 

# --- فایل ذخیره‌سازی اطلاعات (برای یادآورها و تاریخ عضویت) ---
DB_FILE = "user_data.json"
reminders_file = "reminders.json"

def load_data(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return {}

def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(data, f)

# --- سیستم یادآور (Reminder) در پس‌زمینه ---
def reminder_worker():
    while True:
        reminders = load_data(reminders_file)
        now = time.time()
        to_remove = []
        
        for chat_id, user_reminders in reminders.items():
            for rem in user_reminders:
                if now >= rem['time']:
                    try:
                        bot.send_message(chat_id, f"⏰ **یادآوری:**\n{rem['text']}")
                        to_remove.append((chat_id, rem['text']))
                    except:
                        pass
        
        if to_remove:
            for chat_id, text in to_remove:
                reminders[chat_id] = [r for r in reminders[chat_id] if r['text'] != text]
            save_data(reminders_file, reminders)
            
        time.sleep(5)

threading.Thread(target=reminder_worker, daemon=True).start()

# --- دیکشنری زبان‌ها ---
LANGUAGES = {
    'fa': {
        'welcome': "سلام {name} عزیز! 👋\n\n🌟 به ربات جادویی ابزارها خوش آمدید.\n\nمن یک جعبه‌ابزار کامل هستم تا کارهای روزمره شما را آسان کنم. از منوی زیر انتخاب کنید:\n\n✨ ابزارهای من:",
        'menu_rows': [
            [('🖼️ عکس به PDF', 'img_to_pdf'), ('📝 متن به PDF', 'txt_to_pdf')],
            [('📱 ساخت QR', 'qr'), ('🗜️ فشرده‌سازی عکس', 'compress_img')],
            [('📄 PDF به متن', 'pdf_to_txt'), ('🌐 ترجمه متن', 'translate')],
            [('📅 تاریخ و ساعت', 'datetime_info'), ('ℹ️ درباره ربات', 'about_bot')],
        ],
        'change_lang_btn': "🌍 تغییر زبان",
        'back_btn': "🔙 بازگشت به منو",
        
        'img_to_pdf': "🖼️ لطفاً عکس خود را بفرستید تا آن را به یک فایل PDF زیبا تبدیل کنم.",
        'txt_to_pdf': "📝 لطفاً متن خود را بفرستید.\n\n💡 **مثال:** `Hello World` یا `سلام دنیا`",
        'qr': "🔗 لطفاً متن یا لینک خود را برای ساخت QR ارسال کنید.\n\n💡 **مثال:** `https://google.com`",
        'compress_img': "🗜️ لطفاً عکس خود را بفرستید تا آن را فشرده کنم.",
        'pdf_to_txt': "📄 لطفاً فایل PDF خود را بفرستید تا متن آن را به صورت یک فایل متنی (.txt) برایتان بفرستم.",
        'translate': "🌐 لطفاً متن خود را بفرستید تا آن را ترجمه کنم.\n\n💡 **مثال:** `Hello World`",
        
        'processing': "⏳ در حال پردازش... لطفاً صبر کنید.",
        
        'err_processing': "❌ خطا در پردازش: {error}",
        'err_pdf': "❌ خطا در پردازش PDF: {error}",
        'err_pdf_only': "❌ لطفاً فقط فایل PDF بفرستید.",
        'err_text': "❌ خطا در پردازش متن.",
        'translated': "🌐 ترجمه شما:\n\n{text}",
        'qr_done': "📱 QR کد شما با موفقیت ساخته شد.",
        'pdf_done': "✅ فایل PDF شما آماده دانلود است.",
        'lang_select': "🌍 لطفاً زبان خود را انتخاب کنید:",
        'main_menu_btn': "🏠 Start",
        'help_btn': "ℹ️ راهنما",
        'help_text': "📖 راهنمای ربات:\n\n- برای استفاده از هر ابزار، روی دکمه آن کلیک کنید.\n- از دکمه Start برای بازگشت به منو استفاده کنید.\n- **دستور یادآور:** /remind",
        
        'datetime_title': "📅 تاریخ و ساعت دقیق:",
        'about_title': "ℹ️ درباره ربات:\n\nاین ربات یک جعبه‌ابزار کامل است.\n\n✨ نسخه: 3.0\n🚀 پلتفرم: GitHub Actions",
        'profile_btn': "👤 پروفایل من",
        'support_btn': "💬 پشتیبانی",
        
        'profile_text': "👤 **اطلاعات شما:**\n\n📛 نام: {name}\n🆔 آیدی عددی: `{id}`\n🌐 زبان: {lang}\n📅 تاریخ عضویت: {date}",
        
        'remind_prompt': "⏰ **سیستم یادآور:**\n\nلطفاً زمان و متن یادآوری را به این شکل بفرستید:\n`/remind 10m به مادرم زنگ بزنم`\n\n**واحدهای زمان:**\n`s` (ثانیه)، `m` (دقیقه)، `h` (ساعت)\n\n**مثال:** `/remind 2h جلسه کاری`",
        'remind_set': "✅ یادآوری برای {time} دیگر تنظیم شد.",
        'remind_invalid': "❌ فرمت اشتباه است. لطفاً از الگوی `/remind 10m متن` استفاده کنید.",
        
        'text_options': "📄 شما یک متن فرستادید. لطفاً انتخاب کنید که چه کاری روی آن انجام دهم:",
        'opt_qr': "📱 ساخت QR",
        'opt_translate': "🌐 ترجمه",
        'opt_pdf': "📝 تبدیل به PDF"
    },
    'en': {
        'welcome': "Hello {name}! 👋\n\n🌟 Welcome to the Magic Tools Bot.\n\nI am a complete toolbox to make your daily tasks easier. Choose from the menu below:\n\n✨ My Tools:",
        'menu_rows': [
            [('🖼️ Image to PDF', 'img_to_pdf'), ('📝 Text to PDF', 'txt_to_pdf')],
            [('📱 Create QR', 'qr'), ('🗜️ Compress Image', 'compress_img')],
            [('📄 PDF to Text', 'pdf_to_txt'), ('🌐 Translate Text', 'translate')],
            [('📅 Date & Time', 'datetime_info'), ('ℹ️ About Bot', 'about_bot')],
        ],
        'change_lang_btn': "🌍 Change Language",
        'back_btn': "🔙 Back to Menu",
        
        'img_to_pdf': "🖼️ Please send your image to convert it to a beautiful PDF.",
        'txt_to_pdf': "📝 Please send your text.\n\n💡 **Example:** `Hello World`",
        'qr': "🔗 Please send text or a link to create a QR code.\n\n💡 **Example:** `https://google.com`",
        'compress_img': "🗜️ Please send your image to compress it.",
        'pdf_to_txt': "📄 Please send your PDF file to extract its text as a .txt file.",
        'translate': "🌐 Please send your text to translate it.\n\n💡 **Example:** `Hello World`",
        
        'processing': "⏳ Processing... Please wait.",
        
        'err_processing': "❌ Error processing: {error}",
        'err_pdf': "❌ Error processing PDF: {error}",
        'err_pdf_only': "❌ Please send only PDF files.",
        'err_text': "❌ Error processing text.",
        'translated': "🌐 Your Translation:\n\n{text}",
        'qr_done': "📱 Your QR code was created successfully.",
        'pdf_done': "✅ Your PDF file is ready for download.",
        'lang_select': "🌍 Please select your language:",
        'main_menu_btn': "🏠 Start",
        'help_btn': "ℹ️ Help",
        'help_text': "📖 Bot Help:\n\n- Click on any tool's button to use it.\n- Use the Start button to return to the menu.\n- **Reminder Command:** /remind",
        
        'datetime_title': "📅 Exact Date & Time:",
        'about_title': "ℹ️ About Bot:\n\nThis bot is a complete toolbox.\n\n✨ Version: 3.0\n🚀 Platform: GitHub Actions",
        'profile_btn': "👤 My Profile",
        'support_btn': "💬 Support",
        
        'profile_text': "👤 **Your Info:**\n\n📛 Name: {name}\n🆔 ID: `{id}`\n🌐 Language: {lang}\n📅 Joined: {date}",
        
        'remind_prompt': "⏰ **Reminder System:**\n\nPlease send the time and text like this:\n`/remind 10m Call mom`\n\n**Time units:**\n`s` (seconds), `m` (minutes), `h` (hours)\n\n**Example:** `/remind 2h Work meeting`",
        'remind_set': "✅ Reminder set for {time} later.",
        'remind_invalid': "❌ Invalid format. Use `/remind 10m Text`.",
        
        'text_options': "📄 You sent a text. Please choose what to do with it:",
        'opt_qr': "📱 Create QR",
        'opt_translate': "🌐 Translate",
        'opt_pdf': "📝 Convert to PDF"
    }
}

user_lang = {}
user_text = {}

def get_lang(chat_id): return user_lang.get(chat_id, 'fa')
def get_text(chat_id, key, **kwargs):
    lang = get_lang(chat_id)
    text = LANGUAGES[lang].get(key, LANGUAGES['fa'].get(key, key))
    return text.format(**kwargs)

# --- منوی اصلی ---
def main_menu(chat_id):
    lang = get_lang(chat_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    for row in LANGUAGES[lang]['menu_rows']:
        buttons = [types.InlineKeyboardButton(text, callback_data=data) for text, data in row]
        markup.add(*buttons)
    markup.add(types.InlineKeyboardButton(LANGUAGES[lang]['change_lang_btn'], callback_data='change_lang'))
    markup.add(types.InlineKeyboardButton(LANGUAGES[lang]['support_btn'], url=SUPPORT_LINK))
    return markup

def back_markup(chat_id):
    lang = get_lang(chat_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(LANGUAGES[lang]['back_btn'], callback_data='main_menu'))
    return markup

def text_options_markup(chat_id):
    lang = get_lang(chat_id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(LANGUAGES[lang]['opt_qr'], callback_data='do_qr'),
        types.InlineKeyboardButton(LANGUAGES[lang]['opt_translate'], callback_data='do_translate'),
        types.InlineKeyboardButton(LANGUAGES[lang]['opt_pdf'], callback_data='do_pdf'),
        types.InlineKeyboardButton(LANGUAGES[lang]['back_btn'], callback_data='main_menu')
    )
    return markup

def persistent_keyboard(chat_id):
    lang = get_lang(chat_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton(LANGUAGES[lang]['main_menu_btn']), types.KeyboardButton(LANGUAGES[lang]['help_btn']))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    db = load_data(DB_FILE)
    if str(chat_id) not in db:
        db[str(chat_id)] = {'joined': datetime.datetime.now().strftime("%Y-%m-%d")}
        save_data(DB_FILE, db)
        
    caption = get_text(chat_id, 'welcome', name=message.from_user.first_name)
    try:
        bot.send_photo(chat_id, photo=LOGO_URL, caption=caption, reply_markup=main_menu(chat_id))
    except:
        bot.send_message(chat_id, caption, reply_markup=main_menu(chat_id))
    bot.send_message(chat_id, "👇", reply_markup=persistent_keyboard(chat_id))

# --- مدیریت دکمه‌های کیبورد (با شرط مقاوم‌تر) ---
@bot.message_handler(func=lambda message: message.text and ("Start" in message.text or "شروع" in message.text))
def back_to_menu(message):
    chat_id = message.chat.id
    text = get_text(chat_id, 'welcome', name=message.from_user.first_name)
    bot.send_message(chat_id, text, reply_markup=main_menu(chat_id))

@bot.message_handler(func=lambda message: message.text and ("راهنما" in message.text or "Help" in message.text))
def show_help(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, get_text(chat_id, 'help_text'), reply_markup=back_markup(chat_id))

# --- دستور یادآور ---
@bot.message_handler(commands=['remind'])
def set_reminder(message):
    chat_id = message.chat.id
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, get_text(chat_id, 'remind_prompt'))
        return
    
    time_str = parts[1]
    text = parts[2]
    
    seconds = 0
    try:
        if time_str.endswith('s'): seconds = int(time_str[:-1])
        elif time_str.endswith('m'): seconds = int(time_str[:-1]) * 60
        elif time_str.endswith('h'): seconds = int(time_str[:-1]) * 3600
        else: raise ValueError
    except:
        bot.reply_to(message, get_text(chat_id, 'remind_invalid'))
        return

    reminders = load_data(reminders_file)
    if str(chat_id) not in reminders:
        reminders[str(chat_id)] = []
    
    reminders[str(chat_id)].append({
        'text': text,
        'time': time.time() + seconds
    })
    save_data(reminders_file, reminders)
    bot.reply_to(message, get_text(chat_id, 'remind_set', time=time_str))

# --- مدیریت دکمه‌های شیشه‌ای ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if call.data == 'main_menu':
        text = get_text(chat_id, 'welcome', name=call.from_user.first_name)
        try:
            bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=call.message.message_id, reply_markup=main_menu(chat_id))
        except:
            bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=main_menu(chat_id))
        return

    if call.data == 'about_bot':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(LANGUAGES[get_lang(chat_id)]['profile_btn'], callback_data='profile'))
        markup.add(types.InlineKeyboardButton(LANGUAGES[get_lang(chat_id)]['back_btn'], callback_data='main_menu'))
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, get_text(chat_id, 'about_title'), reply_markup=markup)
        return

    if call.data == 'profile':
        db = load_data(DB_FILE)
        joined = db.get(str(chat_id), {}).get('joined', 'Unknown')
        text = get_text(chat_id, 'profile_text', 
                        name=call.from_user.first_name, 
                        id=chat_id, 
                        lang=get_lang(chat_id), 
                        date=joined)
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, text, reply_markup=back_markup(chat_id), parse_mode='Markdown')
        return

    if call.data == 'change_lang':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🇮🇷 فارسی", callback_data='set_lang_fa'))
        markup.add(types.InlineKeyboardButton("🇬🇧 English", callback_data='set_lang_en'))
        bot.edit_message_text(get_text(chat_id, 'lang_select'), chat_id, call.message.message_id, reply_markup=markup)
        return
    
    if call.data.startswith('set_lang_'):
        lang = call.data.split('_')[-1]
        user_lang[chat_id] = lang
        text = get_text(chat_id, 'welcome', name=call.from_user.first_name)
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=main_menu(chat_id))
        bot.send_message(chat_id, "👇", reply_markup=persistent_keyboard(chat_id))
        return
    
    if call.data == 'datetime_info':
        bot.answer_callback_query(call.id)
        now = datetime.datetime.now()
        shamsi = jdatetime.datetime.fromgregorian(datetime=now)
        text = (
            f"{get_text(chat_id, 'datetime_title')}\n\n"
            f"🗓️ تاریخ شمسی: {shamsi.strftime('%Y/%m/%d')}\n"
            f"🗓️ تاریخ میلادی: {now.strftime('%Y-%m-%d')}\n"
            f"⏰ ساعت دقیق: {now.strftime('%H:%M:%S')}\n"
            f"📅 روز هفته: {shamsi.strftime('%A')}"
        )
        bot.send_message(chat_id, text, reply_markup=back_markup(chat_id))
        return
    
    prompts = {'img_to_pdf':'img_to_pdf', 'txt_to_pdf':'txt_to_pdf', 'qr':'qr', 'compress_img':'compress_img', 'pdf_to_txt':'pdf_to_txt', 'translate':'translate'}
    if call.data in prompts:
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, get_text(chat_id, prompts[call.data]), reply_markup=back_markup(chat_id), parse_mode='Markdown')
        return
        
    if call.data in ['do_qr', 'do_translate', 'do_pdf']:
        bot.answer_callback_query(call.id)
        text = user_text.get(chat_id)
        if not text:
            bot.send_message(chat_id, "❌ خطا: متن پیدا نشد.", reply_markup=main_menu(chat_id))
            return
        if call.data == 'do_qr':
            try:
                img = qrcode.make(text)
                img.save("qr.png")
                with open("qr.png", 'rb') as photo:
                    bot.send_photo(chat_id, photo, caption=get_text(chat_id, 'qr_done'), reply_markup=back_markup(chat_id))
                os.remove("qr.png")
            except Exception as e:
                bot.send_message(chat_id, f"❌ خطا: {e}", reply_markup=back_markup(chat_id))
        elif call.data == 'do_translate':
            try:
                translator = Translator()
                lang = get_lang(chat_id)
                dest = 'fa' if lang == 'fa' else 'en'
                result = translator.translate(text, src='auto', dest=dest)
                bot.send_message(chat_id, get_text(chat_id, 'translated', text=result.text), reply_markup=back_markup(chat_id))
            except Exception as e:
                bot.send_message(chat_id, f"❌ خطا در ترجمه: {e}", reply_markup=back_markup(chat_id))
        elif call.data == 'do_pdf':
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for line in text.split('\n'):
                    pdf.cell(200, 10, txt=line, ln=True, align='L')
                pdf.output("text.pdf")
                with open("text.pdf", 'rb') as pdf_file:
                    bot.send_document(chat_id, pdf_file, caption=get_text(chat_id, 'pdf_done'), reply_markup=back_markup(chat_id))
                os.remove("text.pdf")
            except Exception as e:
                bot.send_message(chat_id, f"❌ خطا: {e}", reply_markup=back_markup(chat_id))
        return

# --- پردازش عکس ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    msg = bot.reply_to(message, get_text(chat_id, 'processing'))
    user_dir = f"temp_{chat_id}"
    os.makedirs(user_dir, exist_ok=True)
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        img_path = os.path.join(user_dir, "input.jpg")
        with open(img_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        img = Image.open(img_path)
        img.thumbnail((800, 800))
        out_path = os.path.join(user_dir, "processed.jpg")
        img.save(out_path, optimize=True, quality=60)
        
        with open(out_path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption="✅ عکس شما با موفقیت پردازش شد.", reply_markup=back_markup(chat_id))
        
        bot.delete_message(chat_id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(get_text(chat_id, 'err_processing', error=e), chat_id, msg.message_id, reply_markup=back_markup(chat_id))
    finally:
        shutil.rmtree(user_dir, ignore_errors=True)

# --- پردازش PDF ---
@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    if message.document.mime_type == 'application/pdf':
        msg = bot.reply_to(message, get_text(chat_id, 'processing'))
        user_dir = f"temp_{chat_id}"
        os.makedirs(user_dir, exist_ok=True)
        
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            pdf_path = os.path.join(user_dir, "input.pdf")
            with open(pdf_path, 'wb') as new_file:
                new_file.write(downloaded_file)
                
            with open(pdf_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                text = "".join([page.extract_text() for page in reader.pages])
            
            if text.strip():
                txt_path = os.path.join(user_dir, "extracted.txt")
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                with open(txt_path, 'rb') as txt_file:
                    bot.send_document(chat_id, txt_file, caption="✅ متن استخراج شده از PDF", reply_markup=back_markup(chat_id))
            else:
                bot.edit_message_text("❌ هیچ متنی در این PDF پیدا نشد.", chat_id, msg.message_id, reply_markup=back_markup(chat_id))
                
        except Exception as e:
            bot.edit_message_text(get_text(chat_id, 'err_pdf', error=e), chat_id, msg.message_id, reply_markup=back_markup(chat_id))
        finally:
            shutil.rmtree(user_dir, ignore_errors=True)
            try:
                bot.delete_message(chat_id, msg.message_id)
            except: pass
    else:
        bot.reply_to(message, get_text(chat_id, 'err_pdf_only'), reply_markup=back_markup(chat_id))

# --- پردازش متن ---
@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/') and "Start" not in message.text and "شروع" not in message.text and "راهنما" not in message.text and "Help" not in message.text)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text
    user_text[chat_id] = text
    bot.send_message(chat_id, get_text(chat_id, 'text_options'), reply_markup=text_options_markup(chat_id))

print("🤖 ربات جادویی روشن شد...")
bot.infinity_polling()
