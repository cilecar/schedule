import logging
import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta

TOKEN = "7580702048:AAFWmm573ZcKt6zcQXquW0cjsf9bUxKcpFw"
HOMEWORK_FILE = "homework.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()

class HomeworkState(StatesGroup):
    adding = State()
    changing = State()
    choosing_subject = State()
    changing_subject = State()
    attaching_file = State()
    entering_task = State()
    entering_due_date = State()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Расписание на сегодня")],
        [KeyboardButton(text="Расписание на завтра")],
        [KeyboardButton(text="Полное расписание")],
        [KeyboardButton(text="Добавить домашнее задание")],
        [KeyboardButton(text="Посмотреть домашние задания")],
        [KeyboardButton(text="Изменить статус задания")]
    ],
    resize_keyboard=True
)

schedule = { 
    "1": 
        { 
        "Четверг": [ 
            "13:10 - пр.Основы программирования Петросян А.М. https://eios.imsit.ru/course/view.php?id=12016", 
            "14:50 - л.Интегралы и дифференциальные уравнения Грицык Е.А. https://eios.imsit.ru/course/view.php?id=12014", 
            "16:30 - пр.Интегралы и дифференциальные уравнения Грицык Е.А. https://eios.imsit.ru/course/view.php?id=12014", 
            "18:10 - л.Линейная алгебра и функция нескольких переменных Леонова И.В. https://eios.imsit.ru/course/view.php?id=12015" ], 
        "Пятница": [ 
            "9:40 - л.История информационного противоборства Микаэлян А.С. https://eios.imsit.ru/course/view.php?id=11962", 
            "11:30 - пр.Право Лудилин Д.Б. https://eios.imsit.ru/course/view.php?id=11984" ], 
        "Суббота": [ 
            "8:00 - пр.Основы информационной безопасности Нигматов В.А.", 
            "9:40 - пр.Иностранный язык Чумичева Н.В.", 
            "11:10 - пр.Социальные и этические вопросы в информационной сфере Ольшанская С.А." ] 
            }, 
    "2": 
        { 
        "Четверг": [ 
            "13:10 - л.История России Обухова Ю.А. https://eios.imsit.ru/course/view.php?id=12026", 
            "14:50 - пр.История России Обухова Ю.А. https://eios.imsit.ru/course/view.php?id=12026", 
            "16:30 - пр.Интегралы и дифференциальные уравнения Грицык Е.А. https://eios.imsit.ru/course/view.php?id=12014", 
            "18:10 - пр.Линейная алгебра и функция нескольких переменных Леонова И.В. https://eios.imsit.ru/course/view.php?id=12015" ], 
        "Пятница": [ 
            "8:00 - л.Физика Леонова И.В. https://eios.imsit.ru/course/view.php?id=12011", 
            "9:40 - л.Право Жидяева Е.С. https://eios.imsit.ru/course/view.php?id=11984" ], 
        "Суббота": [ 
            "8:00 - пр.Линейная алгебра и функция нескольких переменных Леонова И.В.", 
            "9:40 - лаб.Физика Леонова И.В.", 
            "11:30 - пр.Дискретная математика Лисин Д.А." ] 
        } }

schedule_subjects = ["Интегралы и дифференциальные уравнения", "Линейная алгебра и функция нескольких переменных", "История информационного противоборства", "Право", "Основы информационной безопасности", "Иностранный язык", "Социальные и этические вопросы в информационной сфере", "История России", "Физика", "Основы программирования", "Дискретная математика"]
homework = []

# Функция загрузки домашнего задания из файла для конкретного пользователя
def load_homework(user_id):
    if os.path.exists(HOMEWORK_FILE):
        with open(HOMEWORK_FILE, "r", encoding="utf-8") as f:
            all_homework = json.load(f)
            return all_homework.get(str(user_id), [])
    return []

# Функция сохранения домашнего задания для конкретного пользователя
def save_homework(user_id, homework_data):
    if os.path.exists(HOMEWORK_FILE):
        with open(HOMEWORK_FILE, "r", encoding="utf-8") as f:
            all_homework = json.load(f)
    else:
        all_homework = {}

    all_homework[str(user_id)] = homework_data

    with open(HOMEWORK_FILE, "w", encoding="utf-8") as f:
        json.dump(all_homework, f, ensure_ascii=False, indent=4)



@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Я бот, который поможет тебе с расписанием и домашними заданиями.", reply_markup=main_keyboard)



# Функция отображения всего расписания 
@dp.message(F.text == "Полное расписание")
async def full_schedule(message: types.Message):
    response = "Полное расписание:\n"
    for week, days in schedule.items():
        response += f"\nНеделя {week}:\n"
        for day, lessons in days.items():
            response += f"{day}:\n" + "\n".join(lessons) + "\n"
    await message.answer(response)




# Функция отображения расписания на сегодня
@dp.message(F.text == "Расписание на сегодня")
async def today_schedule(message: types.Message):
    today = datetime.now()

    SEMESTER_START = datetime(2024, 9, 2)

    weeks_passed = (today - SEMESTER_START).days // 7

    current_week = "1" if weeks_passed % 2 == 0 else "2"

    days_map = {
        "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда", 
        "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
    }
    today_name = days_map.get(today.strftime("%A"), today.strftime("%A"))

    response = schedule.get(current_week, {}).get(today_name, ["На сегодня пар нет."])
    await message.answer(f"Сейчас {current_week}-я неделя.\n\n" + "\n".join(response))



# Функция отображения расписания на завтра
@dp.message(F.text == "Расписание на завтра")
async def tomorrow_schedule(message: types.Message):
    now = datetime.now()

    SEMESTER_START = datetime(2024, 9, 2)  # 2 сентября 2024

    weeks_passed = (now - SEMESTER_START).days // 7

    current_week = "1" if weeks_passed % 2 == 0 else "2"

    tomorrow = (now.weekday() + 1) % 7
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

    tomorrow_name = days[tomorrow]

    response = schedule.get(current_week, {}).get(tomorrow_name, ["На завтра пар нет."])

    await message.answer("\n".join(response))



# Функция напоминания о завтрашних парах
async def send_tomorrow_schedule():
    while True:
        now = datetime.now()
        target_time = now.replace(hour=18, minute=0, second=0, microsecond=0)

        if now > target_time:
            target_time += timedelta(days=1)

        wait_time = (target_time - now).total_seconds()
        await asyncio.sleep(wait_time)

        SEMESTER_START = datetime(2024, 9, 2)

        weeks_passed = (now - SEMESTER_START).days // 7

        current_week = "1" if weeks_passed % 2 == 0 else "2"

        tomorrow_day = (datetime.today() + timedelta(days=1)).strftime("%A")
        days_map = {
            "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда", 
            "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
        }

        tomorrow_name = days_map.get(tomorrow_day, tomorrow_day)
        
        response = schedule.get(current_week, {}).get(tomorrow_name, ["На завтра пар нет."])

        await bot.send_message(706172589, f"📅 Завтра у тебя:\n" + "\n".join(response))


#----------------------------------------------------------------------------------------------------------#



# Функция добавления записи домашнего задания
@dp.message(F.text == "Добавить домашнее задание")
async def add_homework_start(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=subj)] for subj in schedule_subjects] + [[KeyboardButton(text="🚫 Отмена")]], 
        resize_keyboard=True
    )
    await state.set_state(HomeworkState.choosing_subject)
    await message.answer("Выберите предмет:", reply_markup=keyboard)


@dp.message(HomeworkState.choosing_subject)
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
    await message.answer("Введите задание:", reply_markup=types.ReplyKeyboardRemove())


@dp.message(HomeworkState.entering_task)
async def enter_task(message: types.Message, state: FSMContext):
    await state.update_data(task=message.text)
    await state.set_state(HomeworkState.attaching_file)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📎 Прикрепить файл")], [KeyboardButton(text="➡ Пропустить")], [KeyboardButton(text="🚫 Отмена")]],
        resize_keyboard=True
    )
    await message.answer("Хотите прикрепить файл?", reply_markup=keyboard)

@dp.message(HomeworkState.attaching_file, F.text == "🚫 Отмена")
async def cancel_attaching_file(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_keyboard)

@dp.message(HomeworkState.attaching_file, F.text == "📎 Прикрепить файл")
async def ask_for_file(message: types.Message, state: FSMContext):
    
    await message.answer("Отправьте файл (PDF, DOCX и другие).", reply_markup=types.ReplyKeyboardRemove())

@dp.message(HomeworkState.attaching_file, F.content_type.in_({"document"}))
async def receive_file(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    await state.update_data(file_id=file_id, file_name=message.document.file_name)
    await state.set_state(HomeworkState.entering_due_date)
    await message.answer("Введите срок выполнения (например, 10.03.2025):")

@dp.message(HomeworkState.attaching_file, F.text == "➡ Пропустить")
async def skip_file(message: types.Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=main_keyboard)
        return
    await state.update_data(file_id=None, file_name=None)
    await state.set_state(HomeworkState.entering_due_date)
    await message.answer("Введите срок выполнения (в формате ДД.ММ.ГГГГ):", reply_markup=types.ReplyKeyboardRemove())

@dp.message(HomeworkState.entering_due_date)
async def enter_due_date(message: types.Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=main_keyboard)
        return

    try:
        datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await message.answer("Некорректный формат. Введите дату в формате ДД.ММ.ГГГГ.")
        return
    
    data = await state.get_data()
    user_id = message.from_user.id  # Получаем ID пользователя

    # Загружаем домашние задания для конкретного пользователя
    homework = load_homework(user_id)

    homework.append({
        "subject": data["subject"],
        "task": data["task"],
        "due_date": message.text,
        "date_added": datetime.now().strftime("%d.%m.%Y"),
        "status": "Не выполнено ❌",
        "file_id": data.get("file_id"),
        "file_name": data.get("file_name")
    })

    save_homework(user_id, homework)  # Сохраняем домашку для конкретного пользователя

    await state.clear()
    await message.answer("Задание добавлено!", reply_markup=main_keyboard)




# Функция просмотра записей домашних заданий
@dp.message(F.text == "Посмотреть домашние задания")
async def show_homework(message: types.Message):
    user_id = message.from_user.id  # Получаем ID пользователя

    homework = load_homework(user_id)  # Загружаем домашку для пользователя

    if not homework:
        await message.answer("Домашних заданий нет.")
    else:
        for task in homework:
            response = f"[{task['status']}] {task['subject']} - {task['task']}, сделать до {task['due_date']} (Добавлено: {task['date_added']})"
            if task.get("file_id"):
                response += f"\n📎 Прикрепленный файл: {task['file_name']}"
                await message.answer_document(task["file_id"], caption=response)
            else:
                await message.answer(response)



# Клавиатура для отмены
cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🚫 Отмена", callback_data="cancel")]
])

# Функция смены статуса записи домашнего задания
@dp.message(F.text == "Изменить статус задания")
async def change_homework_prompt(message: types.Message, state: FSMContext):
    user_id = message.from_user.id  # Получаем ID пользователя
    homework = load_homework(user_id)  # Загружаем домашку для пользователя

    if not homework:
        await message.answer("Домашних заданий нет.")
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=subj)] for subj in schedule_subjects] + [[KeyboardButton(text="🚫 Отмена")]], 
        resize_keyboard=True
    )

    await state.set_state(HomeworkState.changing_subject)
    await message.answer("Выберите предмет:", reply_markup=keyboard)

@dp.message(HomeworkState.changing_subject)
async def choose_subject_for_status_change(message: types.Message, state: FSMContext):
    user_id = message.from_user.id  # Получаем ID пользователя
    homework = load_homework(user_id)  # Загружаем домашку для пользователя

    if message.text == "🚫 Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=main_keyboard)
        return

    if message.text not in schedule_subjects:
        await message.answer("Выберите предмет из списка.")
        return

    subject = message.text
    subject_tasks = [task for task in homework if task["subject"] == subject]

    if not subject_tasks:
        await state.clear()
        await message.answer(f"Нет заданий по предмету {subject}.", reply_markup=main_keyboard)
        return

    await state.update_data(subject=subject, subject_tasks=subject_tasks)

    # Создаем кнопки с текстом задания
    task_buttons = [[KeyboardButton(text=task["task"])] for task in subject_tasks]
    task_buttons.append([KeyboardButton(text="🚫 Отмена")])

    keyboard = ReplyKeyboardMarkup(keyboard=task_buttons, resize_keyboard=True)

    await state.set_state(HomeworkState.changing)
    await message.answer("Выберите задание:", reply_markup=keyboard)

@dp.message(HomeworkState.changing)
async def change_homework_status(message: types.Message, state: FSMContext):
    user_id = message.from_user.id  # Получаем ID пользователя
    data = await state.get_data()
    subject_tasks = data.get("subject_tasks", [])

    selected_task = next((task for task in subject_tasks if task["task"] == message.text), None)

    if not selected_task:
        await message.answer("Ошибка: задание не найдено. Выберите из списка.")
        return

    # Сохраняем индекс выбранной задачи в состоянии
    await state.update_data(selected_task=selected_task)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выполнено", callback_data="status_done")],
        [InlineKeyboardButton(text="❌ Не выполнено", callback_data="status_not_done")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data="status_delete")],
        [InlineKeyboardButton(text="🚫 Отмена", callback_data="cancel")]
    ])
    
    await message.answer(f"Выберите новый статус для задания:\n<b>{selected_task['task']}</b>", reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(lambda c: c.data in ["status_done", "status_not_done", "status_delete", "cancel"])
async def process_status_change(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id  # Получаем ID пользователя
    data = await state.get_data()
    selected_task = data.get("selected_task")  # Получаем выбранную задачу

    if callback_query.data == "cancel":
        await state.clear()
        await callback_query.message.answer("Действие отменено.", reply_markup=main_keyboard)
        await callback_query.answer()
        return
    
    if not selected_task:
        await callback_query.message.answer("Ошибка: задание не найдено.", reply_markup=main_keyboard)
        await callback_query.answer()
        return

    # Обновляем статус задачи
    if callback_query.data == "status_done":
        selected_task["status"] = "Выполнено ✅"
    elif callback_query.data == "status_not_done":
        selected_task["status"] = "Не выполнено ❌"
    elif callback_query.data == "status_delete":
        # Удаляем задание
        homework = load_homework(user_id)
        homework = [task for task in homework if task != selected_task]  # Удаляем задачу
        save_homework(user_id, homework)
        await callback_query.message.answer('Задача удалена.', reply_markup=main_keyboard)
        await state.clear()
        return

    # Обновляем список заданий с новым статусом
    homework = load_homework(user_id)

    # Ищем нужную задачу и обновляем ее статус
    for task in homework:
        if task["task"] == selected_task["task"]:  # Сравниваем по имени задания
            task["status"] = selected_task["status"]  # Обновляем статус
            break  # Останавливаемся на первой найденной задаче

    # Сохраняем обновленные задания
    save_homework(user_id, homework)

    await state.clear()
    await callback_query.message.answer(f'Установлен статус: {selected_task["status"]}', reply_markup=main_keyboard)
    await callback_query.answer()









async def send_deadline_reminders():
    while True:
        now = datetime.now()
        for task in homework:
            due_date = datetime.strptime(task["due_date"], "%d.%m.%Y")
            if due_date - timedelta(days=1) <= now < due_date and task["status"] == "Не выполнено ❌":
                await bot.send_message(
                    chat_id="706172589",
                    text=f"❗Напоминание: Завтра дедлайн по предмету {task['subject']}!❗\nЗадание: {task['task']}"
                )
        await asyncio.sleep(3600)


USER_HOMEWORK_DIR = "homework_data/"

# Функция загрузки домашнего задания для конкретного пользователя
def load_homework(user_id):
    user_homework_file = f"{USER_HOMEWORK_DIR}{user_id}_homework.json"
    if os.path.exists(user_homework_file):
        with open(user_homework_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Функция сохранения домашнего задания для конкретного пользователя
def save_homework(user_id, homework_data):
    user_homework_file = f"{USER_HOMEWORK_DIR}{user_id}_homework.json"
    os.makedirs(USER_HOMEWORK_DIR, exist_ok=True)
    with open(user_homework_file, "w", encoding="utf-8") as f:
        json.dump(homework_data, f, ensure_ascii=False, indent=4)


async def main():
    logging.basicConfig(level=logging.INFO)
    asyncio.create_task(send_deadline_reminders())
    await bot.delete_webhook(drop_pending_updates=True)
    loop = asyncio.get_event_loop()
    loop.create_task(send_tomorrow_schedule())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())