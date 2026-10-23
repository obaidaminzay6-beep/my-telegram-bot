

import telebot
from telebot import types
import qrcode
from fpdf import FPDF
import os
from PIL import Image
import PyPDF2
from googletrans import Translator

# ⚠️ توکن به صورت خودکار از تنظیمات امن گیت‌هاب خوانده می‌شود
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- دیکشنری زبان‌ها ---
LANGUAGES = {
    'fa': {
        'welcome': "سلام **{name}** عزیز! 👋\n\n🌟 به **ربات جادویی ابزارها** خوش آمدید.\n\nمن یک جعبه‌ابزار کامل هستم تا کارهای روزمره شما را آسان کنم. از منوی زیر انتخاب کنید:\n\n✨ **ابزارهای من:**",
        'menu': [
            ('🖼️ عکس به PDF', 'img_to_pdf'),
            ('📝 متن به PDF', 'txt_to_pdf'),
            ('📱 ساخت QR', 'qr'),
            ('🗜️ فشرده‌سازی عکس', 'compress_img'),
            ('📄 PDF به متن', 'pdf_to_txt'),
            ('🌐 ترجمه متن', 'translate'),
            ('📸 تغییر اندازه عکس', 'resize_img'),
            ('🌍 تغییر زبان', 'change_lang')
        ],
        'img_to_pdf': "🖼️ **لطفاً عکس خود را بفرستید تا آن را به یک فایل PDF زیبا تبدیل کنم.**",
        'txt_to_pdf': "📝 **لطفاً متن خود را بفرستید تا آن را به PDF تبدیل کنم.**",
        'qr': "🔗 **لطفاً متن یا لینک خود را برای ساخت QR ارسال کنید.**",
        'compress_img': "🗜️ **لطفاً عکس خود را بفرستید تا آن را فشرده کنم.**",
        'pdf_to_txt': "📄 **لطفاً فایل PDF خود را بفرستید تا متن آن را استخراج کنم.**",
        'translate': "🌐 **لطفاً متن خود را بفرستید تا آن را ترجمه کنم.**",
        'resize_img': "📸 **لطفاً عکس خود را بفرستید تا اندازه آن را تغییر دهم.**",
        'err_processing': "❌ **خطا در پردازش:** {error}",
        'err_pdf': "❌ **خطا در پردازش PDF:** {error}",
        'err_pdf_only': "❌ **لطفاً فقط فایل PDF بفرستید.**",
        'err_text': "❌ **خطا در پردازش متن.**",
        'translated': "🌐 **ترجمه شما:**\n\n{text}",
        'qr_done': "📱 **QR کد شما با موفقیت ساخته شد.**",
        'pdf_done': "✅ **فایل PDF شما آماده دانلود است.**",
        'lang_select': "🌍 **Please select your language:**\nلطفاً زبان خود را انتخاب کنید:"
    },
    'en': {
        'welcome': "Hello **{name}**! 👋\n\n🌟 Welcome to the **Magic Tools Bot**.\n\nI am a complete toolbox to make your daily tasks easier. Choose from the menu below:\n\n✨ **My Tools:**",
        'menu': [
            ('🖼️ Image to PDF', 'img_to_pdf'),
            ('📝 Text to PDF', 'txt_to_pdf'),
            ('📱 Create QR', 'qr'),
            ('🗜️ Compress Image', 'compress_img'),
            ('📄 PDF to Text', 'pdf_to_txt'),
            ('🌐 Translate Text', 'translate'),
            ('📸 Resize Image', 'resize_img'),
            ('🌍 Change Language', 'change_lang')
        ],
        'img_to_pdf': "🖼️ **Please send your image to convert it to a beautiful PDF.**",
        'txt_to_pdf': "📝 **Please send your text to convert it to PDF.**",
        'qr': "🔗 **Please send text or a link to create a QR code.**",
        'compress_img': "🗜️ **Please send your image to compress it.**",
        'pdf_to_txt': "📄 **Please send your PDF file to extract its text.**",
        'translate': "🌐 **Please send your text to translate it.**",
        'resize_img': "📸 **Please send your image to resize it.**",
        'err_processing': "❌ **Error processing:** {error}",
        'err_pdf': "❌ **Error processing PDF:** {error}",
        'err_pdf_only': "❌ **Please send only PDF files.**",
        'err_text': "❌ **Error processing text.**",
        'translated': "🌐 **Your Translation:**\n\n{text}",
        'qr_done': "📱 **Your QR code was created successfully.**",
        'pdf_done': "✅ **Your PDF file is ready for download.**",
        'lang_select': "🌍 **Please select your language:**"
    }
}

user_lang = {}
def get_lang(chat_id): return user_lang.get(chat_id, 'fa')
def get_text(chat_id, key, **kwargs):
    lang = get_lang(chat_id)
    text = LANGUAGES[lang].get(key, LANGUAGES['fa'].get(key, key))
    return text.format(**kwargs)

# --- منوی اصلی ---
def main_menu(chat_id):
    lang = get_lang(chat_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    for text, data in LANGUAGES[lang]['menu']:
        markup.add(types.InlineKeyboardButton(text, callback_data=data))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = get_text(message.chat.id, 'welcome', name=message.from_user.first_name)
    bot.send_message(message.chat.id, text, reply_markup=main_menu(message.chat.id), parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if call.data == 'change_lang':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🇮🇷 فارسی", callback_data='set_lang_fa'))
        markup.add(types.InlineKeyboardButton("🇬🇧 English", callback_data='set_lang_en'))
        bot.edit_message_text(get_text(chat_id, 'lang_select'), chat_id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
        return
    if call.data.startswith('set_lang_'):
        lang = call.data.split('_')[-1]
        user_lang[chat_id] = lang
        text = get_text(chat_id, 'welcome', name=call.from_user.first_name)
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=main_menu(chat_id), parse_mode='Markdown')
        return
    
    prompts = {'img_to_pdf':'img_to_pdf', 'txt_to_pdf':'txt_to_pdf', 'qr':'qr', 'compress_img':'compress_img', 'pdf_to_txt':'pdf_to_txt', 'translate':'translate', 'resize_img':'resize_img'}
    if call.data in prompts:
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, get_text(chat_id, prompts[call.data]), parse_mode='Markdown')

# --- پردازش عکس ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    msg = bot.reply_to(message, "⏳ **در حال پردازش عکس...**")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("temp_image.jpg", 'wb') as new_file:
            new_file.write(downloaded_file)
        
        img = Image.open("temp_image.jpg")
        img.thumbnail((800, 800))
        img.save("processed_image.jpg", optimize=True, quality=60)
        
        with open("processed_image.jpg", 'rb') as photo:
            bot.send_photo(chat_id, photo, caption="✅ **عکس شما با موفقیت پردازش شد.**")
        
        os.remove("temp_image.jpg")
        os.remove("processed_image.jpg")
        bot.delete_message(chat_id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(get_text(chat_id, 'err_processing', error=e), chat_id, msg.message_id)

# --- پردازش PDF ---
@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    if message.document.mime_type == 'application/pdf':
        msg = bot.reply_to(message, "⏳ **در حال استخراج متن از PDF...**")
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
                bot.edit_message_text(f"📄 **متن استخراج شده:**\n\n{text}", chat_id, msg.message_id, parse_mode='Markdown')
            else:
                bot.edit_message_text("❌ **هیچ متنی در این PDF پیدا نشد.**", chat_id, msg.message_id)
            os.remove("temp.pdf")
        except Exception as e:
            bot.edit_message_text(get_text(chat_id, 'err_pdf', error=e), chat_id, msg.message_id)
    else:
        bot.reply_to(message, get_text(chat_id, 'err_pdf_only'))

# --- پردازش متن ---
@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
def handle_text(message):
    chat_id = message.chat.id
    text = message.text
    
    # ۱. ساخت QR
    try:
        img = qrcode.make(text)
        img.save("qr.png")
        with open("qr.png", 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=get_text(chat_id, 'qr_done'), parse_mode='Markdown')
        os.remove("qr.png")
    except: pass

    # ۲. ترجمه
    try:
        translator = Translator()
        if any(c.isalpha() for c in text) and not text.startswith('http'):
            lang = get_lang(chat_id)
            dest = 'fa' if lang == 'fa' else 'en'
            result = translator.translate(text, src='auto', dest=dest)
            bot.reply_to(message, get_text(chat_id, 'translated', text=result.text), parse_mode='Markdown')
            return
    except: pass

    # ۳. تبدیل متن به PDF
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in text.split('\n'):
            pdf.cell(200, 10, txt=line, ln=True, align='L')
        pdf.output("text.pdf")
        with open("text.pdf", 'rb') as pdf_file:
            bot.send_document(chat_id, pdf_file, caption=get_text(chat_id, 'pdf_done'), parse_mode='Markdown')
        os.remove("text.pdf")
    except:
        bot.reply_to(message, get_text(chat_id, 'err_text'))

print("🤖 ربات جادویی روشن شد...")
bot.infinity_polling()
