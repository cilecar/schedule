from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re
from data.schedule_data import GLOBAL_SEMESTER_START, DAYS_MAP, schedule

def get_current_week(now: datetime) -> str:
    """Определяет текущую учебную неделю (1 или 2)."""
    weeks_passed = (now - GLOBAL_SEMESTER_START).days // 7
    return "1" if weeks_passed % 2 == 0 else "2"

def get_tomorrow_lessons(now: datetime) -> list:
    """Возвращает список пар на завтрашний день с учетом правильной недели."""
    tomorrow_date = now + timedelta(days=1)
    # Вычисляем номер недели именно для ЗАВТРАШНЕГО дня
    tomorrow_week = get_current_week(tomorrow_date) 
    
    tomorrow_day_name = tomorrow_date.strftime("%A")
    tomorrow_local = DAYS_MAP.get(tomorrow_day_name, tomorrow_day_name)
    return schedule.get(tomorrow_week, {}).get(tomorrow_local, [])

def format_lesson_html(lesson_str: str) -> str:
    """Ищет ссылку в строке и делает ее красивой HTML-гиперссылкой."""
    # Ищем всё, что начинается на http:// или https://
    url_match = re.search(r'(https?://[^\s]+)', lesson_str)

    if url_match:
        url = url_match.group(1)
        # Удаляем длинную ссылку из оригинальной строки
        clean_text = lesson_str.replace(url, "").strip()
        # Возвращаем чистый текст + кликабельную кнопку
        return f"{clean_text} <a href='{url}'>[Ссылка]</a>"

    return lesson_str