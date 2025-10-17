import os
import telebot

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🎉 Бот запущен и работает! Отправь мне фото для стикера")

@bot.message_handler(commands=['test'])
def send_test(message):
    bot.reply_to(message, "✅ Тест пройден! Бот отвечает!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "📸 Фото получено! Функция стикеров скоро будет добавлена.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Вы сказали: {message.text}")

if __name__ == '__main__':
    print("🚀 Бот запускается...")
    bot.infinity_polling()
