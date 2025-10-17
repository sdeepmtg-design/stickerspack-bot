import os
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not API_TOKEN:
    raise ValueError("Не установлен TELEGRAM_BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Клавиатура
def get_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("🎨 Создать стикер"), KeyboardButton("ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer(
        "🎨 Привет! Я бот для создания стикеров.\n\n"
        "Отправь мне фото и я помогу сделать из него стикер!",
        reply_markup=get_keyboard()
    )

@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.answer(
        "🤖 Как использовать бота:\n\n"
        "1. Отправь мне любое фото\n"
        "2. Я обработаю его\n"
        "3. Ты получишь готовый PNG файл\n\n"
        "Пока что я просто сохраняю фото. Скоро добавлю обработку!",
        reply_markup=get_keyboard()
    )

@dp.message_handler(lambda message: message.text == "🎨 Создать стикер")
async def create_sticker(message: types.Message):
    await message.answer("Отправь мне фото для создания стикера! 📷")

@dp.message_handler(lambda message: message.text == "ℹ️ Помощь")
async def show_help(message: types.Message):
    await help_command(message)

@dp.message_handler(content_types=['photo'])
async def handle_photo(message: types.Message):
    try:
        await message.answer("🔄 Обрабатываю фото...")
        
        # Просто сохраняем информацию о фото
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        
        await message.answer(
            f"✅ Фото получено!\n"
            f"Размер: {photo.width}x{photo.height}\n"
            f"ID файла: {file_info.file_id}\n\n"
            f"Скоро здесь будет настоящая обработка стикеров! 🎨"
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.answer("❌ Произошла ошибка при обработке фото")

@dp.message_handler()
async def echo_message(message: types.Message):
    await message.answer(
        "Отправь мне фото для создания стикера или используй кнопки ниже!",
        reply_markup=get_keyboard()
    )

if __name__ == '__main__':
    logger.info("Бот запускается...")
    executor.start_polling(dp, skip_updates=True)
