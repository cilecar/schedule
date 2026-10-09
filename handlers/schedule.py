from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Router, F, types
from data.schedule_data import DAYS_MAP, schedule
from services.utils import get_current_week, format_lesson_html
from services.logger import log_action

# Создаем роутер для расписания
router = Router()


@router.message(F.text == "📅 Расписание на сегодня")
async def today_schedule(message: types.Message):
    now = datetime.now(ZoneInfo("Europe/Moscow"))
    current_week = get_current_week(now)
    today_name = DAYS_MAP.get(now.strftime("%A"), now.strftime("%A"))
    lessons = schedule.get(current_week, {}).get(today_name, ["На сегодня пар нет."])

    # Форматируем каждую строчку
    formatted_lessons = [format_lesson_html(lesson) for lesson in lessons]

    await message.answer(
        f"Сейчас {current_week}-я неделя.\n\n" + "\n".join(formatted_lessons),
        parse_mode="HTML" # Говорим Телеграму читать HTML-теги
    )
    log_action(message.from_user.id, "Попытка отправки расписания на сегодня", "Расписание на сегодня")


@router.message(F.text == "📆 Расписание на завтра")
async def tomorrow_schedule(message: types.Message):
    now = datetime.now(ZoneInfo("Europe/Moscow"))
    current_week = get_current_week(now)
    tomorrow_date = now.date() + timedelta(days=1)
    tomorrow_name = DAYS_MAP.get(tomorrow_date.strftime("%A"), tomorrow_date.strftime("%A"))
    lessons = schedule.get(current_week, {}).get(tomorrow_name, ["На завтра пар нет."])

    formatted_lessons = [format_lesson_html(lesson) for lesson in lessons]

    await message.answer(
        f"Сейчас {current_week}-я неделя.\n\n" + "\n".join(formatted_lessons),
        parse_mode="HTML"
    )
    log_action(message.from_user.id, "Попытка отправки расписания на завтра", "Расписание на завтра")


@router.message(F.text == "📖 Полное расписание")
async def full_schedule(message: types.Message):
    response = "<b>Полное расписание:</b>\n"
    for week, days in schedule.items():
        response += f"\n<b>Неделя {week}:</b>\n"
        for day, lessons in days.items():
            formatted_lessons = [format_lesson_html(lesson) for lesson in lessons]
            response += f"\n<u>{day}</u>:\n" + "\n".join(formatted_lessons) + "\n"

    await message.answer(response, parse_mode="HTML")
    log_action(message.from_user.id, "Попытка отправки полного расписания", "Полное расписание")