import os
import io
import logging
import requests
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
    from PIL import Image, ImageOps, ImageFilter, ImageEnhance
    PILLOW_AVAILABLE = True
    logger.info("✅ Pillow is available")
except ImportError:
    PILLOW_AVAILABLE = False
    logger.warning("❌ Pillow not available")

# Хранилище для создания стикерпаков
user_stickerpacks = {}

def remove_background_simple(image):
    """Упрощенное удаление фона - делает белый/светлый фон прозрачным"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    datas = image.getdata()
    new_data = []
    
    for item in datas:
        # Делаем белый и светлые цвета прозрачными
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            new_data.append((255, 255, 255, 0))  # полностью прозрачный
        else:
            new_data.append(item)
    
    image.putdata(new_data)
    return image

def create_sticker_image(photo_data):
    """Создает изображение для стикера с прозрачным фоном"""
    if not PILLOW_AVAILABLE:
        raise Exception("Pillow not installed")
    
    # Открываем изображение
    image = Image.open(io.BytesIO(photo_data)).convert('RGBA')
    
    # Удаляем фон (упрощенная версия)
    image = remove_background_simple(image)
    
    # Создаем квадратное изображение 512x512
    target_size = 512
    
    # Создаем новое изображение с прозрачным фоном
    sticker = Image.new('RGBA', (target_size, target_size), (255, 255, 255, 0))
    
    # Масштабируем оригинальное изображение чтобы вписать в 512x512
    width, height = image.size
    scale = min(target_size / width, target_size / height) * 0.8  # оставляем отступы
    
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Позиционируем по центру
    x = (target_size - new_width) // 2
    y = (target_size - new_height) // 2
    
    # Накладываем на прозрачный фон
    sticker.paste(resized_image, (x, y), resized_image)
    
    return sticker

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('📸 Создать стикер'))
    markup.add(types.KeyboardButton('📚 Мой стикерпак'))
    markup.add(types.KeyboardButton('ℹ️ Помощь'))
    
    bot.reply_to(message,
        "🎨 *Бот для создания стикеров*\n\n"
        "Я помогу тебе создать собственный стикерпак!\n\n"
        "✨ *Что можно сделать:*\n"
        "• Создать стикер из фото\n"
        "• Добавить в свой стикерпак\n"
        "• Поделиться с друзьями\n\n"
        "Начни с кнопки *Создать стикер*!",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        "🤖 *Как создать стикерпак:*\n\n"
        "1. Нажми *Создать стикер*\n"
        "2. Отправь фото с четким объектом\n"
        "3. Получи стикер с прозрачным фоном\n"
        "4. Используй файл для создания стикерпака\n\n"
        "📝 *Советы для фото:*\n"
        "• Объект на светлом фоне\n"
        "• Хорошее освещение\n"
        "• Четкие контуры\n"
        "• Объект в центре кадра",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['createsticker'])
def create_sticker_cmd(message):
    bot.reply_to(message, "Отправь мне фото для создания стикера! 📷")

@bot.message_handler(func=lambda message: message.text == '📸 Создать стикер')
def make_sticker(message):
    bot.reply_to(message, 
        "📸 *Отправь фото для стикера*\n\n"
        "Лучше всего подойдут:\n"
        "• Фото на белом фоне\n"
        "• Селфи с хорошим светом\n"  
        "• Изображения предметов\n"
        "• Картинки с четкими краями",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == '📚 Мой стикерпак')
def my_stickerpack(message):
    bot.reply_to(message,
        "📚 *Создание стикерпака*\n\n"
        "Чтобы создать стикерпак в Telegram:\n\n"
        "1. Нажми *Создать стикер*\n"
        "2. Отправь фото\n"
        "3. Сохрани полученный PNG-файл\n"
        "4. Напиши @Stickers\n"
        "5. Выбери /newpack\n"
        "6. Загрузи сохраненные стикеры\n\n"
        "Или используй официального @Stickers бота!",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == 'ℹ️ Помощь')
def show_help(message):
    help_cmd(message)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.reply_to(message, "🔄 Создаю стикер с прозрачным фоном...")
        
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        if PILLOW_AVAILABLE:
            # Создаем стикер с прозрачным фоном
            sticker_image = create_sticker_image(downloaded_file)
            
            # Сохраняем как PNG
            output = io.BytesIO()
            sticker_image.save(output, format='PNG', optimize=True)
            output.seek(0)
            
            # Отправляем стикер
            bot.send_document(
                message.chat.id, 
                output, 
                visible_file_name='sticker.png',
                caption="✅ *Стикер готов!*\n\n"
                       "📝 *Что дальше:*\n"
                       "1. Сохрани этот файл\n"
                       "2. Напиши @Stickers в Telegram\n" 
                       "3. Создай новый стикерпак\n"
                       "4. Загрузи этот файл как стикер\n\n"
                       "✨ Теперь у тебя есть собственный стикер!",
                parse_mode='Markdown'
            )
            
        else:
            # Pillow не доступен
            bot.reply_to(message,
                "❌ *Сервис временно недоступен*\n\n"
                "Ведутся технические работы...",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error creating sticker: {e}")
        bot.reply_to(message,
            "❌ *Не удалось создать стикер*\n\n"
            "Попробуй:\n"
            "• Фото на светлом фоне\n" 
            "• Более четкое изображение\n"
            "• Другой ракурс\n\n"
            "Или попробуй позже!",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: True)
def echo(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('📸 Создать стикер'))
    markup.add(types.KeyboardButton('📚 Мой стикерпак'))
    
    bot.reply_to(message,
        "Выбери действие из меню ниже 👇",
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
    return "🤖 Sticker Bot - Create custom sticker packs!"

@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    print("🚀 Starting Sticker Pack Bot...")
    print(f"📦 Pillow available: {PILLOW_AVAILABLE}")
    
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
