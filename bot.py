import os
import io
import logging
from flask import Flask, request
import telebot
from telebot import types
import random
import string

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Попробуем импортировать Pillow
try:
    from PIL import Image, ImageOps, ImageFilter
    PILLOW_AVAILABLE = True
    logger.info("✅ Pillow is available")
except ImportError:
    PILLOW_AVAILABLE = False
    logger.warning("❌ Pillow not available")

def create_sticker_image(photo_data, style='simple'):
    """Создает стикер 512x512 с разными стилями"""
    if not PILLOW_AVAILABLE:
        raise Exception("Pillow not installed")
    
    image = Image.open(io.BytesIO(photo_data)).convert('RGBA')
    target_size = 512
    
    # Создаем квадратное изображение
    width, height = image.size
    
    # Вычисляем размер для вписывания
    scale = min(target_size / width, target_size / height) * 0.9  # оставляем отступы
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    # Масштабируем
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Создаем прозрачный фон 512x512
    sticker = Image.new('RGBA', (target_size, target_size), (255, 255, 255, 0))
    
    # Центрируем изображение
    x = (target_size - new_width) // 2
    y = (target_size - new_height) // 2
    
    # Накладываем на прозрачный фон
    sticker.paste(resized, (x, y), resized)
    
    # Применяем стиль
    if style == 'cartoon':
        # Упрощенный мультяшный эффект
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Color(sticker)
        sticker = enhancer.enhance(1.3)
        sticker = sticker.filter(ImageFilter.SMOOTH_MORE)
    elif style == 'outline':
        # Эффект контуров
        edges = sticker.filter(ImageFilter.FIND_EDGES)
        sticker = Image.blend(sticker, edges, 0.1)
    
    return sticker

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

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🎨 Создать стикер'))
    markup.add(types.KeyboardButton('📚 Как добавить в Telegram'))
    markup.add(types.KeyboardButton('✨ Стили'))
    
    bot.reply_to(message,
        "🎉 *Бот для создания стикеров*\n\n"
        "Я помогу тебе создать крутые стикеры из фото!\n\n"
        "✨ *Что я умею:*\n"
        "• Создавать стикеры 512x512 пикселей\n"
        "• Убирать фон (упрощенно)\n"
        "• Применять разные стили\n"
        "• Готовые PNG для Telegram\n\n"
        "Нажми *Создать стикер* и отправь фото! 📷",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == '🎨 Создать стикер')
def create_sticker(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('⚪ Простой стикер'))
    markup.add(types.KeyboardButton('🎨 Мультяшный'))
    markup.add(types.KeyboardButton('🌈 С контурами'))
    markup.add(types.KeyboardButton('⬅️ Назад'))
    
    bot.reply_to(message,
        "🎨 *Выбери стиль для стикера:*\n\n"
        "⚪ *Простой стикер* - чистое изображение\n"
        "🎨 *Мультяшный* - яркие цвета, мультяшный вид\n"
        "🌈 *С контурами* - подчеркивает края\n\n"
        "Выбери стиль и отправь фото!",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == '📚 Как добавить в Telegram')
def how_to_add(message):
    bot.reply_to(message,
        "📚 *Как добавить стикеры в Telegram*\n\n"
        "1. *Создай стикер* через этого бота\n"
        "2. *Сохрани* полученный PNG-файл\n"
        "3. *Напиши* @Stickers боту\n"
        "4. *Выбери* /newpack\n"
        "5. *Придумай* название для стикерпака\n"
        "6. *Загрузи* сохраненные PNG-файлы\n"
        "7. *Добавь* эмодзи для каждого стикера\n"
        "8. *Отправь* /publish чтобы опубликовать\n"
        "9. *Поздравляю!* Твой стикерпак готов! 🎉\n\n"
        "✨ *Совет:* Можно добавить до 120 стикеров в один пак!",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == '✨ Стили')
def show_styles(message):
    bot.reply_to(message,
        "✨ *Доступные стили:*\n\n"
        "⚪ *Простой стикер*\n"
        "• Чистое изображение\n"
        "• Прозрачный фон\n"
        "• Идеально для четких фото\n\n"
        "🎨 *Мультяшный*\n"
        "• Яркие цвета\n"
        "• Мягкие края\n"
        "• Веселый вид\n\n"
        "🌈 *С контурами*\n"
        "• Подчеркнутые края\n"
        "• Художественный эффект\n"
        "• Для выразительных фото\n\n"
        "Выбери стиль и экспериментируй! 🎨",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == '⬅️ Назад')
def back_to_main(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🎨 Создать стикер'))
    markup.add(types.KeyboardButton('📚 Как добавить в Telegram'))
    
    bot.reply_to(message, "Главное меню:", reply_markup=markup)

# Хранилище выбранных стилей
user_styles = {}

@bot.message_handler(func=lambda message: message.text in ['⚪ Простой стикер', '🎨 Мультяшный', '🌈 С контурами'])
def set_style(message):
    user_styles[message.chat.id] = message.text
    style_map = {
        '⚪ Простой стикер': 'simple',
        '🎨 Мультяшный': 'cartoon', 
        '🌈 С контурами': 'outline'
    }
    
    bot.reply_to(message,
        f"✅ Выбран стиль: {message.text}\n\n"
        f"Теперь отправь мне фото для создания стикера! 📷\n\n"
        f"✨ *Совет:* Лучше всего подходят фото на светлом фоне!",
        parse_mode='Markdown'
    )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        user_id = message.chat.id
        selected_style = user_styles.get(user_id, '⚪ Простой стикер')
        style_map = {
            '⚪ Простой стикер': 'simple',
            '🎨 Мультяшный': 'cartoon',
            '🌈 С контурами': 'outline'
        }
        
        style_key = style_map.get(selected_style, 'simple')
        
        bot.reply_to(message, f"🔄 Создаю стикер в стиле {selected_style}...")
        
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        if not PILLOW_AVAILABLE:
            bot.reply_to(message, "❌ Сервис временно недоступен")
            return
        
        # Создаем стикер
        sticker_image = create_sticker_image(downloaded_file, style_key)
        
        # Убираем фон для простого стикера
        if style_key == 'simple':
            sticker_image = remove_background_simple(sticker_image)
        
        # Сохраняем как PNG
        output = io.BytesIO()
        sticker_image.save(output, format='PNG', optimize=True)
        output.seek(0)
        
        # Отправляем стикер как документ
        bot.send_document(
            message.chat.id,
            output,
            visible_file_name='sticker.png',
            caption=f"✅ *Стикер готов!*\n\n"
                   f"🎨 Стиль: {selected_style}\n"
                   f"📏 Размер: 512x512 пикселей\n"
                   f"🎯 Формат: PNG с прозрачностью\n\n"
                   f"📚 *Как добавить в Telegram:*\n"
                   f"1. Сохрани этот файл\n"
                   f"2. Напиши @Stickers\n"
                   f"3. Создай новый стикерпак\n"
                   f"4. Загрузи этот файл\n\n"
                   f"Хочешь еще? Выбери стиль и отправь новое фото! 📷",
            parse_mode='Markdown'
        )
        
        # Сбрасываем выбранный стиль
        if user_id in user_styles:
            del user_styles[user_id]
            
    except Exception as e:
        logger.error(f"Error creating sticker: {e}")
        bot.reply_to(message,
            "❌ *Не удалось создать стикер*\n\n"
            "Попробуй:\n"
            "• Фото на светлом фоне\n"
            "• Более четкое изображение\n"
            "• Другой ракурс\n\n"
            "Или попробуй другой стиль!",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: True)
def echo(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🎨 Создать стикер'))
    markup.add(types.KeyboardButton('📚 Как добавить в Telegram'))
    
    bot.reply_to(message,
        "Выбери действие из меню ниже 👇\n"
        "Или нажми *Создать стикер* чтобы начать! 🎨",
        parse_mode='Markdown',
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
    return "🤖 Sticker Creator Bot"

if __name__ == '__main__':
    print("🚀 Starting Sticker Creator Bot...")
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
