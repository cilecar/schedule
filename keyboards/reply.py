from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Расписание на сегодня")],
        [KeyboardButton(text="📆 Расписание на завтра")],
        [KeyboardButton(text="📖 Полное расписание")],
        [KeyboardButton(text="📝 Добавить домашнее задание")],
        [KeyboardButton(text="📚 Посмотреть домашние задания")],
        [KeyboardButton(text="✏️ Изменить статус задания")],
        [KeyboardButton(text="⚙️ Настройки")]
    ],
    resize_keyboard=True
)

cancel_reply_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🚫 Отмена")]],
    resize_keyboard=True
)