import os
import io
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from rembg import remove
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
            [KeyboardButton("⚪ Просто без фона"), KeyboardButton("🎨 Мультяшный")],
            [KeyboardButton("🌈 Яркий контур"), KeyboardButton("👾 Пиксель-арт")],
            [KeyboardButton("📐 Геометрический"), KeyboardButton("🎯 Ч/Б контур")]
        ],
        resize_keyboard=True
    )

@dp.message_handler(commands=['start'])
async def start_command(message: Message):
    await message.answer(
        "🎨 Привет! Я бот для создания стикеров с разными стилями!\n\n"
        "Выбери стиль обработки и отправь мне фото:",
        reply_markup=get_style_keyboard()
    )

@dp.message_handler(commands=['help'])
async def help_command(message: Message):
    await message.answer(
        "🤖 Как использовать бота:\n\n"
        "1. Выбери стиль из меню\n"
        "2. Отправь фото или картинку\n"
        "3. Получи готовый стикер!\n\n"
        "Доступные стили:\n"
        "⚪ Просто без фона - убирает фон\n"
        "🎨 Мультяшный - делает изображение как мультфильм\n"
        "🌈 Яркий контур - добавляет яркие контуры\n"
        "👾 Пиксель-арт - превращает в пиксельную графику\n"
        "📐 Геометрический - упрощает до геометрических форм\n"
        "🎯 Ч/Б контур - создает черно-белый контурный рисунок"
    )

@dp.message_handler(lambda message: message.text in [
    "⚪ Просто без фона", "🎨 Мультяшный", "🌈 Яркий контур", 
    "👾 Пиксель-арт", "📐 Геометрический", "🎯 Ч/Б контур"
])
async def choose_style(message: Message, state: FSMContext):
    style_map = {
        "⚪ Просто без фона": "no_bg",
        "🎨 Мультяшный": "cartoon", 
        "🌈 Яркий контур": "outline",
        "👾 Пиксель-арт": "pixel",
        "📐 Геометрический": "geometric",
        "🎯 Ч/Б контур": "bw_sketch"
    }
    
    await state.update_data(style=style_map[message.text])
    await StickerStates.waiting_for_photo.set()
    await message.answer("Отлично! Теперь отправь мне фото 📷")

@dp.message_handler(content_types=['photo'], state=StickerStates.waiting_for_photo)
async def process_photo_with_style(message: Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        selected_style = user_data.get('style', 'no_bg')
        
        await message.answer("🔄 Обрабатываю изображение...")
        
        # Скачиваем фото
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        downloaded_file = await bot.download_file(file.file_path)
        
        # Обрабатываем изображение
        input_image = Image.open(io.BytesIO(downloaded_file.getvalue())).convert('RGB')
        
        # Применяем выбранный стиль
        if selected_style == 'no_bg':
            output_image = apply_no_background(input_image)
        elif selected_style == 'cartoon':
            output_image = apply_cartoon_style(input_image)
        elif selected_style == 'outline':
            output_image = apply_outline_style(input_image)
        elif selected_style == 'pixel':
            output_image = apply_pixel_style(input_image)
        elif selected_style == 'geometric':
            output_image = apply_geometric_style(input_image)
        elif selected_style == 'bw_sketch':
            output_image = apply_bw_sketch_style(input_image)
        
        # Конвертируем в PNG для стикера
        output_bytes = io.BytesIO()
        output_image.save(output_bytes, format='PNG', optimize=True)
        output_bytes.seek(0)
        
        # Отправляем результат
        await message.reply_document(
            document=types.InputFile(output_bytes, filename='sticker.png'),
            caption=f"✅ Готово! Стиль: {selected_style}"
        )
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await message.answer("❌ Произошла ошибка при обработке. Попробуйте другую фотографию.")
    
    finally:
        await state.finish()

@dp.message_handler(content_types=['photo'])
async def process_photo_without_style(message: Message):
    await message.answer("⚠️ Сначала выбери стиль из меню ниже!", reply_markup=get_style_keyboard())

# Функции обработки стилей
def apply_no_background(image):
    """Просто удаляет фон"""
    return remove(image)

def apply_cartoon_style(image):
    """Мультяшный стиль"""
    # Сначала удаляем фон
    no_bg = remove(image)
    
    # Увеличиваем насыщенность
    enhancer = ImageEnhance.Color(no_bg)
    saturated = enhancer.enhance(1.3)
    
    # Добавляем легкое размытие для мультяшного эффекта
    cartoon = saturated.filter(ImageFilter.SMOOTH_MORE)
    
    return cartoon

def apply_outline_style(image):
    """Стиль с яркими контурами"""
    no_bg = remove(image)
    
    # Находим края
    edges = no_bg.filter(ImageFilter.FIND_EDGES)
    
    # Увеличиваем контраст краев
    enhancer = ImageEnhance.Contrast(edges)
    strong_edges = enhancer.enhance(3.0)
    
    # Накладываем края на оригинал
    result = Image.blend(no_bg, strong_edges, 0.3)
    
    return result

def apply_pixel_style(image):
    """Пиксель-арт стиль"""
    no_bg = remove(image)
    
    # Уменьшаем разрешение
    small_size = (128, 128)
    pixelated = no_bg.resize(small_size, Image.NEAREST)
    
    # Возвращаем к исходному размеру
    result = pixelated.resize(no_bg.size, Image.NEAREST)
    
    return result

def apply_geometric_style(image):
    """Геометрический стиль"""
    no_bg = remove(image)
    
    # Упрощаем изображение через постернизацию
    simplified = no_bg.convert('P', palette=Image.ADAPTIVE, colors=8)
    result = simplified.convert('RGB')
    
    return result

def apply_bw_sketch_style(image):
    """Черно-белый контурный стиль"""
    no_bg = remove(image)
    
    # Конвертируем в градации серого
    gray = no_bg.convert('L')
    
    # Находим края
    edges = gray.filter(ImageFilter.FIND_EDGES)
    
    # Инвертируем (черные линии на белом фоне)
    inverted = Image.eval(edges, lambda x: 255 - x)
    
    return inverted.convert('RGB')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
