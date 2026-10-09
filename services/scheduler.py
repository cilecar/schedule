import asyncio
import logging
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from database.db import load_user_settings, load_users, load_homework # <-- Изменили импорты
from services.utils import get_tomorrow_lessons, format_lesson_html
from data.schedule_data import schedule, DAYS_MAP
from handlers.base import AdminState
from keyboards.reply import cancel_reply_keyboard

logger = logging.getLogger(__name__)

last_clear_date = datetime.now(ZoneInfo("Europe/Moscow")).date()
sent_notifications = set()
sent_deadline_notifications = set()
prompted_lessons = set()

def check_and_clear_cache():
    """Надежно очищает кэш при смене суток."""
    global last_clear_date
    now_date = datetime.now(ZoneInfo("Europe/Moscow")).date()
    if now_date > last_clear_date:
        sent_notifications.clear()
        sent_deadline_notifications.clear()
        prompted_lessons.clear()
        last_clear_date = now_date
        logger.info("Кэш уведомлений очищен на новый день.")

async def send_tomorrow_schedule_callback(bot: Bot):
    while True:
        try:
            check_and_clear_cache()
            now = datetime.now(ZoneInfo("Europe/Moscow"))
            users = load_users() # Берем ВСЕХ пользователей

            for uid in users:
                if uid in sent_notifications:
                    continue
                
                user_settings = load_user_settings(uid)
                if not user_settings.get("notifications_enabled", True):
                    continue

                notif_time = user_settings.get("notification_time", "20:00")
                if now.strftime("%H:%M") == notif_time:
                    lessons = get_tomorrow_lessons(now)
                    if lessons:
                        formatted = [format_lesson_html(l) for l in lessons]
                        await bot.send_message(uid, f"📅 Завтра у тебя:\n" + "\n".join(formatted), parse_mode="HTML")
                    
                    sent_notifications.add(uid)
        except Exception as e:
            logger.error(f"Ошибка в задаче расписания: {e}")
        
        await asyncio.sleep(30)

async def send_deadline_reminders_callback(bot: Bot):
    while True:
        try:
            check_and_clear_cache()
            now = datetime.now(ZoneInfo("Europe/Moscow"))
            users = load_users()

            for uid in users:
                if uid in sent_deadline_notifications:
                    continue

                user_settings = load_user_settings(uid)
                if not user_settings.get("deadline_notifications_enabled", True):
                    continue

                notif_time = user_settings.get("deadline_notification_time", "12:00")
                if now.strftime("%H:%M") == notif_time:
                    homework_list = load_homework(uid)
                    tomorrow_date_str = (now + timedelta(days=1)).strftime("%d.%m.%Y")
                    
                    bad_tasks = [t for t in homework_list if t["due_date"] == tomorrow_date_str and t["status"] == "Не выполнено ❌"]
                    
                    if bad_tasks:
                        msg = "❗️Напоминание, завтра дедлайн❗️\n"
                        for t in bad_tasks:
                            msg += f"\n— {t['subject']}: {t['task']}"
                        
                        await bot.send_message(uid, msg)
                    
                    sent_deadline_notifications.add(uid)
        except Exception as e:
            logger.error(f"Ошибка в задаче дедлайнов: {e}")
            
        await asyncio.sleep(30)

async def ask_admin_for_link_callback(bot: Bot, dp: Dispatcher):
    while True:
        try:
            check_and_clear_cache()
            now = datetime.now(ZoneInfo("Europe/Moscow"))
            day_name = DAYS_MAP.get(now.strftime("%A"), now.strftime("%A"))

            if day_name in ["Четверг", "Пятница"]:
                from services.utils import get_current_week
                lessons = schedule.get(get_current_week(now), {}).get(day_name, [])

                for lesson in lessons:
                    if lesson in prompted_lessons: continue
                    
                    parts = lesson.split(" - ", 1)
                    if len(parts) < 2: continue
                        
                    start_time_str = parts[0].strip()
                    subject_raw = parts[1].strip()

                    try:
                        sh, sm = map(int, start_time_str.split(":"))
                        start_dt = now.replace(hour=sh, minute=sm, second=0, microsecond=0)
                        
                        diff = start_dt - now
                        if timedelta(minutes=14) <= diff <= timedelta(minutes=15):
                            prompted_lessons.add(lesson)
                            
                            subject_clean = re.sub(r'https?://\S+', '', subject_raw).strip()
                            url_match = re.search(r'(https?://[^\s]+)', subject_raw)
                            eios_link = f"\nСсылка EIOS: <a href='{url_match.group(1)}'>[Перейти]</a>" if url_match else ""
                            
                            end_dt = start_dt + timedelta(minutes=90)
                            time_range = f"{start_time_str} - {end_dt.strftime('%H:%M')}"

                            state = FSMContext(storage=dp.storage, key=StorageKey(bot_id=bot.id, chat_id=ADMIN_ID, user_id=ADMIN_ID))
                            await state.set_state(AdminState.waiting_for_lesson_link)
                            await state.update_data(lesson_subject=subject_clean, lesson_time=time_range)

                            await bot.send_message(ADMIN_ID, f"Предмет: <b>{subject_clean}</b>{eios_link}\n\nВведите ссылку на чат:", 
                                                   reply_markup=cancel_reply_keyboard, parse_mode="HTML")
                    except ValueError:
                        continue
        except Exception as e:
            logger.error(f"Ошибка в задаче запроса ссылок: {e}")
            
        await asyncio.sleep(40)

active_background_tasks = set()

def start_background_tasks(bot: Bot, dp: Dispatcher):
    # Теперь мы сохраняем задачи, и Python их не убьет!
    t1 = asyncio.create_task(send_tomorrow_schedule_callback(bot))
    t2 = asyncio.create_task(send_deadline_reminders_callback(bot))
    t3 = asyncio.create_task(ask_admin_for_link_callback(bot, dp))
    
    active_background_tasks.update({t1, t2, t3})