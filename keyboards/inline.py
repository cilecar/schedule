from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_pagination_keyboard(page: int, total_pages: int, page_tasks: list) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для пагинации и файлов домашки."""
    file_buttons = [
        [InlineKeyboardButton(text=f"Файлы: {task['task'][:20]}...", callback_data=f"files_{task['task_id']}")]
        for task in page_tasks if task.get("files")
    ]
    pagination_buttons = []
    if total_pages > 1:
        pagination_buttons.append([
            InlineKeyboardButton(text="⬅️", callback_data=f"prev_{page}"),
            InlineKeyboardButton(text="➡️", callback_data=f"next_{page}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=file_buttons + pagination_buttons)


def get_status_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру изменения статуса задания."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выполнено", callback_data="status_done")],
        [InlineKeyboardButton(text="❌ Не выполнено", callback_data="status_not_done")],
        [InlineKeyboardButton(text="📅 Изменить дату", callback_data="status_edit_date")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data="status_delete")],
        [InlineKeyboardButton(text="🚫 Отмена", callback_data="cancel")]
    ])


def get_settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру настроек."""
    schedule_enabled = settings.get('notifications_enabled', True)
    deadline_enabled = settings.get('deadline_notifications_enabled', True)
    hide_completed = settings.get('hide_completed_tasks', False)
    
    notif_time = settings.get("notification_time", "20:00")
    deadline_time = settings.get("deadline_notification_time", "12:00")

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Показывать все задания" if hide_completed else "Скрывать выполненные задания", 
            callback_data="toggle_hide_completed"
        )],
        [InlineKeyboardButton(
            text=f"{'Выключить' if schedule_enabled else 'Включить'} оповещение расписания",
            callback_data="toggle_schedule_notifications"
        )],
        [InlineKeyboardButton(
            text=f"Время оповещения расписания: {notif_time}", 
            callback_data="change_schedule_notification_time"
        )],
        [InlineKeyboardButton(
            text=f"{'Выключить' if deadline_enabled else 'Включить'} оповещение о дедлайне",
            callback_data="toggle_deadline_notifications"
        )],
        [InlineKeyboardButton(
            text=f"Время оповещения о дедлайне: {deadline_time}", 
            callback_data="change_deadline_notification_time"
        )],
        [InlineKeyboardButton(text="🚫 Отмена", callback_data="cancel")]
    ])