import os
import logging

# Базовая настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("❌ Токен бота не найден!")
        return
    
    logger.info("✅ Токен найден, пробуем импортировать aiogram...")
    
    try:
        from aiogram import Bot, Dispatcher, types, executor
        
        bot = Bot(token=TOKEN)
        dp = Dispatcher(bot)
        logger.info("✅ Aiogram успешно загружен!")
        
        @dp.message_handler(commands=['start'])
        async def start_handler(message: types.Message):
            await message.answer("🎉 Бот работает! Отправь /test")
            
        @dp.message_handler(commands=['test'])
        async def test_handler(message: types.Message):
            await message.answer("✅ Тест пройден! Бот отвечает!")
            
        @dp.message_handler()
        async def echo_handler(message: types.Message):
            await message.answer(f"Эхо: {message.text}")
        
        logger.info("🚀 Запускаем бота...")
        executor.start_polling(dp, skip_updates=True)
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        logger.info("Попробуйте использовать python-telegram-bot вместо aiogram")

if __name__ == '__main__':
    main()
