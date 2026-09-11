import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
DB_PATH = os.getenv("DB_PATH", "group_bot.db")

TZ = ZoneInfo("Asia/Tashkent")

QUESTIONS = [
    "Assalomu alaykum, sinfdoshlar! 😊 Bugun maktabdagi eng esda qolgan voqeangiz qaysi?",
    "Sinfdoshlar, maktab davridan kimning hazillari hali ham yodingizda? 😄",
    "87-guruhni eslab ko‘raylik: maktabdagi eng sevimli ustozingiz kim edi?",
    "Kim maktab davriga bir kunga qaytishni xohlardi? Nega? 😊",
    "Sinfdoshlar, guruhimizdagi eng davrakash odam kim deb o‘ylaysiz? 😄",
]

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS activity("
            "user_id INTEGER PRIMARY KEY,"
            "name TEXT,"
            "count INTEGER DEFAULT 0)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS birthdays("
            "user_id INTEGER PRIMARY KEY,"
            "name TEXT,"
            "month INTEGER,"
            "day INTEGER)"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum, sinfdoshlar! 😊\n\n"
        "Men Sinfdoshlar davrasini jonlantirish uchun yordamchi botman.\n\n"
        "/savol — suhbat savoli\n"
        "/faollar — TOP-3 faol sinfdosh\n"
        "/tugilgan KUN OY — tug‘ilgan kunni saqlash\n"
        "Masalan: /tugilgan 15 8"
    )

async def question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = datetime.now(TZ).timetuple().tm_yday % len(QUESTIONS)
    await update.message.reply_text(QUESTIONS[index])

async def active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with sqlite3.connect(DB_PATH) as c:
        rows = c.execute(
            "SELECT name, count FROM activity "
            "ORDER BY count DESC, name ASC LIMIT 3"
        ).fetchall()

    if not rows:
        await update.message.reply_text(
            "Hali faollik statistikasi yig‘ilmadi 😊"
        )
        return

    text = "🏆 TOP-3 faol sinfdoshlar:\n"
    text += "\n".join(
        f"{i}. {name} — {count} ta xabar"
        for i, (name, count) in enumerate(rows, 1)
    )
    await update.message.reply_text(text)

async def birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text(
            "Masalan: /tugilgan 15 8"
        )
        return

    try:
        day, month = map(int, context.args)
        datetime(2024, month, day)
    except (ValueError, TypeError):
        await update.message.reply_text(
            "Sana noto‘g‘ri. Masalan: /tugilgan 15 8"
        )
        return

    user = update.effective_user

    with sqlite3.connect(DB_PATH) as c:
        c.execute(
            "INSERT OR REPLACE INTO birthdays"
            "(user_id, name, month, day) VALUES (?, ?, ?, ?)",
            (user.id, user.full_name, month, day),
        )

    await update.message.reply_text(
        f"Rahmat, {user.full_name}! 🎉 Tug‘ilgan kuningiz saqlandi."
    )

async def count_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return

    user = update.effective_user

    with sqlite3.connect(DB_PATH) as c:
        c.execute(
            "INSERT INTO activity(user_id, name, count) "
            "VALUES (?, ?, 1) "
            "ON CONFLICT(user_id) DO UPDATE SET "
            "name=excluded.name, count=count+1",
            (user.id, user.full_name),
        )

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Sinfdoshlar bot ishlayapti! ✅"
    )

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi")

    if not BASE_URL:
        raise RuntimeError("RENDER_EXTERNAL_URL topilmadi")

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("savol", question))
    app.add_handler(CommandHandler("faollar", active))
    app.add_handler(CommandHandler("tugilgan", birthday))
    app.add_handler(CommandHandler("health", health))

    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            count_message
        )
    )

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="telegram",
        webhook_url=f"{BASE_URL}/telegram",
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
