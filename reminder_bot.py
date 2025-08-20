import logging
import asyncio
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 🔒 Токен Telegram и ID админа
TOKEN = "8334051228:AAFcSyean64FwsDZ7zpzad920bboUbD8gIk"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

user_states = {}
reminder_times = [time(7, 0), time(10, 0), time(17, 0)]


def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Тест пройдено / Test completed", callback_data="completed")],
        [InlineKeyboardButton("⏰ Пройду пізніше / I’ll do it later", callback_data="later")]
    ])


def log_to_sheet(name, username, user_id, lang, status):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Test Responses").sheet1
    sheet.append_row([
        name,
        username if username else "—",
        str(user_id),
        lang if lang else "—",
        status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_states[user_id] = {"status": "waiting"}

    await update.message.reply_text(
        "❗️Привіт! Не забудь пройти тестування до кінця місяця: https://forms.office.com/e/76GbS3T71W\n"
        "❗️Hi! Don’t forget to complete the test by the end of the month: https://forms.office.com/e/76GbS3T71W",
        reply_markup=get_keyboard()
    )

    log_to_sheet(user.full_name, user.username, user.id, user.language_code, "🚀 Старт")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    await query.answer()

    if query.data == "completed":
        user_states[user_id]["status"] = "completed"
        await query.edit_message_text("✅ Дякуємо! / Thank you for completing the test.")
        log_to_sheet(user.full_name, user.username, user_id, user.language_code, "✅ Пройдено")
    elif query.data == "later":
        user_states[user_id]["status"] = "later"
        await query.edit_message_text("⏰ Добре, нагадаємо пізніше. / Got it, we’ll remind you later.")
        log_to_sheet(user.full_name, user.username, user_id, user.language_code, "⏰ Позже")


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


async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    asyncio.create_task(reminder_loop(app))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()


if __name__ == "__main__":
    asyncio.run(main())
