import os
import io
import logging
import random
import string
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

# Хранилище пользовательских данных
user_data = {}

def generate_pack_name():
    """Генерирует уникальное имя для стикерпака"""
    return 'pack_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

def create_proper_sticker(photo_data, user_id):
    """Создает правильный стикер для Telegram"""
    if not PILLOW_AVAILABLE:
        raise Exception("Pillow not installed")
    
    # Открываем изображение
    image = Image.open(io.BytesIO(photo_data)).convert('RGBA')
    
    # Размер для стикеров Telegram
    target_size = 512
    
    # Определяем область для обрезки (центрируем)
    width, height = image.size
    
    if width == height:
        # Уже квадрат
        cropped = image
    elif width > height:
        # Горизонтальное - обрезаем по центру
        left = (width - height) // 2
        cropped = image.crop((left, 0, left + height, height))
    else:
        # Вертикальное - обрезаем по центру
        top = (height - width) // 2
        cropped = image.crop((0, top, width, top + width))
    
    # Масштабируем до 512x512
    sticker = cropped.resize((target_size, target_size), Image.Resampling.LANCZOS)
    
    return sticker

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🎨 Создать стикерпак'))
    markup.add(types.KeyboardButton('📖 Инструкция'))
    
    # Инициализируем данные пользователя
    user_data[message.chat.id] = {
        'pack_name': generate_pack_name(),
        'stickers_count': 0,
        'waiting_for_title': False
    }
    
    bot.reply_to(message,
        "🎉 *Бот для создания стикерпаков*\n\n"
        "Я помогу тебе создать персональный стикерпак!\n\n"
        "✨ *Как это работает:*\n"
        "1. Нажми *Создать стикерпак*\n"
        "2. Отправляй фото одно за другим\n"
        "3. Получи ссылку на готовый стикерпак!\n\n"
        "Начни прямо сейчас! 🚀",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(commands=['newpack'])
def new_pack(message):
    user_data[message.chat.id] = {
        'pack_name': generate_pack_name(),
        'stickers_count': 0,
        'waiting_for_title': True
    }
    
    bot.reply_to(message,
        "🎨 *Создание нового стикерпака*\n\n"
        "Придумай название для своего стикерпака:\n"
        "(например: 'Мои крутые стикеры' или 'Memes 2024')",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == '🎨 Создать стикерпак')
def create_pack(message):
    user_data[message.chat.id] = {
        'pack_name': generate_pack_name(), 
        'stickers_count': 0,
        'waiting_for_title': True
    }
    
    bot.reply_to(message,
        "🎨 *Создание нового стикерпака*\n\n"
        "Придумай название для своего стикерпака:\n"
        "(например: 'Мои крутые стикеры' или 'Memes 2024')",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == '📖 Инструкция')
def show_instructions(message):
    bot.reply_to(message,
        "📖 *Инструкция по созданию стикерпака*\n\n"
        "1. Нажми *Создать стикерпак*\n"
        "2. Придумай название\n"
        "3. Отправляй фото одно за другим\n"
        "4. Каждое фото будет добавлено в стикерпак\n"
        "5. Получи ссылку на готовый стикерпак!\n\n"
        "✨ *Советы:*\n"
        "• Используй фото с четкими объектами\n"
        "• Лучше на однородном фоне\n"
        "• Можно добавить до 120 стикеров\n\n"
        "Начни с кнопки *Создать стикерпак*!",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('waiting_for_title'))
def handle_pack_title(message):
    user_id = message.chat.id
    user_data[user_id]['pack_title'] = message.text
    user_data[user_id]['waiting_for_title'] = False
    
    bot.reply_to(message,
        f"✅ Отлично! Стикерпак *'{message.text}'* создан!\n\n"
        "Теперь отправляй фото одно за другим:\n"
        "• Каждое фото станет стикером\n"
        "• Можно отправить несколько фото\n"
        "• Когда закончишь - напиши /done\n\n"
        "Отправь первое фото! 📷",
        parse_mode='Markdown'
    )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        user_id = message.chat.id
        user_info = user_data.get(user_id, {})
        
        if not user_info or user_info.get('waiting_for_title'):
            bot.reply_to(message, "❌ Сначала создай стикерпак! Нажми 'Создать стикерпак'")
            return
        
        bot.reply_to(message, "🔄 Добавляю стикер в твой пак...")
        
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        if PILLOW_AVAILABLE:
            # Создаем стикер
            sticker_image = create_proper_sticker(downloaded_file, user_id)
            
            # Сохраняем как PNG
            output = io.BytesIO()
            sticker_image.save(output, format='PNG', optimize=True)
            output.seek(0)
            
            # Отправляем как документ (пока не можем создать настоящий стикерпак через API)
            user_data[user_id]['stickers_count'] += 1
            
            bot.send_document(
                message.chat.id,
                output,
                visible_file_name=f"sticker_{user_data[user_id]['stickers_count']}.png",
                caption=f"✅ Стикер #{user_data[user_id]['stickers_count']} готов!\n"
                       f"Пак: {user_info.get('pack_title', 'Мой пак')}\n\n"
                       f"Отправляй следующее фото или напиши /done чтобы завершить"
            )
            
        else:
            bot.reply_to(message, "❌ Сервис временно недоступен")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        bot.reply_to(message, "❌ Ошибка при создании стикера")

@bot.message_handler(commands=['done'])
def finish_pack(message):
    user_id = message.chat.id
    user_info = user_data.get(user_id, {})
    
    if not user_info or user_info.get('waiting_for_title'):
        bot.reply_to(message, "❌ Сначала создай стикерпак!")
        return
    
    stickers_count = user_info.get('stickers_count', 0)
    
    if stickers_count == 0:
        bot.reply_to_message(message, "❌ Ты не добавил ни одного стикера!")
        return
    
    bot.reply_to(message,
        f"🎉 *Твой стикерпак готов!*\n\n"
        f"📦 *{user_info.get('pack_title', 'Мой пак')}*\n"
        f"📊 Стикеров: {stickers_count}\n\n"
        f"📝 *Чтобы добавить стикеры в Telegram:*\n"
        f"1. Сохрани все PNG-файлы\n"
        f"2. Напиши @Stickers боту\n"
        f"3. Выбери /newpack\n"
        f"4. Загрузи сохраненные файлы\n\n"
        f"✨ Теперь у тебя есть собственный стикерпак!\n\n"
        f"Хочешь создать еще один? Нажми *Создать стикерпак*!",
        parse_mode='Markdown',
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
            types.KeyboardButton('🎨 Создать стикерпак')
        )
    )
    
    # Сбрасываем данные пользователя
    user_data[user_id] = {}

@bot.message_handler(func=lambda message: True)
def echo(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🎨 Создать стикерпак'))
    markup.add(types.KeyboardButton('📖 Инструкция'))
    
    bot.reply_to(message,
        "Выбери действие из меню 👇",
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
    return "🤖 Sticker Pack Creator Bot"

if __name__ == '__main__':
    print("🚀 Starting Sticker Pack Creator...")
    
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
