from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, JobQueue
import datetime

ADMIN_ID = 451971519
agents = {}
test_link = "https://forms.office.com/e/76GbS3T71W"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    agents[user_id] = {"remind": True, "job": None, "chat_id": chat_id, "responded": False}
    await send_test_reminder(update, context)

async def send_test_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("✅ Тест пройдено / Test completed", callback_data="done")
        ],
        [
            InlineKeyboardButton("⏰ Пройду пізніше / I’ll do it later", callback_data="later")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"❗️Привіт! Не забудь пройти тестування до кінця місяця: {test_link}\n❗️Hi! Don’t forget to complete the test by the end of the month: {test_link}",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    full_name = query.from_user.full_name
    agents[user_id]["responded"] = True

    if query.data == "done":
        agents[user_id]["remind"] = False
        if agents[user_id]["job"]:
            agents[user_id]["job"].schedule_removal()
        await query.edit_message_text("✅ Дякую! / Thank you! Тест пройдено.")

        with open("done.txt", "a") as f:
            f.write(f"{full_name} (ID: {user_id}) пройшов(ла) тест\n")

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"✅ Агент {full_name} (ID: {user_id}) повідомив, що пройшов(ла) тест!"
        )

    elif query.data == "later":
        await query.edit_message_text("⏰ Добре, нагадаю пізніше / I’ll remind you later.")
        schedule_daily_reminder(context.job_queue, user_id, query.message.chat_id)


def schedule_daily_reminder(job_queue: JobQueue, user_id: int, chat_id: int):
    if agents[user_id]["job"]:
        agents[user_id]["job"].schedule_removal()

    job = job_queue.run_daily(
        lambda ctx: send_daily_if_needed(ctx, user_id),
        time=datetime.time(hour=10, minute=0)
    )
    agents[user_id]["job"] = job

async def send_daily_if_needed(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    if agents.get(user_id, {}).get("remind") and not agents[user_id].get("responded"):
        chat_id = agents[user_id]["chat_id"]
        keyboard = [
            [
                InlineKeyboardButton("✅ Тест пройдено / Test completed", callback_data="done")
            ],
            [
                InlineKeyboardButton("⏰ Пройду пізніше / I’ll do it later", callback_data="later")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❗️Привіт! Не забудь пройти тестування до кінця місяця: {test_link}\n❗️Hi! Don’t forget to complete the test by the end of the month: {test_link}",
            reply_markup=reply_markup
        )

if __name__ == '__main__':
    app = ApplicationBuilder().token("8334051228:AAFcSyean64FwsDZ7zpzad920bboUbD8gIk").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

