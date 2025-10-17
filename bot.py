import os
import telebot
from flask import Flask
import threading

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Создаем Flask приложение для порта
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Bot is running!"

@app.route('/health')
def health():
    return "✅ OK"

# Обработчики бота
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎉 Бот запущен! Отправь мне фото для создания стикера")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "📸 Отправь фото - я сделаю из него стикер!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "📸 Фото получено! Обрабатываю... Скоро здесь будут стикеры!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Для создания стикера отправь мне фото 📷")

def run_bot():
    """Запускает бота в отдельном потоке"""
    print("🤖 Starting Telegram bot...")
    bot.infinity_polling()

def run_web():
    """Запускает веб-сервер"""
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Starting web server on port {port}...")
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    print("🚀 Starting application...")
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем веб-сервер в основном потоке
    run_web()
