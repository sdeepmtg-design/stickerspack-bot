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
    from PIL import Image, ImageOps
    PILLOW_AVAILABLE = True
    logger.info("✅ Pillow is available")
except ImportError:
    PILLOW_AVAILABLE = False
    logger.warning("❌ Pillow not available")

# Хранилище данных пользователей
user_packs = {}

def generate_pack_name(user_id):
    """Генерирует уникальное имя для стикерпака"""
    return f"pack_{user_id}_{random.randint(1000, 9999)}_by_{bot.get_me().username}"

def create_sticker_image(photo_data):
    """Создает изображение для стикера 512x512"""
    if not PILLOW_AVAILABLE:
        raise Exception("Pillow not installed")
    
    image = Image.open(io.BytesIO(photo_data)).convert('RGBA')
    target_size = 512
    
    # Создаем квадратное изображение с прозрачным фоном
    width, height = image.size
    
    # Вычисляем размер для вписывания
    scale = min(target_size / width, target_size / height)
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
    
    return sticker

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    
    # Инициализируем или получаем данные пользователя
    if user_id not in user_packs:
        user_packs[user_id] = {
            'pack_name': generate_pack_name(user_id),
            'stickers_count': 0,
            'pack_created': False
        }
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🆕 Создать стикерпак'))
    markup.add(types.KeyboardButton('➕ Добавить стикер'))
    markup.add(types.KeyboardButton('📚 Мой стикерпак'))
    
    bot.reply_to(message,
        "🎉 *Бот для создания стикерпаков*\n\n"
        "Я создаю *настоящие стикерпаки* через Telegram API!\n\n"
        "✨ *Процесс:*\n"
        "1. Нажми *Создать стикерпак*\n"
        "2. Придумай название\n"
        "3. Добавляй стикеры из фото\n"
        "4. Получи ссылку на готовый пак!\n\n"
        "Начни сейчас! 🚀",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == '🆕 Создать стикерпак')
def create_new_pack(message):
    user_id = message.chat.id
    
    # Генерируем новое имя для пакета
    user_packs[user_id] = {
        'pack_name': generate_pack_name(user_id),
        'stickers_count': 0,
        'pack_created': False,
        'waiting_for_title': True
    }
    
    bot.reply_to(message,
        "🎨 *Создание нового стикерпака*\n\n"
        "Придумай название для своего стикерпака:\n"
        "(например: 'Мои мемы' или 'Персональные стикеры')",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: user_packs.get(message.chat.id, {}).get('waiting_for_title'))
def handle_pack_title(message):
    user_id = message.chat.id
    pack_title = message.text
    
    user_packs[user_id]['pack_title'] = pack_title
    user_packs[user_id]['waiting_for_title'] = False
    
    bot.reply_to(message,
        f"✅ Отлично! Стикерпак *'{pack_title}'* готов к созданию!\n\n"
        "Теперь отправь первое фото для стикера 📷\n"
        "Я создам стикерпак и добавлю туда твой первый стикер!",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == '➕ Добавить стикер')
def add_sticker(message):
    user_id = message.chat.id
    user_data = user_packs.get(user_id, {})
    
    if not user_data or not user_data.get('pack_created'):
        bot.reply_to(message, "❌ Сначала создай стикерпак через '🆕 Создать стикерпак'")
        return
    
    bot.reply_to(message, "📸 Отправь фото для нового стикера!")

@bot.message_handler(func=lambda message: message.text == '📚 Мой стикерпак')
def show_my_pack(message):
    user_id = message.chat.id
    user_data = user_packs.get(user_id, {})
    
    if not user_data or not user_data.get('pack_created'):
        bot.reply_to(message, "❌ У тебя еще нет стикерпака. Создай его через '🆕 Создать стикерпак'")
        return
    
    pack_name = user_data['pack_name']
    stickers_count = user_data['stickers_count']
    
    # Ссылка на стикерпак
    bot_username = bot.get_me().username
    stickerpack_url = f"https://t.me/addstickers/{pack_name}"
    
    bot.reply_to(message,
        f"📚 *Твой стикерпак*\n\n"
        f"🪄 *{user_data.get('pack_title', 'Мой стикерпак')}*\n"
        f"📊 Стикеров: {stickers_count}\n\n"
        f"🔗 *Ссылка:* {stickerpack_url}\n\n"
        f"✨ *Как использовать:*\n"
        f"• Перейди по ссылке выше\n"
        f"• Нажми 'Add Stickers'\n"
        f"• Готово! Твой пак в Telegram!",
        parse_mode='Markdown'
    )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        user_id = message.chat.id
        user_data = user_packs.get(user_id, {})
        
        if not user_data:
            bot.reply_to(message, "❌ Сначала создай стикерпак через '🆕 Создать стикерпак'")
            return
        
        bot.reply_to(message, "🔄 Создаю стикер...")
        
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        if not PILLOW_AVAILABLE:
            bot.reply_to(message, "❌ Сервис временно недоступен")
            return
        
        # Создаем стикер
        sticker_image = create_sticker_image(downloaded_file)
        
        # Сохраняем во временный файл
        temp_file = f"temp_{user_id}_{user_data['stickers_count']}.png"
        sticker_image.save(temp_file, format='PNG')
        
        # Эмодзи для стикера
        emojis = "😀"
        
        try:
            with open(temp_file, 'rb') as sticker_data:
                if not user_data.get('pack_created'):
                    # Создаем новый стикерпак с первым стикером
                    bot.create_new_sticker_set(
                        user_id=user_id,
                        name=user_data['pack_name'],
                        title=user_data.get('pack_title', 'Мои стикеры'),
                        png_sticker=sticker_data,
                        emojis=emojis
                    )
                    user_packs[user_id]['pack_created'] = True
                    user_packs[user_id]['stickers_count'] = 1
                    
                    stickerpack_url = f"https://t.me/addstickers/{user_data['pack_name']}"
                    
                    bot.reply_to(message,
                        f"🎉 *Стикерпак создан!*\n\n"
                        f"✅ Первый стикер добавлен!\n"
                        f"📚 Пак: {user_data.get('pack_title', 'Мои стикеры')}\n\n"
                        f"🔗 *Ссылка на стикерпак:*\n"
                        f"{stickerpack_url}\n\n"
                        f"✨ Перейди по ссылке чтобы добавить пак в Telegram!\n\n"
                        f"Хочешь добавить еще стикеров? Отправляй следующее фото! 📷",
                        parse_mode='Markdown'
                    )
                    
                else:
                    # Добавляем стикер в существующий пак
                    bot.add_sticker_to_set(
                        user_id=user_id,
                        name=user_data['pack_name'],
                        png_sticker=sticker_data,
                        emojis=emojis
                    )
                    user_packs[user_id]['stickers_count'] += 1
                    
                    bot.reply_to(message,
                        f"✅ *Стикер #{user_packs[user_id]['stickers_count']} добавлен!*\n\n"
                        f"📚 Пак: {user_data.get('pack_title', 'Мои стикеры')}\n"
                        f"📊 Всего стикеров: {user_packs[user_id]['stickers_count']}\n\n"
                        f"Продолжай добавлять стикеры! 📷",
                        parse_mode='Markdown'
                    )
            
            # Удаляем временный файл
            os.remove(temp_file)
            
        except Exception as e:
            logger.error(f"Sticker API error: {e}")
            os.remove(temp_file)
            
            if "STICKERSET_INVALID" in str(e):
                bot.reply_to(message, "❌ Ошибка создания стикерпака. Попробуй создать новый пак через '🆕 Создать стикерпак'")
            else:
                bot.reply_to(message, f"❌ Ошибка: {e}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        bot.reply_to(message, "❌ Ошибка при создании стикера")

@bot.message_handler(func=lambda message: True)
def echo(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🆕 Создать стикерпак'))
    
    bot.reply_to(message,
        "Нажми '🆕 Создать стикерпак' чтобы начать создание стикеров! 🎨",
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
    return "🤖 Telegram Sticker Pack Creator"

if __name__ == '__main__':
    print("🚀 Starting Telegram Sticker Pack Creator...")
    
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
