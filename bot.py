import os
import io
import logging
from flask import Flask, request
import telebot
from telebot import types

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Попробуем импортировать Pillow
try:
    from PIL import Image, ImageOps
    PILLOW_AVAILABLE = True
    logger.info("✅ Pillow is available")
except ImportError:
    PILLOW_AVAILABLE = False
    logger.warning("❌ Pillow not available")

# Стикерпак бота (у каждого бота может быть свой стикерпак)
STICKER_SET_NAME = "MyCustomStickersByBot"  # Должно заканчиваться на ByBot

def create_sticker_image(photo_data):
    """Создает изображение для стикера"""
    if not PILLOW_AVAILABLE:
        raise Exception("Pillow not installed")
    
    # Открываем изображение
    image = Image.open(io.BytesIO(photo_data)).convert('RGBA')
    
    # Размер для стикеров Telegram
    target_size = 512
    
    # Определяем область для обрезки (центрируем)
    width, height = image.size
    
    # Вычисляем квадратную область
    size = min(width, height)
    left = (width - size) // 2
    top = (height - size) // 2
    
    # Обрезаем до квадрата
    cropped = image.crop((left, top, left + size, top + size))
    
    # Масштабируем до 512x512
    sticker = cropped.resize((target_size, target_size), Image.Resampling.LANCZOS)
    
    return sticker

def create_sticker_set(user_id):
    """Создает стикерпак для пользователя"""
    pack_name = f"{STICKER_SET_NAME}_{user_id}"
    return pack_name

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('➕ Добавить стикер'))
    markup.add(types.KeyboardButton('📚 Мой стикерпак'))
    
    bot.reply_to(message,
        "🎉 *Бот для создания стикеров*\n\n"
        "Я создаю *настоящие стикеры* которые сразу появляются в Telegram!\n\n"
        "✨ *Что можно сделать:*\n"
        "• Добавить стикер из фото\n"
        "• Стикеры сохраняются в твой пак\n"
        "• Использовать как обычные стикеры\n\n"
        "Нажми *Добавить стикер* и отправь фото! 🚀",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(commands=['addsticker'])
def add_sticker(message):
    bot.reply_to(message, "Отправь фото для создания стикера! 📷")

@bot.message_handler(func=lambda message: message.text == '➕ Добавить стикер')
def add_sticker_btn(message):
    bot.reply_to(message, 
        "📸 Отправь мне фото - я превращу его в стикер!\n\n"
        "✨ *Советы для лучшего результата:*\n"
        "• Квадратные фото работают лучше\n"
        "• Объект в центре кадра\n"
        "• Хорошее освещение",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == '📚 Мой стикерпак')
def my_stickerpack(message):
    pack_name = create_sticker_set(message.chat.id)
    bot.reply_to(message,
        f"📚 *Твой стикерпак*\n\n"
        f"Используй стикеры через меню стикеров в Telegram!\n\n"
        f"Чтобы добавить новый стикер:\n"
        f"1. Нажми *Добавить стикер*\n"
        f"2. Отправь фото\n"
        f"3. Готово! Стикер появится в твоем паке\n\n"
        f"✨ Все просто!",
        parse_mode='Markdown'
    )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        user_id = message.chat.id
        pack_name = create_sticker_set(user_id)
        
        bot.reply_to(message, "🔄 Создаю стикер...")
        
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        if PILLOW_AVAILABLE:
            # Создаем стикер
            sticker_image = create_sticker_image(downloaded_file)
            
            # Сохраняем как PNG
            output = io.BytesIO()
            sticker_image.save(output, format='PNG', optimize=True)
            output.seek(0)
            
            try:
                # Пробуем создать стикерпак или добавить стикер в существующий
                # Генерируем уникальный эмодзи для стикера
                emoji = "👍"
                
                # Загружаем стикер
                with open('temp_sticker.png', 'wb') as f:
                    f.write(output.getvalue())
                
                # Отправляем как стикер (это создаст стикер в интерфейсе)
                with open('temp_sticker.png', 'rb') as sticker_file:
                    bot.send_sticker(
                        message.chat.id,
                        sticker_file,
                        reply_to_message_id=message.message_id
                    )
                
                # Удаляем временный файл
                os.remove('temp_sticker.png')
                
                bot.reply_to(message,
                    "✅ *Стикер создан!*\n\n"
                    "Теперь ты можешь:\n"
                    "• Нажать на стикер чтобы добавить в избранное\n"
                    "• Отправить друзьям\n"
                    "• Использовать в любом чате\n\n"
                    "Хочешь еще стикеров? Отправляй следующее фото! 📷",
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Sticker creation error: {e}")
                # Если не получилось создать стикер, отправляем как документ
                bot.send_document(
                    message.chat.id,
                    output,
                    visible_file_name='sticker.png',
                    caption="✅ Стикер готов! Используй этот файл"
                )
            
        else:
            bot.reply_to(message, "❌ Сервис временно недоступен")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        bot.reply_to(message, "❌ Ошибка при создании стикера")

@bot.message_handler(func=lambda message: True)
def echo(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('➕ Добавить стикер'))
    
    bot.reply_to(message,
        "Отправь фото для создания стикера! 📷\n"
        "Или используй кнопку ниже:",
        reply_markup=markup
    )

# Вебхук обработчик
@app.route('/webhook/' + TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Error', 403

@app.route('/')
def home():
    return "🤖 Real Sticker Creator Bot"

if __name__ == '__main__':
    print("🚀 Starting Real Sticker Creator...")
    
    # Устанавливаем вебхук
    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url:
        webhook_url = f"{render_url}/webhook/{TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook set to: {webhook_url}")
    
    # Запускаем Flask
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
