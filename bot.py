import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Проверяем токен
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("Токен бота не найден!")
    exit(1)

logger.info("Токен бота найден, запускаем...")

try:
    from aiogram import Bot, Dispatcher, types, executor
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher(bot)
    
    logger.info("Aiogram успешно импортирован")
    
except ImportError as e:
    logger.error(f"Ошибка импорта: {e}")
    exit(1)

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("🎉 Бот запущен и работает! Отправь мне фото")

@dp.message_handler(commands=['test'])
async def test_cmd(message: types.Message):
    await message.answer("✅ Бот отвечает! Все работает отлично!")

@dp.message_handler(content_types=['photo'])
async def handle_photo(message: types.Message):
    await message.answer("📸 Фото получено! Функция стикеров скоро будет добавлена.")

@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(f"Вы написали: {message.text}")

if __name__ == '__main__':
    logger.info("Запуск бота...")
    executor.start_polling(dp, skip_updates=True)
