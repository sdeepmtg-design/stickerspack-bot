import os
import io
import logging
from flask import Flask
import telebot
from PIL import Image, ImageFilter, ImageEnhance, ImageOps

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

# Клавиатура с выбором стилей
def create_style_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('🎨 Мультяшный')
    btn2 = telebot.types.KeyboardButton('👾 Пиксель-арт')
    btn3 = telebot.types.KeyboardButton('🌈 Контуры')
    btn4 = telebot.types.KeyboardButton('🔥 Винтажный')
    btn5 = telebot.types.KeyboardButton('⚪ Без фона')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "🎉 Привет! Я бот для создания стикеров!\n\n"
        "Выбери стиль и отправь мне фото:",
        reply_markup=create_style_keyboard()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        "🤖 Как использовать:\n"
        "1. Выбери стиль из кнопок\n"
        "2. Отправь фото\n"
        "3. Получи стикер!\n\n"
        "Доступные стили:\n"
        "🎨 Мультяшный - яркие цвета\n"
        "👾 Пиксель-арт - ретро стиль\n"
        "🌈 Контуры - выделяет края\n"
        "🔥 Винтажный - старинный эффект\n"
        "⚪ Без фона - прозрачный фон"
    )

@bot.message_handler(func=lambda message: message.text in ['🎨 Мультяшный', '👾 Пиксель-арт', '🌈 Контуры', '🔥 Винтажный', '⚪ Без фона'])
def set_style(message):
    bot.reply_to(message, f"Выбран стиль: {message.text} 📷\nТеперь отправь фото!")
    # Сохраняем выбранный стиль (упрощенно)
    bot.register_next_step_handler(message, process_photo_with_style, message.text)

def process_photo_with_style(message, style):
    if not message.photo:
        bot.reply_to(message, "Пожалуйста, отправь фото!")
        return
    
    try:
        bot.reply_to(message, "🔄 Обрабатываю фото...")
        
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Открываем изображение
        image = Image.open(io.BytesIO(downloaded_file)).convert('RGB')
        
        # Обрабатываем в выбранном стиле
        if style == '🎨 Мультяшный':
            result = apply_cartoon_style(image)
        elif style == '👾 Пиксель-арт':
            result = apply_pixel_style(image)
        elif style == '🌈 Контуры':
            result = apply_outline_style(image)
        elif style == '🔥 Винтажный':
            result = apply_vintage_style(image)
        elif style == '⚪ Без фона':
            result = remove_background_simple(image)
        
        # Сохраняем результат
        output = io.BytesIO()
        result.save(output, format='PNG')
        output.seek(0)
        
        # Отправляем результат
        bot.send_document(message.chat.id, output, visible_file_name='sticker.png')
        bot.reply_to(message, f"✅ Готово! Стиль: {style}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        bot.reply_to(message, "❌ Ошибка обработки. Попробуй другое фото.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, 
        "📸 Фото получено! Выбери стиль обработки:",
        reply_markup=create_style_keyboard()
    )

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, 
        "Выбери стиль из кнопок ниже и отправь фото для создания стикера! 📷",
        reply_markup=create_style_keyboard()
    )

# Функции обработки изображений
def apply_cartoon_style(image):
    """Мультяшный стиль"""
    # Увеличиваем насыщенность
    enhancer = ImageEnhance.Color(image)
    saturated = enhancer.enhance(1.5)
    
    # Увеличиваем контраст
    contrast_enhancer = ImageEnhance.Contrast(saturated)
    result = contrast_enhancer.enhance(1.3)
    
    return result

def apply_pixel_style(image):
    """Пиксель-арт стиль"""
    # Уменьшаем и увеличиваем обратно
    small_size = (100, 100)
    pixelated = image.resize(small_size, Image.NEAREST)
    result = pixelated.resize(image.size, Image.NEAREST)
    
    return result

def apply_outline_style(image):
    """Стиль с контурами"""
    # Находим края
    edges = image.filter(ImageFilter.FIND_EDGES)
    
    # Увеличиваем контраст краев
    enhancer = ImageEnhance.Contrast(edges)
    strong_edges = enhancer.enhance(3.0)
    
    # Накладываем на оригинал
    result = Image.blend(image, strong_edges, 0.3)
    
    return result

def apply_vintage_style(image):
    """Винтажный стиль"""
    # Добавляем сепию
    sepia = image.convert('RGB')
    width, height = sepia.size
    pixels = sepia.load()
    
    for py in range(height):
        for px in range(width):
            r, g, b = sepia.getpixel((px, py))
            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)
            pixels[px, py] = (min(255, tr), min(255, tg), min(255, tb))
    
    return sepia

def remove_background_simple(image):
    """Упрощенное удаление фона"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    datas = image.getdata()
    new_data = []
    
    for item in datas:
        # Делаем светлые цвета прозрачными
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    
    image.putdata(new_data)
    return image

if __name__ == '__main__':
    print("🚀 Starting bot with sticker functionality...")
    
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
