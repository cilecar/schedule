from email import message

from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import ADMIN_ID
from database.db import add_user, load_user_settings, save_user_settings, load_users
from keyboards.reply import main_keyboard
from services.logger import log_action, logger

# Создаем роутер
router = Router()


# Состояния для администратора
class AdminState(StatesGroup):
    sending_global_message = State()
    waiting_for_lesson_link = State()


@router.message(Command("start"))
async def start(message: types.Message):
    add_user(message.from_user.id)
    user_id = message.from_user.id
    settings = load_user_settings(user_id)

    response = "Приветственное сообщение отправлено"
    log_action(message.from_user.id, "Запуск команды /start", response)

    if settings == {
        "notifications_enabled": True,
        "notification_time": "20:00",
        "deadline_notifications_enabled": True,
        "deadline_notification_time": "12:00"
    }:
        settings = {
            "notifications_enabled": True,
            "notification_time": "14:00",
            "deadline_notifications_enabled": True,
            "deadline_notification_time": "12:00"
        }
        save_user_settings(user_id, settings)

    welcome_message = (
        "Привет! Я бот, который поможет тебе с расписанием и домашними заданиями.\n\n"
        "Вот что я умею:\n"
        "1. 📅 Расписание на сегодня - показывает расписание на текущий день.\n"
        "2. 📆 Расписание на завтра - показывает расписание на следующий день.\n"
        "3. 📖 Полное расписание - показывает полное расписание на обе недели.\n"
        "4. 📝 Добавить домашнее задание - позволяет добавить новое домашнее задание.\n"
        "5. 📚 Посмотреть домашние задания - показывает список всех домашних заданий.\n"
        "6. ✏️ Изменить статус задания - позволяет изменить статус домашнего задания (выполнено/не выполнено/удалить).\n"
        "7. ⚙️ Настройки - позволяет настроить уведомления и отображение выполненных заданий.\n\n"
        "Если вы нашли баг или ошибку, сообщите администратору - @cilecar"
    )
    await message.answer(welcome_message, reply_markup=main_keyboard)


@router.message(Command("send_global_message"))
async def send_global_message(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    await message.answer("Введите сообщение для отправки всем пользователям:")
    await state.set_state(AdminState.sending_global_message)

    response = "Глобальное сообщение"
    log_action(message.from_user.id, "Попытка отправки глобального сообщения", response)


@router.message(AdminState.sending_global_message)
async def process_global_message(message: types.Message, state: FSMContext, bot: Bot):
    global_message = message.text.strip()
    formatted_message = f"❗️Сообщение от администратора❗️\n\n{global_message}"
    users = load_users()

    for uid in users:
        try:
            await bot.send_message(uid, formatted_message)
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение пользователю {uid}: {e}")

    await state.clear()
    await message.answer("Сообщение отправлено всем пользователям.")


@router.message(AdminState.waiting_for_lesson_link)
async def process_lesson_link(message: types.Message, state: FSMContext, bot: Bot):
    if message.text and message.text.lower() in ["отмена", "🚫 отмена"]:
        await state.clear()
        await message.answer("Отправка ссылки отменена.", reply_markup=main_keyboard)
        return

    link = message.text or message.caption or "Без текста"
    data = await state.get_data()

    subject = data.get("lesson_subject", "Неизвестный предмет")
    time_range = data.get("lesson_time", "Неизвестное время")

    formatted_message = f"❗️Ссылка на пару❗️\n\nПредмет: {subject}\nВремя: {time_range}\nСсылка: {link}"

    admin_id = message.from_user.id
    users = load_users()

    # Рассылаем всем, КРОМЕ админа
    for uid in users:
        if uid == admin_id:
            continue
        try:
            await bot.send_message(uid, formatted_message)
        except Exception:
            pass

    await state.clear()
    
    # Отправляем админу ту же рассылку, но ЖЕСТКО цепляем главную клавиатуру
    await message.answer(formatted_message, reply_markup=main_keyboard)
    # И отправляем подтверждение
    await message.answer("✅ Ссылка успешно отправлена всем пользователям!")