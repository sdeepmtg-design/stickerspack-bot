import os
import io
import logging
import requests
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from PIL import Image, ImageFilter, ImageEnhance, ImageOps

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
            [KeyboardButton("🌈 Яркий контур"), KeyboardButton("📐 Геометрический")],
            [KeyboardButton("🎯 Ч/Б контур"), KeyboardButton("🔥 Винтажный")]
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
        "🎨 Мультяшный - делает изображение как мультфильм\n"
        "👾 Пиксель-арт - превращает в пиксельную графику\n"
        "🌈 Яркий контур - добавляет яркие контуры\n"
        "📐 Геометрический - упрощает до геометрических форм\n"
        "🎯 Ч/Б контур - создает черно-белый контурный рисунок\n"
        "🔥 Винтажный - добавляет старинный эффект"
    )

@dp.message_handler(lambda message: message.text in [
    "🎨 Мультяшный", "🌈 Яркий контур", "👾 Пиксель-арт", 
    "📐 Геометрический", "🎯 Ч/Б контур", "🔥 Винтажный"
])
async def choose_style(message: Message, state: FSMContext):
    style_map = {
        "🎨 Мультяшный": "cartoon", 
        "🌈 Яркий контур": "outline",
        "👾 Пиксель-арт": "pixel",
        "📐 Геометрический": "geometric",
        "🎯 Ч/Б контур": "bw_sketch",
        "🔥 Винтажный": "vintage"
    }
    
    await state.update_data(style=style_map[message.text])
    await StickerStates.waiting_for_photo.set()
    await message.answer("Отлично! Теперь отправь мне фото 📷")

@dp.message_handler(content_types=['photo'], state=StickerStates.waiting_for_photo)
async def process_photo_with_style(message: Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        selected_style = user_data.get('style', 'cartoon')
        
        await message.answer("🔄 Обрабатываю изображение...")
        
        # Скачиваем фото
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        downloaded_file = await bot.download_file(file.file_path)
        
        # Обрабатываем изображение
        input_image = Image.open(io.BytesIO(downloaded_file.getvalue())).convert('RGB')
        
        # Применяем выбранный стиль
        if selected_style == 'cartoon':
            output_image = apply_cartoon_style(input_image)
        elif selected_style == 'outline':
            output_image = apply_outline_style(input_image)
        elif selected_style == 'pixel':
            output_image = apply_pixel_style(input_image)
        elif selected_style == 'geometric':
            output_image = apply_geometric_style(input_image)
        elif selected_style == 'bw_sketch':
            output_image = apply_bw_sketch_style(input_image)
        elif selected_style == 'vintage':
            output_image = apply_vintage_style(input_image)
        
        # Конвертируем в PNG для стикера
        output_bytes = io.BytesIO()
        
        # Создаем изображение с прозрачным фоном
        if output_image.mode != 'RGBA':
            output_image = output_image.convert('RGBA')
            
        # Упрощаем фон для лучшего результата
        output_image = make_background_transparent(output_image)
        
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
def make_background_transparent(image):
    """Упрощенное удаление фона - делает белый и светлые цвета прозрачными"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    datas = image.getdata()
    new_data = []
    
    for item in datas:
        # Делаем белый и светлые цвета прозрачными
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    
    image.putdata(new_data)
    return image

def apply_cartoon_style(image):
    """Мультяшный стиль"""
    # Увеличиваем насыщенность
    enhancer = ImageEnhance.Color(image)
    saturated = enhancer.enhance(1.5)
    
    # Добавляем легкое размытие
    cartoon = saturated.filter(ImageFilter.SMOOTH_MORE)
    
    # Увеличиваем контраст
    contrast_enhancer = ImageEnhance.Contrast(cartoon)
    result = contrast_enhancer.enhance(1.2)
    
    return result

def apply_outline_style(image):
    """Стиль с яркими контурами"""
    # Находим края
    edges = image.filter(ImageFilter.FIND_EDGES)
    
    # Увеличиваем контраст краев
    enhancer = ImageEnhance.Contrast(edges)
    strong_edges = enhancer.enhance(3.0)
    
    # Накладываем края на оригинал
    result = Image.blend(image, strong_edges, 0.2)
    
    return result

def apply_pixel_style(image):
    """Пиксель-арт стиль"""
    # Уменьшаем разрешение
    small_size = (64, 64)
    pixelated = image.resize(small_size, Image.NEAREST)
    
    # Возвращаем к исходному размеру
    result = pixelated.resize(image.size, Image.NEAREST)
    
    return result

def apply_geometric_style(image):
    """Геометрический стиль"""
    # Упрощаем изображение через постернизацию
    simplified = image.convert('P', palette=Image.ADAPTIVE, colors=6)
    result = simplified.convert('RGB')
    
    return result

def apply_bw_sketch_style(image):
    """Черно-белый контурный стиль"""
    # Конвертируем в градации серого
    gray = image.convert('L')
    
    # Находим края
    edges = gray.filter(ImageFilter.FIND_EDGES)
    
    # Инвертируем (черные линии на белом фоне)
    inverted = Image.eval(edges, lambda x: 255 - x)
    
    return inverted.convert('RGB')

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
    
    # Добавляем шум
    result = sepia.filter(ImageFilter.GaussianBlur(0.5))
    
    return result

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
