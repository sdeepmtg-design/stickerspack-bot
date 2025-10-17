import os
import logging
from aiogram import Bot, Dispatcher, types, executor

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет! Я бот для стикеров. Отправь мне фото!")

@dp.message_handler(content_types=['photo'])
async def handle_photo(message: types.Message):
    await message.answer("Фото получено! Скоро добавлю обработку стикеров.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
