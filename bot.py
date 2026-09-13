import telebot
import threading
from datetime import datetime
from flask import Flask

BOT_TOKEN = "8968681957:AAH0gvJ2CaQxgYO5vXjMRLc6mEP_MuTAomU"
CHAT_ID = "7075975650"
SALOM_XABARI = "Xayrli tong! 🌞 Bugun ajoyib kun bo'lsin!"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, f"Salom! Sizning chat_id: {message.chat.id}")


threading.Thread(target=bot.infinity_polling, daemon=True).start()


@app.route("/send-morning-message")
def send_morning_message():
    try:
        bot.send_message(CHAT_ID, SALOM_XABARI)
        print(f"[{datetime.now()}] Xabar yuborildi: {SALOM_XABARI}")
        return "Xabar yuborildi!"
    except Exception as e:
        print(f"Xatolik: {e}")
        return f"Xatolik: {e}", 500


@app.route("/")
def home():
    return "Bot ishlayapti!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
