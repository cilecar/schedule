import asyncio
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import PAGE_SIZE
from database.db import load_homework, save_homework, load_user_settings
from data.schedule_data import schedule_subjects, ALLOWED_EXTENSIONS, schedule, DAYS_MAP
from keyboards.reply import main_keyboard, cancel_reply_keyboard
from keyboards.inline import get_pagination_keyboard, get_status_keyboard
from services.utils import get_current_week
from services.logger import log_action

router = Router()


class HomeworkState(StatesGroup):
    choosing_subject = State()
    choosing_subject_for_adding = State()
    entering_task = State()
    attaching_files = State()
    entering_due_date = State()
    changing_subject = State()
    changing = State()
    entering_new_date = State()


# Глобальные структуры для обратной связи при загрузке файлов
feedback_tasks = {}
processed_albums = set()


async def debounce_send_feedback(bot: Bot, chat_id: int, key: str):
    await asyncio.sleep(1)  # Ждем 1 секунду после последнего файла
    await bot.send_message(chat_id, "Файлы прикреплены. Прикрепите еще файлы или нажмите ➡ Продолжить.")
    feedback_tasks.pop(key, None)
    if not key.startswith("user_"):
        processed_albums.add(key)


# ==========================================
# ПРОСМОТР ДОМАШНИХ ЗАДАНИЙ
# ==========================================

@router.message(F.text == "📚 Посмотреть домашние задания")
async def show_homework_subjects(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Все задания")],
            *[[KeyboardButton(text=subj)] for subj in schedule_subjects],
            [KeyboardButton(text="🚫 Отмена")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите предмет или нажмите 'Все задания'.", reply_markup=keyboard)
    await state.set_state(HomeworkState.choosing_subject)
    log_action(message.from_user.id, "Попытка просмотра домашних заданий", "Посмотреть домашние задания")


@router.message(HomeworkState.choosing_subject)
async def show_homework(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=main_keyboard)
        return

    if message.text == "Все задания":
        await state.update_data(subject=None)
        tasks = load_homework(user_id)
    else:
        subject = message.text
        if subject not in schedule_subjects:
            await message.answer("Выберите предмет из списка.")
            return
        await state.update_data(subject=subject)
        tasks = [task for task in load_homework(user_id) if task["subject"] == subject]

    # --- ФИЛЬТРАЦИЯ ВЫПОЛНЕННЫХ ---
    user_settings = load_user_settings(user_id)
    if user_settings.get("hide_completed_tasks", False): # <--- Меняем True на False
        tasks = [task for task in tasks if "Выполнено ✅" not in task.get("status", "")]

    # --- БРОНЕБОЙНАЯ СОРТИРОВКА ---
    tasks.sort(key=lambda x: datetime.strptime(x.get("date_added", "01.01.2024"), "%d.%m.%Y"))
    tasks.reverse()
    
    if not tasks:
        await message.answer("Нет актуальных домашних заданий по выбранному предмету.")
        return

    page = 1
    total_pages = ((len(tasks) - 1) // PAGE_SIZE) + 1
    start, end = (page - 1) * PAGE_SIZE, page * PAGE_SIZE
    page_tasks = tasks[start:end]

    title = "Все домашние задания" if message.text == "Все задания" else f"Домашние задания по предмету {message.text}"
    text = f"{title} (страница {page}/{total_pages}):\n\n"

    for task in page_tasks:
        text += (
            f"Статус: {task['status']}\n"
            f"Предмет: {task['subject']}\n"
            f"Задание: {task['task']}\n"
            f"Сделать до: {task['due_date']}\n"
        )
        if task.get("files_count", 0) > 0:
            text += f"Количество прикрепленных файлов: {task['files_count']}\n"
        text += "\n"

    inline_kb = get_pagination_keyboard(page, total_pages, page_tasks)
    await state.update_data(page=page, total_pages=total_pages, tasks=tasks)
    await message.answer(text, reply_markup=inline_kb)


@router.callback_query(lambda c: c.data.startswith("prev_") or c.data.startswith("next_"))
async def paginate_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data.get("page", 1)
    total_pages = data.get("total_pages", 1)
    tasks = data.get("tasks", [])
    subject = data.get("subject")

    if total_pages == 1:
        await callback_query.answer()
        return

    new_page = current_page - 1 if callback_query.data.startswith("prev_") else current_page + 1
    if new_page < 1:
        new_page = total_pages
    elif new_page > total_pages:
        new_page = 1

    page_tasks = tasks[(new_page - 1) * PAGE_SIZE: new_page * PAGE_SIZE]
    title = f"Домашние задания по предмету {subject}" if subject else "Все домашние задания"
    text = f"{title} (страница {new_page}/{total_pages}):\n\n"

    for task in page_tasks:
        text += (
            f"Статус: {task['status']}\n"
            f"Предмет: {task['subject']}\n"
            f"Задание: {task['task']}\n"
            f"Сделать до: {task['due_date']}\n"
        )
        if task.get("files_count", 0) > 0:
            text += f"Количество прикрепленных файлов: {task['files_count']}\n"
        text += "\n"

    inline_kb = get_pagination_keyboard(new_page, total_pages, page_tasks)
    await callback_query.message.edit_text(text, reply_markup=inline_kb)
    await state.update_data(page=new_page)
    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith("files_"))
async def send_task_files_callback(callback_query: types.CallbackQuery, bot: Bot):
    user_id = callback_query.from_user.id
    task_id = callback_query.data.split("_", 1)[1]
    tasks = load_homework(user_id)
    task = next((task for task in tasks if task.get("task_id") == task_id), None)

    if not task:
        await callback_query.answer("Задание не найдено.", show_alert=True)
        return

    text = (
        f"Статус: {task['status']}\n"
        f"Предмет: {task['subject']}\n"
        f"Задание: {task['task']}\n"
        f"Сделать до: {task['due_date']}\n"
    )
    if task.get("files_count", 0) > 0:
        text += f"Количество прикрепленных файлов: {task['files_count']}\n"

    photos = []
    documents = []
    if task.get("files"):
        for file in task["files"]:
            if file["type"] == "photo":
                photos.append(types.InputMediaPhoto(media=file["file_id"], caption=text if not photos else None))
            elif file["type"] == "document":
                documents.append(types.InputMediaDocument(media=file["file_id"]))

    if photos:
        await bot.send_media_group(user_id, photos)
    else:
        await bot.send_message(user_id, text)

    if documents:
        await bot.send_media_group(user_id, documents)
    await callback_query.answer()


# ==========================================
# ДОБАВЛЕНИЕ ДОМАШНЕГО ЗАДАНИЯ
# ==========================================

@router.message(F.text == "📝 Добавить домашнее задание")
async def add_homework_start(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=subj)] for subj in schedule_subjects] + [[KeyboardButton(text="🚫 Отмена")]],
        resize_keyboard=True
    )
    await state.set_state(HomeworkState.choosing_subject_for_adding)
    await message.answer("Выберите предмет:", reply_markup=keyboard)
    log_action(message.from_user.id, "Попытка добавления домашнего задания", "Добавить домашнее задание")


@router.message(HomeworkState.choosing_subject_for_adding)
async def choose_subject(message: types.Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=main_keyboard)
        return
    if message.text not in schedule_subjects:
        await message.answer("Выберите предмет из списка.")
        return

    await state.update_data(subject=message.text)
    await state.set_state(HomeworkState.entering_task)
    await message.answer("Введите задание:", reply_markup=cancel_reply_keyboard)


@router.message(HomeworkState.entering_task)
async def enter_task(message: types.Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=main_keyboard)
        return

    await state.update_data(task=message.text)
    await state.set_state(HomeworkState.attaching_files)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📎 Прикрепить файлы")],
            [KeyboardButton(text="➡ Продолжить")],
            [KeyboardButton(text="🚫 Отмена")]
        ],
        resize_keyboard=True
    )
    await message.answer("Хотите прикрепить файлы?", reply_markup=keyboard)


@router.message(HomeworkState.attaching_files, F.text == "🚫 Отмена")
async def cancel_attaching_files(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_keyboard)


@router.message(HomeworkState.attaching_files, F.text == "📎 Прикрепить файлы")
async def ask_for_files(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="➡ Продолжить")], [KeyboardButton(text="🚫 Отмена")]],
        resize_keyboard=True
    )
    await message.answer("Отправьте файлы (до 10 файлов, PDF, DOCX и другие).", reply_markup=keyboard)


@router.message(HomeworkState.attaching_files, F.document | F.photo)
async def receive_files(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    files = data.get("files", [])
    if len(files) >= 10:
        await message.answer("⚠ Вы можете прикрепить не более 10 файлов.")
        return

    file_info = {}
    if message.document:
        file_name = message.document.file_name
        file_extension = file_name.split(".")[-1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            await message.answer("⚠ Этот формат файла не поддерживается. Разрешены только PDF, DOCX, PNG, JPEG, JPG.")
            return
        file_info = {"file_id": message.document.file_id, "type": "document"}
    elif message.photo:
        file_info = {"file_id": message.photo[-1].file_id, "type": "photo"}

    files.append(file_info)
    await state.update_data(files=files)

    key = message.media_group_id if message.media_group_id else f"user_{message.from_user.id}"
    if message.media_group_id and message.media_group_id in processed_albums:
        await bot.send_message(message.chat.id, "Альбом уже загружен, файлы получены.")
        return

    if key in feedback_tasks:
        feedback_tasks[key].cancel()
    feedback_tasks[key] = asyncio.create_task(debounce_send_feedback(bot, message.chat.id, key))


@router.message(HomeworkState.attaching_files, F.text == "➡ Продолжить")
async def skip_files(message: types.Message, state: FSMContext):
    data = await state.get_data()
    subject = data.get("subject")
    next_class_date = None
    today = datetime.now(ZoneInfo("Europe/Moscow"))

    for offset in range(1, 15):
        check_date = today + timedelta(days=offset)
        day_name = DAYS_MAP.get(check_date.strftime("%A"), check_date.strftime("%A"))
        week_of_check_date = get_current_week(check_date)
        lessons = schedule.get(week_of_check_date, {}).get(day_name, [])
        if any(subject in lesson for lesson in lessons):
            next_class_date = check_date
            break

    next_class_date_str = next_class_date.strftime("%d.%m.%Y") if next_class_date else "не найдено"

    builder = ReplyKeyboardBuilder()

    # Добавляем кнопку с датой, только если бот смог ее вычислить
    if next_class_date_str != "не найдено":
        builder.button(text=next_class_date_str)

    builder.button(text="🚫 Отмена")
    builder.adjust(1)

    await message.answer(
        f"Введите срок выполнения (в формате ДД.ММ.ГГГГ). Следующее занятие по предмету {subject} будет {next_class_date_str}:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    await state.set_state(HomeworkState.entering_due_date)


@router.message(HomeworkState.entering_due_date)
async def enter_due_date(message: types.Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=main_keyboard)
        return

    try:
        due_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        if due_date < datetime.now().date() or due_date > datetime(2030, 12, 31).date():
            await message.answer("Некорректная дата. Введите дату в формате ДД.ММ.ГГГГ.")
            return
    except ValueError:
        await message.answer("Некорректный формат. Введите дату в формате ДД.ММ.ГГГГ.")
        return

    data = await state.get_data()
    user_id = message.from_user.id
    homework_list = load_homework(user_id)
    task_id = uuid.uuid4().hex
    files = data.get("files", [])

    homework_list.append({
        "subject": data["subject"],
        "task": data["task"],
        "task_id": task_id,
        "due_date": message.text,
        "date_added": datetime.now().strftime("%d.%m.%Y"),
        "status": "Не выполнено ❌",
        "files": files,
        "files_count": len(files)
    })

    save_homework(user_id, homework_list)
    await state.clear()
    await message.answer("Задание добавлено!", reply_markup=main_keyboard)


# ==========================================
# ИЗМЕНЕНИЕ СТАТУСА ДОМАШНЕГО ЗАДАНИЯ
# ==========================================

@router.message(F.text == "✏️ Изменить статус задания")
async def change_homework_prompt(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    homework_list = load_homework(user_id)
    if not homework_list:
        await message.answer("Домашних заданий нет.")
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=subj)] for subj in schedule_subjects] + [[KeyboardButton(text="🚫 Отмена")]],
        resize_keyboard=True
    )
    await state.set_state(HomeworkState.changing_subject)
    await message.answer("Выберите предмет:", reply_markup=keyboard)
    log_action(message.from_user.id, "Попытка изменения статуса задания", "Изменить статус задания")


@router.message(HomeworkState.changing_subject)
async def choose_subject_for_status_change(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    homework_list = load_homework(user_id)

    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=main_keyboard)
        return
    if message.text not in schedule_subjects:
        await message.answer("Выберите предмет из списка.")
        return

    subject = message.text
    subject_tasks = [task for task in homework_list if task["subject"] == subject]

    if not subject_tasks:
        await state.clear()
        await message.answer(f"Нет заданий по предмету {subject}.", reply_markup=main_keyboard)
        return

    updated = False
    for task in subject_tasks:
        if "task_id" not in task:
            task["task_id"] = uuid.uuid4().hex
            updated = True

    if updated:
        save_homework(user_id, homework_list)

    await state.update_data(subject=subject, subject_tasks=subject_tasks)

    buttons = []
    for task in subject_tasks:
        display_text = task["task"] if len(task["task"]) <= 30 else task["task"][:30] + "..."
        buttons.append([InlineKeyboardButton(text=display_text, callback_data=f"select_{task['task_id']}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(HomeworkState.changing)
    await message.answer("Выберите задание для изменения статуса:", reply_markup=keyboard)


@router.callback_query(lambda c: c.data.startswith("select_"))
async def select_task_for_status_change(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    subject_tasks = data.get("subject_tasks", [])
    task_id = callback_query.data.split("select_")[1]

    selected_task = next((task for task in subject_tasks if task["task_id"] == task_id), None)
    if not selected_task:
        await callback_query.answer("Ошибка: задание не найдено.", show_alert=True)
        return

    await state.update_data(selected_task=selected_task)
    await callback_query.message.edit_text(
        f"Выберите новый статус для задания:\n"
        f"Задание: {selected_task['task']}\n"
        f"Текущий статус: {selected_task['status']}",
        reply_markup=get_status_keyboard()
    )
    await callback_query.answer()


@router.message(HomeworkState.changing)
async def change_homework_status(message: types.Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=main_keyboard)
        return

    data = await state.get_data()
    subject_tasks = data.get("subject_tasks", [])
    selected_task = next((task for task in subject_tasks if task["task"] == message.text), None)

    if not selected_task:
        await message.answer("Ошибка: задание не найдено. Выберите из списка.")
        return

    await state.update_data(selected_task=selected_task)
    await message.answer(
        f"Выберите новый статус для задания: <b>{selected_task['task']}</b>\n"
        f"Текущий статус: <b>{selected_task['status']}</b>",
        reply_markup=get_status_keyboard(), parse_mode="HTML"
    )


@router.callback_query(
    lambda c: c.data in ["status_done", "status_not_done", "status_edit_date", "status_delete", "cancel"] or c.data.startswith(
        ("done_", "notdone_", "delete_")))
async def process_status_change_update(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback_query.from_user.id

    # Обработка старого формата кнопок (для совместимости с историей чата)
    if callback_query.data.startswith(("done_", "notdone_", "delete_")):
        action, task_id = callback_query.data.split("_", 1)
        homework_list = load_homework(user_id)
        selected_task = next((task for task in homework_list if task.get("task").startswith(task_id)), None)
        if not selected_task:
            await callback_query.message.answer("Ошибка: задание не найдено.", reply_markup=main_keyboard)
            await callback_query.answer()
            return

        if action == "done":
            selected_task["status"] = "Выполнено ✅"
        elif action == "notdone":
            selected_task["status"] = "Не выполнено ❌"
        elif action == "delete":
            homework_list = [task for task in homework_list if task != selected_task]
            save_homework(user_id, homework_list)
            await callback_query.message.delete()
            await callback_query.message.answer(f'Задание "{selected_task["task"]}" удалено.',
                                                reply_markup=main_keyboard)
            await state.clear()
            return

        for task in homework_list:
            if task["task"] == selected_task["task"]:
                task["status"] = selected_task["status"]
                break
        save_homework(user_id, homework_list)
        await callback_query.message.delete()
        await callback_query.message.answer(
            f'Для задания "{selected_task["task"]}" установлен статус: {selected_task["status"]}',
            reply_markup=main_keyboard)
        await state.clear()
        await callback_query.answer()
        return

    # Обработка нового формата кнопок
    data = await state.get_data()
    selected_task = data.get("selected_task")

    if callback_query.data == "cancel":
        await state.clear()
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await bot.send_message(user_id, "Действие отменено.", reply_markup=main_keyboard)
        await callback_query.answer()
        return

    if not selected_task:
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await bot.send_message(user_id, "Ошибка: задание не найдено.", reply_markup=main_keyboard)
        await callback_query.answer()
        return

    if callback_query.data == "status_done":
        selected_task["status"] = "Выполнено ✅"
    elif callback_query.data == "status_not_done":
        selected_task["status"] = "Не выполнено ❌"
    elif callback_query.data == "status_edit_date":
        await state.set_state(HomeworkState.entering_new_date)
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await bot.send_message(
            user_id, 
            f"Введите новую дату дедлайна для «{selected_task['task']}» (ДД.ММ.ГГГГ):", 
            reply_markup=cancel_reply_keyboard
        )
        await callback_query.answer()
        return    
    elif callback_query.data == "status_delete":
        homework_list = load_homework(user_id)
        homework_list = [task for task in homework_list if task != selected_task]
        save_homework(user_id, homework_list)
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await bot.send_message(user_id, f'Задание "{selected_task["task"]}" удалено.', reply_markup=main_keyboard)
        await state.clear()
        await callback_query.answer()
        return

    homework_list = load_homework(user_id)
    for task in homework_list:
        if task["task"] == selected_task["task"]:
            task["status"] = selected_task["status"]
            break

    save_homework(user_id, homework_list)
    try:
        await callback_query.message.delete()
    except Exception:
        pass

    await bot.send_message(user_id,
                           f'Для задания "{selected_task["task"]}" установлен статус: {selected_task["status"]}',
                           reply_markup=main_keyboard)
    await state.clear()
    await callback_query.answer()

@router.message(HomeworkState.entering_new_date)
async def process_new_due_date(message: types.Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=main_keyboard)
        return

    # Тот самый блок проверки (да, он дублируется, и это нормально!)
    try:
        new_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        if new_date < datetime.now().date() or new_date > datetime(2030, 12, 31).date():
            await message.answer("Некорректная дата. Введите дату в формате ДД.ММ.ГГГГ.")
            return
    except ValueError:
        await message.answer("Некорректный формат. Введите дату в формате ДД.ММ.ГГГГ.")
        return

    # Логика ОБНОВЛЕНИЯ существующего ДЗ
    data = await state.get_data()
    selected_task = data.get("selected_task")
    user_id = message.from_user.id
    
    homework_list = load_homework(user_id)
    # Ищем наше задание и меняем ему дату
    for task in homework_list:
        if task.get("task_id") == selected_task.get("task_id"):
            task["due_date"] = message.text
            break
            
    save_homework(user_id, homework_list)
    await state.clear()
    await message.answer(f"Дата дедлайна успешно изменена на {message.text}!", reply_markup=main_keyboard)