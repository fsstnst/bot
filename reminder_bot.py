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
from google.oauth2.service_account import Credentials

# Google Sheets auth
creds_json = {
  "type": "service_account",
  "project_id": "test-responses-469611",
  "private_key_id": "f68f93bc77f4a340e717d525b32c798b4df1c91f",
  "private_key": """-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDMZOPScAj0UaAD\naIPC4+410oCXfk5FW4y9x30klAFKVCOGGBRtEInEqrw+moGZZK/it88C03Bbd4JT\n3GeWcYOTInxOg2o0y4UsO6dE1fD6sjsG8bHKXb40UQXbdNXudCfETLzD8bfnNsE2\nPzUcqnCx0dDTx/OB6KXNs2tyAIb9FS5VMGtSz0ZBveAZx0VvqLDzD5gmsMsxOdjo\nhrvhjx2Y7vu71AJYzq1lpl4wd8GcfP7XxnAFHCJNk9z5aKlFeaesaSKuY348ML/0\nwq1swK5cXBxRym/tiBYFe7OyBZnzchdMKyA3xJhGt8yTh5evwyT0ixt+jOaVInlO\nSNnnCgD7AgMBAAECggEAAJvM2zh+OECn96gSEklYxu7FEOQsFlS938zyrtL6twtS\nu1r7woGyR6O7i8y8A9rFece5QDa5KKmu5RS/3abfPGcjyMZiPPQgLs6sqha/Jrk5\n0MS83e0Ch/8RXVZCbEDNXjsLYjR1OouOxcLWii/4nQMXqcoXFiWtsTAWKFr2U51s\noNCYLk80wjyJdcO1QzdclefvXMATjv3UoZoiT8pTC9YMPyiHBX0YoNofSiURxXnT\nNzX8bugbzN+A03kVm67BJLmqBFNwuN0emw4XYDwmbqEwm0ULot8uzK8F7scVtmyB\np7k8Yyn6vQjNLMGlTapccoPaTJdP2itvmQX/TDa+oQKBgQDokHR9Fbd42u26Xuca\nnFO2a84wlsFEOOVfZF8cJmXqJxXKDs9WL1/jPXKf/K447661UG7uGJ7MpZNNiYnB\nvrjwf+t6d0Frbu26SGvwSo4Y/FnhJxoOypgNkRfEIrgOWbmAdOsqqqVUrse9MXmF\nVvwGxAV19LfDxk7LTRyoD7laGwKBgQDg/bf5b+E3r8kRXiQ34tvqg2yN8Nvj0H1F\nO/6YuE5iVKCl+pxGBiwtKrUDaGUTQUM9OoQUau0SP/B6UhqDwwsXTwJxUCraOm8k\nMdA0UpkVmS2AfKpqbZxs23lnH49wzPAirIVDtpGNQB7ohyd4SpPOgtRJx9f3HsnN\n/TDqfI5ioQKBgDz40nGQ5f87dqQsCW8CmTf0X6SBgb3/JLOzvvPEZWfUQ3QsGdPA\nq+UJ0Sl8t7iZrjY/FjY6IjgJGOt1Kbav6BC1mOkMpwwhkxYJsrLW+RY34uCSvdQu\n7VpxNcfoSlUI1QeGn7kZ8CqZgChr9i4tNfoYHk5kkGE1dqb6Wo79QF0NAoGANSdb\n3n8zCw/phcPi9J0Q7Y+NBt+fY2vvHHs3A+ePBSYPKgdSAi0VJLqRNzPjpS/m7cE0\nUQqN5aDbdFqPTw+2QBR3dEPHS/VAKqHmGWZmKjcdC9zn+erZaNJVFSrcnX6dQOPX\nPA8WxfMfGjpL9dxQnRpFgwTGnehVLughNVSl4uECgYEAwbg15MKYnyv52zeeVqxk\ntfAqZJLWbLse7wf0UjpOp+oaub1bR88ShAxDkFJShst6sy0MrINS3nsOn8izI3/K\nq+3shnk0+DemJqOH4qFI874caHbYFApcMtsVlw6twK3PjMp2/IhAzX6rA8ofvSBF\nxXjDbCNKW4DBc+quJ5wrlJw=\n-----END PRIVATE KEY-----""",
  "client_email": "sheet-bot@test-responses-469611.iam.gserviceaccount.com",
  "client_id": "109563862816569863845",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/sheet-bot@test-responses-469611.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

creds = Credentials.from_service_account_info(
    creds_json,
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)
gc = gspread.authorize(creds)
sheet = gc.open("Test Responses").sheet1

# Telegram
TOKEN = "8334051228:AAFcSyean64FwsDZ7zpzad920bboUbD8gIk"
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

user_states = {}
reminder_times = [time(7, 0), time(10, 0), time(15, 20)]

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Тест пройдено / Test completed", callback_data="completed")],
        [InlineKeyboardButton("⏰ Пройду пізніше / I’ll do it later", callback_data="later")]
    ])

def log_to_sheet(name, username, user_id, lang, event):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([name, username, str(user_id), lang, event, timestamp])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_states[user.id] = {"status": "waiting"}
    log_to_sheet(user.full_name, user.username or "—", user.id, user.language_code, "▶️ /start")
    await update.message.reply_text(
        "❗️Привіт! Не забудь пройти тестування до кінця місяця: https://forms.office.com/e/aVbZuhXAL7"
        "❗️Hi! Don’t forget to complete the test by the end of the month: https://forms.office.com/e/AhcuUbisgu",
        reply_markup=get_keyboard()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "completed":
        user_states[user.id]["status"] = "completed"
        log_to_sheet(user.full_name, user.username or "—", user.id, user.language_code, "✅ Пройдено")
        await query.edit_message_text("✅ Дякуємо! / Thank you for completing the test.")
    elif query.data == "later":
        user_states[user.id]["status"] = "later"
        log_to_sheet(user.full_name, user.username or "—", user.id, user.language_code, "⏰ Позже")
        await query.edit_message_text("⏰ Добре, нагадаємо пізніше. / Got it, we’ll remind you later.")

async def reminder_loop(app):
    while True:
        now = datetime.now().time()
        if any(now.hour == rt.hour and now.minute == rt.minute for rt in reminder_times):
            for user_id, state in user_states.items():
                if state["status"] in ["waiting", "later"]:
                    try:
                        await app.bot.send_message(
                            chat_id=user_id,
                            text="❗️Нагадування: не забудь пройти тест https://forms.office.com/e/aVbZuhXAL7 / Reminder: please complete the test\nhttps://forms.office.com/e/AhcuUbisgu",
                            reply_markup=get_keyboard()
                        )
                    except Exception as e:
                        logging.warning(f"Couldn't send reminder to {user_id}: {e}")
            await asyncio.sleep(60)
        await asyncio.sleep(10)

async def main_wrapper():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    asyncio.create_task(reminder_loop(app))
    await app.run_polling()
    
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main_wrapper())
