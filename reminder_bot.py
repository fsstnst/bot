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
import json
import os
from google.oauth2.service_account import Credentials
import gspread

# 🔒 Вшитый токен
TOKEN = "8334051228:AAFcSyean64FwsDZ7zpzad920bboUbD8gIk"

# 🕒 Время напоминаний
reminder_times = [time(10, 0), time(14, 0), time(20, 0)]
user_states = {}

# 📊 Настройка Google Sheets
def get_sheet():
    creds_json = os.environ["GOOGLE_CREDENTIALS"]
    creds_dict = json.loads(creds_json)
    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gc = gspread.authorize(credentials)
    return gc.open("Test Responses").sheet1

def log_to_sheet(user, event):
    sheet = get_sheet()
    sheet.append_row([
        user.full_name,
        f"@{user.username}" if user.username else "—",
        user.id,
        user.language_code,
        event,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ])

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Тест пройдено / Test completed", callback_data="completed")],
        [InlineKeyboardButton("⏰ Пройду пізніше / I’ll do it later", callback_data="later")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_states[user.id] = {"status": "waiting"}

    await update.message.reply_text(
        "❗️Привіт! Не забудь пройти тестування до кінця місяця: https://forms.office.com/e/76GbS3T71W\n"
        "❗️Hi! Don’t forget to complete the test by the end of the month: https://forms.office.com/e/76GbS3T71W",
        reply_markup=get_keyboard()
    )

    log_to_sheet(user, "/start")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "completed":
        user_states[user.id]["status"] = "completed"
        await query.edit_message_text("✅ Дякуємо! / Thank you for completing the test.")
        log_to_sheet(user, "✅ Пройдено")
    elif query.data == "later":
        user_states[user.id]["status"] = "later"
        await query.edit_message_text("⏰ Добре, нагадаємо пізніше. / Got it, we’ll remind you later.")
        log_to_sheet(user, "⏰ Пізніше")

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
    await app.initialize()
    await app.start()
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

