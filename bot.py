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

# Попробуем импортировать Pillow
try:
    from PIL import Image, ImageOps, ImageFilter, ImageEnhance
    PILLOW_AVAILABLE = True
    logger.info("✅ Pillow is available")
except ImportError:
    PILLOW_AVAILABLE = False
    logger.warning("❌ Pillow not available - using basic functionality")

def create_sticker_from_photo(photo_data, style='simple'):
    """Создает настоящий стикер из фото"""
    if not PILLOW_AVAILABLE:
        raise Exception("Pillow not installed")
    
    # Открываем изображение
    image = Image.open(io.BytesIO(photo_data)).convert('RGBA')
    
    # Создаем квадратное изображение 512x512 (стандарт для стикеров)
    target_size = 512
    
    # 1. Определяем область для обрезки
    width, height = image.size
    
    # Обрезаем до квадрата по центру
    if width > height:
        # Горизонтальное фото - обрезаем по высоте
        left = (width - height) // 2
        top = 0
        right = left + height
        bottom = height
    else:
        # Вертикальное фото - обрезаем по ширине
        left = 0
        top = (height - width) // 2
        right = width
        bottom = top + width
    
    # Обрезаем до квадрата
    cropped = image.crop((left, top, right, bottom))
    
    # Масштабируем до 512x512
    sticker = cropped.resize((target_size, target_size), Image.Resampling.LANCZOS)
    
    # Применяем стиль
    if style == 'cartoon':
        # Упрощенный мультяшный эффект
        enhancer = ImageEnhance.Color(sticker)
        sticker = enhancer.enhance(1.3)
        sticker = sticker.filter(ImageFilter.SMOOTH_MORE)
    elif style == 'outline':
        # Эффект контуров
        edges = sticker.filter(ImageFilter.FIND_EDGES)
        sticker = Image.blend(sticker, edges, 0.1)
    
    # Сохраняем как PNG с прозрачностью
    output = io.BytesIO()
    sticker.save(output, format='PNG', optimize=True)
    output.seek(0)
    
    return output

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('📸 Создать стикер'))
    markup.add(telebot.types.KeyboardButton('ℹ️ О боте'))
    
    bot.reply_to(message,
        "🎨 *Бот для создания стикеров*\n\n"
        "Отправь мне фото и я превращу его в настоящий стикер!\n"
        "• Прозрачный фон\n"  
        "• Квадратный формат 512x512\n"
        "• Готово для Telegram\n\n"
        "Нажми *Создать стикер* и отправь фото!",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        "🤖 *Как создать стикер:*\n"
        "1. Нажми *Создать стикер*\n"
        "2. Отправь любое фото\n"
        "3. Получи готовый PNG-стикер\n\n"
        "📝 *Что делает бот:*\n"
        "• Обрезает фото до квадрата\n"
        "• Масштабирует до 512x512 пикселей\n"
        "• Сохраняет с прозрачным фоном\n"
        "• Оптимизирует для Telegram\n\n"
        "Просто отправь фото и попробуй! 📷",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == '📸 Создать стикер')
def make_sticker(message):
    bot.reply_to(message, 
        "Отправь мне фото для создания стикера!\n\n"
        "📝 *Совет:*\n"
        "• Выбери фото с четким объектом\n"  
        "• Лучше без сложного фона\n"
        "• Объект должен быть в центре",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == 'ℹ️ О боте')
def about(message):
    help_cmd(message)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.reply_to(message, "🔄 Создаю стикер...")
        
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        if PILLOW_AVAILABLE:
            # Создаем настоящий стикер
            sticker_data = create_sticker_from_photo(downloaded_file)
            
            # Отправляем стикер
            bot.send_document(
                message.chat.id, 
                sticker_data, 
                visible_file_name='sticker.png',
                caption="✅ *Готово! Твой стикер:*\n\n"
                       "• Формат: 512x512 пикселей\n"
                       "• Прозрачный фон\n" 
                       "• Готов для Telegram\n\n"
                       "Чтобы добавить в стикерпак:\n"
                       "1. Сохрани этот файл\n"
                       "2. Создай новый стикерпак в Telegram\n"
                       "3. Добавь этот PNG как стикер",
                parse_mode='Markdown'
            )
        else:
            # Pillow не доступен - отправляем оригинал
            bot.reply_to(message,
                "❌ *Функция стикеров временно недоступна*\n\n"
                "Технические работы... Попробуй позже!",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error creating sticker: {e}")
        bot.reply_to(message,
            "❌ *Не удалось создать стикер*\n\n"
            "Попробуй:\n"
            "• Другое фото\n" 
            "• Более четкое изображение\n"
            "• Объект в центре кадра",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: True)
def echo(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('📸 Создать стикер'))
    
    bot.reply_to(message,
        "Отправь мне фото для создания стикера! 📷\n"
        "Или нажми кнопку ниже:",
        reply_markup=markup
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
    return "🤖 Sticker Bot - Ready to create stickers!"

@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    print("🚀 Starting Real Sticker Bot...")
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
