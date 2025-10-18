import os
import logging
from flask import Flask
import telebot

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Sticker Bot is running!"

@app.route('/health')
def health():
    return "OK"

# Клавиатура
def create_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('🎨 Стили')
    btn2 = telebot.types.KeyboardButton('📸 Сделать стикер')
    btn3 = telebot.types.KeyboardButton('ℹ️ Помощь')
    markup.add(btn1, btn2, btn3)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "🎉 Привет! Я бот для создания стикеров!\n\n"
        "Нажми 'Сделать стикер' и отправь мне фото!",
        reply_markup=create_keyboard()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        "🤖 Как использовать:\n"
        "1. Нажми 'Сделать стикер'\n"
        "2. Отправь фото\n"
        "3. Получи стикер!\n\n"
        "Пока что бот в разработке, но скоро здесь будут крутые стикеры! 🎨"
    )

@bot.message_handler(func=lambda message: message.text == '📸 Сделать стикер')
def make_sticker(message):
    bot.reply_to(message, "Отправь мне фото для создания стикера! 📷")

@bot.message_handler(func=lambda message: message.text == '🎨 Стили')
def show_styles(message):
    bot.reply_to(message,
        "🎨 Доступные стили (скоро):\n"
        "• Мультяшный\n"
        "• Пиксель-арт\n"
        "• Контуры\n"
        "• Винтажный\n"
        "• Без фона\n\n"
        "Сначала отправь фото! 📸"
    )

@bot.message_handler(func=lambda message: message.text == 'ℹ️ Помощь')
def show_help(message):
    help_cmd(message)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # Сохраняем информацию о фото
        file_info = bot.get_file(message.photo[-1].file_id)
        file_size = message.photo[-1].file_size
        
        bot.reply_to(message,
            f"📸 Фото получено!\n"
            f"Размер: {file_size} байт\n"
            f"ID: {file_info.file_id}\n\n"
            "🔄 Функция создания стикеров скоро будет добавлена!\n"
            "А пока можешь отправить еще фото или написать /help"
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        bot.reply_to(message, "❌ Ошибка при обработке фото")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, 
        "Используй кнопки ниже или отправь фото для создания стикера! 📷",
        reply_markup=create_keyboard()
    )

if __name__ == '__main__':
    print("🚀 Starting basic sticker bot...")
    
    # Запускаем веб-сервер в фоне
    import threading
    def run_web():
        port = int(os.getenv('PORT', 10000))
        app.run(host='0.0.0.0', port=port, debug=False)
    
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    # Запускаем бота
    try:
        print("🤖 Starting Telegram bot...")
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ Bot error: {e}")
