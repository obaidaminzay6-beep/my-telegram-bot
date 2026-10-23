

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

# ⚠️ توکن به صورت خودکار از تنظیمات امن گیت‌هاب خوانده می‌شود
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- تنظیمات شخصی‌سازی ---
LOGO_URL = "https://i.imgur.com/8QO9R3n.jpeg" 
# لینک پشتیبانی (آیدی تلگرام شما)
SUPPORT_LINK = "https://t.me/DarkVenom404" 

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
        'txt_to_pdf': "📝 لطفاً متن خود را بفرستید تا آن را به PDF تبدیل کنم.",
        'qr': "🔗 لطفاً متن یا لینک خود را برای ساخت QR ارسال کنید.",
        'compress_img': "🗜️ لطفاً عکس خود را بفرستید تا آن را فشرده کنم.",
        'pdf_to_txt': "📄 لطفاً فایل PDF خود را بفرستید تا متن آن را استخراج کنم.",
        'translate': "🌐 لطفاً متن خود را بفرستید تا آن را ترجمه کنم.",
        
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
        'help_text': "📖 راهنمای ربات جادویی:\n\n🖼️ عکس به PDF: عکس را بفرستید تا به PDF تبدیل شود.\n📝 متن به PDF: متن را بفرستید تا به PDF تبدیل شود.\n📱 ساخت QR: لینک یا متن را بفرستید تا QR ساخته شود.\n🗜️ فشرده‌سازی عکس: عکس را بفرستید تا حجم آن کم شود.\n📄 PDF به متن: فایل PDF را بفرستید تا متن آن استخراج شود.\n🌐 ترجمه: متن انگلیسی یا فارسی را بفرستید تا ترجمه شود.\n📅 تاریخ و ساعت: تاریخ شمسی و میلادی و ساعت دقیق را نشان می‌دهد.\n\n🔙 برای بازگشت به منو از دکمه زیر استفاده کنید.",
        
        'datetime_title': "📅 تاریخ و ساعت دقیق:",
        'about_title': "ℹ️ درباره ربات جادویی:\n\nاین ربات یک جعبه‌ابزار کامل و رایگان است که برای راحتی شما طراحی شده است.\n\n✨ نسخه: 2.0\n👨‍💻 سازنده: تیم توسعه‌دهندگان\n🚀 پلتفرم: GitHub Actions\n\nاز اینکه از ربات ما استفاده می‌کنید سپاسگزاریم ❤️",
        
        'support_btn': "💬 پشتیبانی",
        
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
        'txt_to_pdf': "📝 Please send your text to convert it to PDF.",
        'qr': "🔗 Please send text or a link to create a QR code.",
        'compress_img': "🗜️ Please send your image to compress it.",
        'pdf_to_txt': "📄 Please send your PDF file to extract its text.",
        'translate': "🌐 Please send your text to translate it.",
        
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
        'help_text': "📖 Magic Bot Help:\n\n🖼️ Image to PDF: Send an image to convert to PDF.\n📝 Text to PDF: Send text to convert to PDF.\n📱 Create QR: Send text or link to create a QR code.\n🗜️ Compress Image: Send an image to reduce its size.\n📄 PDF to Text: Send a PDF file to extract its text.\n🌐 Translate: Send text to translate it.\n📅 Date & Time: Shows the exact date and time.\n\n🔙 Use the button below to return to the main menu.",
        
        'datetime_title': "📅 Exact Date & Time:",
        'about_title': "ℹ️ About Magic Bot:\n\nThis bot is a complete and free toolbox designed for your convenience.\n\n✨ Version: 2.0\n👨‍💻 Developer: Dev Team\n🚀 Platform: GitHub Actions\n\nThank you for using our bot ❤️",
        
        'support_btn': "💬 Support",
        
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

# --- منوی اصلی (Inline) ---
def main_menu(chat_id):
    lang = get_lang(chat_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for row in LANGUAGES[lang]['menu_rows']:
        buttons = [types.InlineKeyboardButton(text, callback_data=data) for text, data in row]
        markup.add(*buttons)
    
    markup.add(types.InlineKeyboardButton(LANGUAGES[lang]['change_lang_btn'], callback_data='change_lang'))
    # فقط دکمه پشتیبانی
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
    btn_start = types.KeyboardButton(LANGUAGES[lang]['main_menu_btn'])
    btn_help = types.KeyboardButton(LANGUAGES[lang]['help_btn'])
    markup.add(btn_start, btn_help)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    caption = get_text(chat_id, 'welcome', name=message.from_user.first_name)
    try:
        bot.send_photo(chat_id, photo=LOGO_URL, caption=caption, reply_markup=main_menu(chat_id))
    except:
        bot.send_message(chat_id, caption, reply_markup=main_menu(chat_id))
    bot.send_message(chat_id, "👇", reply_markup=persistent_keyboard(chat_id))

@bot.message_handler(func=lambda message: message.text in [LANGUAGES['fa']['main_menu_btn'], LANGUAGES['en']['main_menu_btn']])
def back_to_menu(message):
    chat_id = message.chat.id
    text = get_text(chat_id, 'welcome', name=message.from_user.first_name)
    bot.send_message(chat_id, text, reply_markup=main_menu(chat_id))

@bot.message_handler(func=lambda message: message.text in [LANGUAGES['fa']['help_btn'], LANGUAGES['en']['help_btn']])
def show_help(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, get_text(chat_id, 'help_text'), reply_markup=back_markup(chat_id))

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
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, get_text(chat_id, 'about_title'), reply_markup=back_markup(chat_id))
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
        bot.send_message(chat_id, get_text(chat_id, prompts[call.data]), reply_markup=back_markup(chat_id))
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

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    msg = bot.reply_to(message, "⏳ در حال پردازش عکس...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("temp_image.jpg", 'wb') as new_file:
            new_file.write(downloaded_file)
        img = Image.open("temp_image.jpg")
        img.thumbnail((800, 800))
        img.save("processed_image.jpg", optimize=True, quality=60)
        with open("processed_image.jpg", 'rb') as photo:
            bot.send_photo(chat_id, photo, caption="✅ عکس شما با موفقیت پردازش شد.", reply_markup=back_markup(chat_id))
        os.remove("temp_image.jpg")
        os.remove("processed_image.jpg")
        bot.delete_message(chat_id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(get_text(chat_id, 'err_processing', error=e), chat_id, msg.message_id, reply_markup=back_markup(chat_id))

@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    if message.document.mime_type == 'application/pdf':
        msg = bot.reply_to(message, "⏳ در حال استخراج متن از PDF...")
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open("temp.pdf", 'wb') as new_file:
                new_file.write(downloaded_file)
            with open("temp.pdf", 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                text = "".join([page.extract_text() for page in reader.pages])
            if text.strip():
                if len(text) > 4000: text = text[:4000] + "\n\n...(متن طولانی است و کوتاه شده)"
                bot.edit_message_text(f"📄 متن استخراج شده:\n\n{text}", chat_id, msg.message_id, reply_markup=back_markup(chat_id))
            else:
                bot.edit_message_text("❌ هیچ متنی در این PDF پیدا نشد.", chat_id, msg.message_id, reply_markup=back_markup(chat_id))
            os.remove("temp.pdf")
        except Exception as e:
            bot.edit_message_text(get_text(chat_id, 'err_pdf', error=e), chat_id, msg.message_id, reply_markup=back_markup(chat_id))
    else:
        bot.reply_to(message, get_text(chat_id, 'err_pdf_only'), reply_markup=back_markup(chat_id))

@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/') and message.text not in [LANGUAGES['fa']['main_menu_btn'], LANGUAGES['fa']['help_btn'], LANGUAGES['en']['main_menu_btn'], LANGUAGES['en']['help_btn']])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text
    user_text[chat_id] = text
    bot.send_message(chat_id, get_text(chat_id, 'text_options'), reply_markup=text_options_markup(chat_id))

print("🤖 ربات جادویی روشن شد...")
bot.infinity_polling()
