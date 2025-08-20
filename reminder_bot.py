import logging
import os
import json
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
from google.oauth2 import service_account

# 🔒 Вшитый токен
TOKEN = "8334051228:AAFcSyean64FwsDZ7zpzad920bboUbD8gIk"

# Настройка логов
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Настройка Google Sheets
creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = service_account.Credentials.from_service_account_info(creds_info)
gc = gspread.authorize(creds)
sheet = gc.open("Test Responses").sheet1  # первая вкладка

# Состояния пользователей и тайминги напоминаний
user_states = {}
reminder_times = [time(10, 0), time(14, 0), time(20, 0)]

# Кнопки
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Тест пройдено / Test completed", callback_data="completed")],
        [InlineKeyboardButton("⏰ Пройду пізніше / I’ll do it later", callback_data="later")]
    ])

# Логгирование в таблицу
def log_to_sheet(user, username, user_id, lang, event):
    sheet.append_row([
        user,
        f"@{username}" if username else "—",
        str(user_id),
        lang,
        event,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ])

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_states[user_id] = {"status": "waiting"}

    await update.message.reply_text(
        "❗️Привіт! Не забудь пройти тестування до кінця місяця: https://forms.office.com/e/76GbS3T71W\n"
        "❗️Hi! Don’t forget to complete the test by the end of the month: https://forms.office.com/e/76GbS3T71W",
        reply_markup=get_keyboard()
    )

    log_to_sheet(user.full_name, user.username, user.id, user.language_code, "🚀 /start")

# Обработка кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    await query.answer()

    if query.data == "completed":
        user_states[user_id]["status"] = "completed"
        await query.edit_message_text("✅ Дякуємо! / Thank you for completing the test.")
        log_to_sheet(user.full_name, user.username, user.id, user.language_code, "✅ Пройдено")
    elif query.data == "later":
        user_states[user_id]["status"] = "later"
        await query.edit_message_text("⏰ Добре, нагадаємо пізніше. / Got it, we’ll remind you later.")
        log_to_sheet(user.full_name, user.username, user.id, user.language_code, "⏰ Позже")

# Напоминания
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

# Запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    asyncio.create_task(reminder_loop(app))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
