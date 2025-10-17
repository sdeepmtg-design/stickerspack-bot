import os
import io
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from PIL import Image, ImageFilter, ImageEnhance

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not API_TOKEN:
    raise ValueError("Не установлен TELEGRAM_BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Состояния бота
class StickerStates(StatesGroup):
    waiting_for_photo = State()

# Клавиатура с выбором стилей
def get_style_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("🎨 Мультяшный"), KeyboardButton("👾 Пиксель-арт")],
            [KeyboardButton("🌈 Контуры"), KeyboardButton("🔥 Винтажный")]
        ],
        resize_keyboard=True
    )

@dp.message_handler(commands=['start'])
async def start_command(message: Message):
    await message.answer(
        "🎨 Привет! Я бот для создания стикеров!\n\n"
        "Выбери стиль и отправь мне фото:",
        reply_markup=get_style_keyboard()
    )

@dp.message_handler(commands=['help'])
async def help_command(message: Message):
    await message.answer(
        "🤖 Как использовать:\n"
        "1. Выбери стиль из меню\n" 
        "2. Отправь фото\n"
        "3. Получи стикер!\n\n"
        "Стили:\n"
        "🎨 Мультяшный - яркие цвета\n"
        "👾 Пиксель-арт - ретро стиль\n"
        "🌈 Контуры - выделяет края\n"
        "🔥 Винтажный - старинный эффект"
    )

@dp.message_handler(lambda message: message.text in ["🎨 Мультяшный", "👾 Пиксель-арт", "🌈 Контуры", "🔥 Винтажный"])
async def choose_style(message: Message, state: FSMContext):
    style_map = {
        "🎨 Мультяшный": "cartoon", 
        "👾 Пиксель-арт": "pixel",
        "🌈 Контуры": "outline", 
        "🔥 Винтажный": "vintage"
    }
    
    await state.update_data(style=style_map[message.text])
    await StickerStates.waiting_for_photo.set()
    await message.answer("Отлично! Теперь отправь мне фото 📷")

@dp.message_handler(content_types=['photo'], state=StickerStates.waiting_for_photo)
async def process_photo(message: Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        selected_style = user_data.get('style', 'cartoon')
        
        await message.answer("🔄 Обрабатываю...")
        
        # Скачиваем фото
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        downloaded_file = await bot.download_file(file.file_path)
        
        # Открываем изображение
        image = Image.open(io.BytesIO(downloaded_file.getvalue())).convert('RGB')
        
        # Применяем стиль
        if selected_style == 'cartoon':
            result = apply_cartoon(image)
        elif selected_style == 'pixel':
            result = apply_pixel(image)
        elif selected_style == 'outline':
            result = apply_outline(image)
        elif selected_style == 'vintage':
            result = apply_vintage(image)
        
        # Конвертируем в PNG
        output = io.BytesIO()
        result.save(output, format='PNG')
        output.seek(0)
        
        await message.reply_document(
            document=types.InputFile(output, filename='sticker.png'),
            caption=f"✅ Готово! Стиль: {selected_style}"
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.answer("❌ Ошибка. Попробуйте другое фото.")
    finally:
        await state.finish()

@dp.message_handler(content_types=['photo'])
async def photo_without_style(message: Message):
    await message.answer("⚠️ Сначала выбери стиль!", reply_markup=get_style_keyboard())

# Простые функции обработки
def apply_cartoon(img):
    enhancer = ImageEnhance.Color(img)
    return enhancer.enhance(1.3)

def apply_pixel(img):
    small = img.resize((100, 100), Image.NEAREST)
    return small.resize(img.size, Image.NEAREST)

def apply_outline(img):
    return img.filter(ImageFilter.EDGE_ENHANCE)

def apply_vintage(img):
    # Простой винтажный эффект - затемнение
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(0.8)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
