
import telebot
from telebot import types
import qrcode
from fpdf import FPDF
import os

# ⚠️ توکن به صورت خودکار از تنظیمات امن گیت‌هاب خوانده می‌شود
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- منوی اصلی شیک ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton('🖼️ تبدیل عکس به PDF', callback_data='img_to_pdf')
    btn2 = types.InlineKeyboardButton('📝 تبدیل متن به PDF', callback_data='txt_to_pdf')
    btn3 = types.InlineKeyboardButton('📱 ساخت QR کد', callback_data='qr')
    markup.add(btn1, btn2, btn3)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        f"سلام {message.from_user.first_name} عزیز! 👋\n\n"
        "به **ربات ابزارهای هوشمند** خوش آمدید. 🌟\n"
        "من اینجا هستم تا کارهای روزمره شما را آسان کنم.\n\n"
        "👇 **از منوی زیر انتخاب کنید:**"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu(), parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'img_to_pdf':
        bot.answer_callback_query(call.id, "عکس را بفرستید!")
        bot.send_message(call.message.chat.id, "🖼️ **لطفاً عکس خود را بفرستید تا آن را به یک فایل PDF تبدیل کنم.**")
    elif call.data == 'txt_to_pdf':
        bot.answer_callback_query(call.id, "متن را بفرستید!")
        bot.send_message(call.message.chat.id, "📝 **لطفاً متن خود را بفرستید تا آن را به یک فایل PDF تبدیل کنم.**")
    elif call.data == 'qr':
        bot.answer_callback_query(call.id, "لینک یا متن را بفرستید!")
        bot.send_message(call.message.chat.id, "🔗 **لطفاً لینک یا متنی که می‌خواهید QR آن ساخته شود را ارسال کنید.**")

# --- پردازش عکس برای تبدیل به PDF ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    msg = bot.reply_to(message, "⏳ **در حال پردازش عکس...**")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("temp_image.jpg", 'wb') as new_file:
            new_file.write(downloaded_file)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.image("temp_image.jpg", x=10, y=10, w=190)
        pdf.output("output.pdf")
        
        with open("output.pdf", 'rb') as pdf_file:
            bot.send_document(message.chat.id, pdf_file, caption="✅ **فایل PDF شما با موفقیت ساخته شد.**")
        
        os.remove("temp_image.jpg")
        os.remove("output.pdf")
        bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ **خطا در تبدیل:** {e}", message.chat.id, msg.message_id)

# --- پردازش متن برای تبدیل به PDF یا ساخت QR ---
@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
def handle_text(message):
    text = message.text
    
    # ساخت QR کد
    try:
        img = qrcode.make(text)
        img.save("qr.png")
        with open("qr.png", 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption="📱 **QR کد شما با موفقیت ساخته شد.**")
        os.remove("qr.png")
    except Exception as e:
        # اگر QR نساخت، متن را به PDF تبدیل کن
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in text.split('\n'):
                pdf.cell(200, 10, txt=line, ln=True, align='L')
            pdf.output("text.pdf")
            
            with open("text.pdf", 'rb') as pdf_file:
                bot.send_document(message.chat.id, pdf_file, caption="✅ **فایل PDF متن شما آماده است.**")
            os.remove("text.pdf")
        except Exception as e2:
            bot.reply_to(message, "❌ **خطا در پردازش متن.**")

print("🤖 ربات ابزارهای هوشمند روشن شد...")
bot.infinity_polling()
