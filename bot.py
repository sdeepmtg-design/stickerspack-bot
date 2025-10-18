import os
import logging
from flask import Flask, request, jsonify
import telebot

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Глобальная переменная для хранения выбранного стиля
user_styles = {}

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
    styles_keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    styles_keyboard.add(
        telebot.types.KeyboardButton('🔄 Мультяшный'),
        telebot.types.KeyboardButton('👾 Пиксель-арт'),
        telebot.types.KeyboardButton('🌈 Контуры'),
        telebot.types.KeyboardButton('🔥 Винтажный'),
        telebot.types.KeyboardButton('⬅️ Назад')
    )
    bot.reply_to(message, "🎨 Выбери стиль для будущих стикеров:", reply_markup=styles_keyboard)

@bot.message_handler(func=lambda message: message.text == '⬅️ Назад')
def back_to_main(message):
    bot.reply_to(message, "Главное меню:", reply_markup=create_keyboard())

@bot.message_handler(func=lambda message: message.text in ['🔄 Мультяшный', '👾 Пиксель-арт', '🌈 Контуры', '🔥 Винтажный'])
def set_style(message):
    user_styles[message.chat.id] = message.text
    bot.reply_to(message, 
        f"✅ Выбран стиль: {message.text}\n"
        f"Теперь нажми 'Сделать стикер' и отправь фото!",
        reply_markup=create_keyboard()
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
        selected_style = user_styles.get(message.chat.id, 'стандартный')
        
        response = (
            f"📸 Фото получено!\n"
            f"Размер: {file_size} байт\n"
            f"Стиль: {selected_style}\n\n"
        )
        
        if selected_style != 'стандартный':
            response += f"🎨 Будет применен стиль: {selected_style}\n\n"
        
        response += (
            "🔄 Функция создания стикеров скоро будет добавлена!\n"
            "Сейчас работаем над стабильностью бота 💪"
        )
        
        bot.reply_to(message, response)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        bot.reply_to(message, "❌ Ошибка при обработке фото")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, 
        "Используй кнопки ниже или отправь фото для создания стикера! 📷",
        reply_markup=create_keyboard()
    )

# Вебхук обработчик
@app.route('/webhook/' + TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Error', 403

@app.route('/')
def home():
    return "🤖 Sticker Bot is running with webhook!"

@app.route('/health')
def health():
    return "OK"

@app.route('/set_webhook')
def set_webhook():
    # Получаем URL Render
    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if not render_url:
        return "RENDER_EXTERNAL_URL not set"
    
    webhook_url = f"{render_url}/webhook/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return f"Webhook set to: {webhook_url}"

if __name__ == '__main__':
    print("🚀 Starting bot with webhook...")
    
    # Устанавливаем вебхук при запуске
    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url:
        webhook_url = f"{render_url}/webhook/{TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook set to: {webhook_url}")
    else:
        print("⚠️ RENDER_EXTERNAL_URL not set, using polling")
        bot.remove_webhook()
    
    # Запускаем Flask
    port = int(os.getenv('PORT', 10000))
    print(f"🌐 Starting web server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
