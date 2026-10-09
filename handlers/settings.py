from datetime import datetime
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from database.db import load_user_settings, save_user_settings
from keyboards.inline import get_settings_keyboard
from services.logger import log_action

router = Router()

class SettingsState(StatesGroup):
    changing_time = State()
    changing_deadline_time = State()

@router.message(F.text == "⚙️ Настройки")
async def notification_settings(message: types.Message):
    user_id = message.from_user.id
    settings = load_user_settings(user_id)

    hide_status = "выключено (задания скрыты)" if settings.get("hide_completed_tasks", False) else "включено (задания показываются)"
    notifications_status = "включено" if settings.get("notifications_enabled", True) else "выключено"
    deadline_notifications_status = "включено" if settings.get("deadline_notifications_enabled", True) else "выключено"
    notification_time = settings.get("notification_time", "20:00")
    deadline_notification_time = settings.get("deadline_notification_time", "12:00")

    response = (
        f"1. Отображение выполненных заданий: {hide_status}\n"
        f"2. Оповещение о завтрашних парах: {notifications_status}\n"
        f"3. Время оповещения о завтрашних парах: {notification_time}\n"
        f"4. Оповещение о дедлайне: {deadline_notifications_status}\n"
        f"5. Время оповещения о дедлайне: {deadline_notification_time}\n\n"
        "Что хотите изменить?"
    )

    await message.answer(response, reply_markup=get_settings_keyboard(settings))
    log_action(message.from_user.id, "Открытие настроек", "Настройки")

@router.callback_query(F.data.in_(
    {"toggle_hide_completed", "toggle_schedule_notifications", "change_schedule_notification_time", 
     "toggle_deadline_notifications", "change_deadline_notification_time", "cancel"}))
async def process_notification_settings(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    settings = load_user_settings(user_id)

    if callback_query.data == "toggle_hide_completed":
        settings["hide_completed_tasks"] = not settings.get("hide_completed_tasks", False)
        save_user_settings(user_id, settings)
        status = "скрыты" if settings["hide_completed_tasks"] else "показываются"
        await callback_query.message.edit_text(f"Отображение обновлено. Теперь выполненные задания {status}.")

    elif callback_query.data == "toggle_schedule_notifications":
        settings["notifications_enabled"] = not settings.get("notifications_enabled", True)
        save_user_settings(user_id, settings)
        status = "включены" if settings["notifications_enabled"] else "выключены"
        await callback_query.message.edit_text(f"Оповещения о завтрашних парах {status}.")

    elif callback_query.data == "change_schedule_notification_time":
        # Удаляем старое меню настроек перед тем как спросить время
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await callback_query.message.answer("Введите новое время оповещения в формате ЧЧ:ММ:")
        await state.set_state(SettingsState.changing_time)

    elif callback_query.data == "toggle_deadline_notifications":
        settings["deadline_notifications_enabled"] = not settings.get("deadline_notifications_enabled", True)
        save_user_settings(user_id, settings)
        status = "включены" if settings["deadline_notifications_enabled"] else "выключены"
        await callback_query.message.edit_text(f"Оповещения о дедлайнах {status}.")

    elif callback_query.data == "change_deadline_notification_time":
        # Удаляем старое меню настроек перед тем как спросить время
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await callback_query.message.answer("Введите новое время оповещения о дедлайнах в формате ЧЧ:ММ:")
        await state.set_state(SettingsState.changing_deadline_time)

    elif callback_query.data == "cancel":
        await callback_query.message.edit_text("Действие отменено.")
        await state.clear()

    await callback_query.answer()


@router.message(SettingsState.changing_time)
async def process_new_time(message: types.Message, state: FSMContext):
    new_time = message.text.strip()
    try:
        # Принудительно форматируем (например, 9:00 -> 09:00)
        parsed = datetime.strptime(new_time, "%H:%M")
        formatted_time = parsed.strftime("%H:%M")
    except ValueError:
        await message.answer("Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.")
        return

    user_id = message.from_user.id
    settings = load_user_settings(user_id)
    settings["notification_time"] = formatted_time
    save_user_settings(user_id, settings)

    await message.answer(f"Время оповещения изменено на {formatted_time}.")
    await state.clear()


@router.message(SettingsState.changing_deadline_time)
async def process_new_deadline_time(message: types.Message, state: FSMContext):
    new_time = message.text.strip()
    try:
        parsed = datetime.strptime(new_time, "%H:%M")
        formatted_time = parsed.strftime("%H:%M")
    except ValueError:
        await message.answer("Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.")
        return

    user_id = message.from_user.id
    settings = load_user_settings(user_id)
    settings["deadline_notification_time"] = formatted_time
    save_user_settings(user_id, settings)

    await message.answer(f"Время оповещения о дедлайнах изменено на {formatted_time}.")
    await state.clear()


# Сохраняем поддержку старых текстовых команд на всякий случай
@router.message(F.text == "Управление оповещениями о завтрашних парах")
async def toggle_notifications_text(message: types.Message):
    user_id = message.from_user.id
    settings = load_user_settings(user_id)
    settings["notifications_enabled"] = not settings["notifications_enabled"]
    save_user_settings(user_id, settings)
    status = "включены" if settings["notifications_enabled"] else "выключены"
    await message.answer(f"Оповещения о завтрашних парах {status}.")


@router.message(F.text == "Изменить время оповещения")
async def change_notification_time_text(message: types.Message, state: FSMContext):
    await message.answer("Введите новое время оповещения в формате ЧЧ:ММ:")
    await state.set_state(SettingsState.changing_time)


@router.message(F.text == "Управление оповещениями о дедлайнах")
async def toggle_deadline_notifications_text(message: types.Message):
    user_id = message.from_user.id
    settings = load_user_settings(user_id)
    settings["deadline_notifications_enabled"] = not settings.get("deadline_notifications_enabled", True)
    save_user_settings(user_id, settings)
    status = "включены" if settings["deadline_notifications_enabled"] else "выключены"
    await message.answer(f"Оповещения о дедлайнах {status}.")


@router.message(F.text == "Изменить время оповещения о дедлайнах")
async def change_deadline_notification_time_text(message: types.Message, state: FSMContext):
    await message.answer("Введите новое время оповещения о дедлайнах в формате ЧЧ:ММ:")
    await state.set_state(SettingsState.changing_deadline_time)