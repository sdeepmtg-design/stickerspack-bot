import os
import io
import logging
from flask import Flask, request
import telebot

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Хранилище стилей пользователей
user_styles = {}

# Клавиатура
def create_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('🎨 Выбрать стиль')
    btn2 = telebot.types.KeyboardButton('📸 Сделать стикер')
    btn3 = telebot.types.KeyboardButton('ℹ️ Помощь')
    markup.add(btn1, btn2, btn3)
    return markup

def create_styles_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton('🔄 Простой стикер'),
        telebot.types.KeyboardButton('👾 Квадратный'),
        telebot.types.KeyboardButton('🌈 Прозрачный'),
        telebot.types.KeyboardButton('⬅️ Назад')
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "🎉 Привет! Я бот для создания стикеров!\n\n"
        "Выбери стиль и отправь мне фото - я сделаю из него стикер! 🎨",
        reply_markup=create_keyboard()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        "🤖 Как создать стикер:\n"
        "1. Нажми 'Выбрать стиль'\n"
        "2. Выбери понравившийся стиль\n"
        "3. Нажми 'Сделать стикер'\n"
        "4. Отправь фото\n\n"
        "✨ Готово! Получишь PNG-файл для стикера!"
    )

@bot.message_handler(func=lambda message: message.text == '📸 Сделать стикер')
def make_sticker(message):
    selected_style = user_styles.get(message.chat.id, '🔄 Простой стикер')
    bot.reply_to(message, f"Стиль: {selected_style}\nОтправь фото для создания стикера! 📷")

@bot.message_handler(func=lambda message: message.text == '🎨 Выбрать стиль')
def show_styles(message):
    bot.reply_to(message, "🎨 Выбери стиль для стикера:", reply_markup=create_styles_keyboard())

@bot.message_handler(func=lambda message: message.text == '⬅️ Назад')
def back_to_main(message):
    bot.reply_to(message, "Главное меню:", reply_markup=create_keyboard())

@bot.message_handler(func=lambda message: message.text in ['🔄 Простой стикер', '👾 Квадратный', '🌈 Прозрачный'])
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
        selected_style = user_styles.get(message.chat.id, '🔄 Простой стикер')
        bot.reply_to(message, f"🔄 Создаю стикер в стиле {selected_style}...")
        
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Пробуем обработать с Pillow, если не получится - отправляем оригинал
        try:
            from PIL import Image, ImageOps
            
            image = Image.open(io.BytesIO(downloaded_file)).convert('RGB')
            
            if selected_style == '👾 Квадратный':
                # Делаем квадратным
                size = min(image.size)
                image = ImageOps.fit(image, (size, size), method=Image.Resampling.LANCZOS)
            elif selected_style == '🌈 Прозрачный':
                # Конвертируем в PNG с прозрачностью
                image = image.convert('RGBA')
            
            # Сохраняем как PNG
            output = io.BytesIO()
            image.save(output, format='PNG', optimize=True)
            output.seek(0)
            sticker_data = output
            
        except ImportError:
            # Если Pillow не установлен, используем оригинальное изображение
            logger.warning("Pillow not available, using original image")
            sticker_data = io.BytesIO(downloaded_file)
        
        # Отправляем результат
        bot.send_document(message.chat.id, sticker_data, visible_file_name='sticker.png')
        bot.reply_to(message, f"✅ Готово! Стикер в стиле: {selected_style}")
        
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        bot.reply_to(message, "❌ Ошибка при создании стикера. Попробуй другое фото.")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, 
        "Используй кнопки ниже для создания стикеров! 📷",
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
    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if not render_url:
        return "RENDER_EXTERNAL_URL not set"
    
    webhook_url = f"{render_url}/webhook/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return f"Webhook set to: {webhook_url}"

if __name__ == '__main__':
    print("🚀 Starting sticker bot...")
    
    # Устанавливаем вебхук
    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url:
        webhook_url = f"{render_url}/webhook/{TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook set to: {webhook_url}")
    
    # Запускаем Flask
    port = int(os.getenv('PORT', 10000))
    print(f"🌐 Starting web server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
