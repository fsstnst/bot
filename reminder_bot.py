import logging
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 📌 Настройки бота
TOKEN = "8334051228:AAFcSyean64FwsDZ7zpzad920bboUbD8gIk"
SHEET_NAME = "Test Responses"
ADMIN_ID = 451971519  # больше не используется

# 📌 Время напоминаний
reminder_times = [time(7, 0), time(10, 0), time(17, 0)]

# 🧠 Хранилище состояний пользователей
user_states = {}

# 📋 Настройка Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# 🛠️ Логгер
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# 📤 Кнопки
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Тест пройдено / Test completed", callback_data="completed")],
        [InlineKeyboardButton("⏰ Пройду пізніше / I’ll do it later", callback_data="later")]
    ])

# 📝 Запись в таблицу
def log_to_sheet(user, event: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [
        user.full_name,
        f"@{user.username}" if user.username else "—",
        str(user.id),
        user.language_code,
        event,
        timestamp,
    ]
    sheet.append_row(row, value_input_option="RAW")

# 🟢 Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_states[user.id] = {"status": "waiting"}

    await update.message.reply_text(
        "❗️Привіт! Не забудь пройти тестування до кінця місяця: https://forms.office.com/e/76GbS3T71W\n"
        "❗️Hi! Don’t forget to complete the test by the end of the month: https://forms.office.com/e/76GbS3T71W",
        reply_markup=get_keyboard()
    )

    log_to_sheet(user, "🚀 /start")

# 🔘 Кнопки
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "completed":
        user_states[user_id]["status"] = "completed"
        await query.edit_message_text("✅ Дякуємо! / Thank you for completing the test.")
        log_to_sheet(query.from_user, "✅ Пройдено")
    elif query.data == "later":
        user_states[user_id]["status"] = "later"
        await query.edit_message_text("⏰ Добре, нагадаємо пізніше. / Got it, we’ll remind you later.")
        log_to_sheet(query.from_user, "⏰ Позже")

# ⏰ Напоминания
async def reminder_loop(app):
    while True:
        now = datetime.now().time()
        if any(now.hour == rt.hour and now.minute == rt.minute for rt in reminder_times):
            for user_id, state in user_states.items():
                if state["status"] in ["waiting", "later"]:
                    try:
                        await app.bot.send_message(
                            chat_id=user_id,
                            text="❗️Нагадування: не забудь пройти тест / Reminder: please complete the test\nhttps://forms.office.com/e/76GbS3T71W",
                            reply_markup=get_keyboard()
                        )
                    except Exception as e:
                        logging.warning(f"Couldn't send reminder to {user_id}: {e}")
            await asyncio.sleep(60)
        await asyncio.sleep(10)

# 🚀 Запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    asyncio.create_task(reminder_loop(app))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
