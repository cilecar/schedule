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

logging.basicConfig(level=logging.INFO)  # Устанавливаем уровень логирования на INFO
logger = logging.getLogger(__name__)

class HomeworkState(StatesGroup):
    adding = State()
    changing = State()
    choosing_subject = State()
    changing_subject = State()
    attaching_file = State()
    entering_task = State()
    entering_due_date = State()
    changing = State()
    changing_time = State()
    changing_deadline_time = State()
    sending_global_message = State()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Расписание на сегодня")],
        [KeyboardButton(text="Расписание на завтра")],
        [KeyboardButton(text="Полное расписание")],
        [KeyboardButton(text="Добавить домашнее задание")],
        [KeyboardButton(text="Посмотреть домашние задания")],
        [KeyboardButton(text="Изменить статус задания")],
        [KeyboardButton(text="Настройка уведомлений")]  # Новая кнопка
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

schedule_subjects = [
        "Интегралы и дифференциальные уравнения", 
        "Линейная алгебра и функция нескольких переменных", 
        "История информационного противоборства", 
        "Право", 
        "Основы информационной безопасности", 
        "Иностранный язык", 
        "Социальные и этические вопросы в информационной сфере", 
        "История России", 
        "Физика", 
        "Основы программирования", 
        "Дискретная математика"
    ]
homework = []

# Функция для загрузки настроек оповещений
def load_user_settings(user_id):
    default_settings = {
        "notifications_enabled": True,
        "notification_time": "20:00",
        "deadline_notifications_enabled": True,
        "deadline_notification_time": "12:00"
    }
    if os.path.exists("users_settings.json"):
        with open("users_settings.json", "r", encoding="utf-8") as f:
            settings = json.load(f)
            return settings.get(str(user_id), default_settings)
    return default_settings  # По умолчанию уведомления включены и время 20:00 и 12:00

# Функция для сохранения настроек оповещений
def save_user_settings(user_id, settings_data):
    if os.path.exists("users_settings.json"):
        with open("users_settings.json", "r", encoding="utf-8") as f:
            settings = json.load(f)
    else:
        settings = {}

    settings[str(user_id)] = settings_data

    with open("users_settings.json", "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

# Функция для загрузки списка пользователей
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Функция для сохранения списка пользователей
def save_users(users):
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)


@dp.message(Command("send_global_message"))
async def send_global_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id != 706172589:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    await message.answer("Введите сообщение для отправки всем пользователям:")
    await state.set_state(HomeworkState.sending_global_message)

@dp.message(HomeworkState.sending_global_message)
async def process_global_message(message: types.Message, state: FSMContext):
    global_message = message.text.strip()
    formatted_message = f"❗️Сообщение от администратора❗️\n\n{global_message}"
    users = load_users()

    for user_id in users:
        try:
            await bot.send_message(user_id, formatted_message)
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

    await state.clear()
    await message.answer("Сообщение отправлено всем пользователям.")

@dp.message(F.text == "Управление оповещениями о завтрашних парах")
async def toggle_notifications(message: types.Message):
    user_id = message.from_user.id
    settings = load_user_settings(user_id)

    settings["notifications_enabled"] = not settings["notifications_enabled"]
    
    save_user_settings(user_id, settings)

    status = "включены" if settings["notifications_enabled"] else "выключены"
    await message.answer(f"Оповещения о завтрашних парах {status}.")


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
    user_id = message.from_user.id  # Получаем ID пользователя
    add_user(user_id)  # Добавляем пользователя в список
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
    await message.answer(f"Сейчас {current_week}-я неделя.\n\n" + "\n".join(response))



# Функция для добавления нового пользователя в список
def add_user(user_id):
    if os.path.exists("users.json"):
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    else:
        users = []
    
    if user_id not in users:
        users.append(user_id)
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=4)

# Функция изменения времени оповещения
@dp.message(F.text == "Изменить время оповещения")
async def change_notification_time(message: types.Message, state: FSMContext):
    await message.answer("Введите новое время оповещения в формате ЧЧ:ММ:")
    await state.set_state(HomeworkState.changing_time)  # Используем новое состояние


# Обработка нового времени
@dp.message(HomeworkState.changing_time)
async def process_new_time(message: types.Message, state: FSMContext):
    new_time = message.text.strip()
    try:
        datetime.strptime(new_time, "%H:%M")
        user_id = message.from_user.id
        settings = load_user_settings(user_id)
        settings["notification_time"] = new_time
        save_user_settings(user_id, settings)
        await message.answer(f"Время оповещения изменено на {new_time}.")
        await state.clear()  # Очищаем состояние
    except ValueError:
        await message.answer("Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.")




# Функция напоминания о завтрашних парах
sent_notifications = set()  # Храним пользователей, которым уже отправили сообщение

async def send_tomorrow_schedule():
    global sent_notifications
    
    while True:
        now = datetime.now()

        if os.path.exists("users_settings.json"):
            with open("users_settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)

            for user_id, user_settings in settings.items():
                if user_settings.get("notifications_enabled", True):
                    notification_time = user_settings.get("notification_time", "22:45")
                    hour, minute = map(int, notification_time.split(":"))

                    if now.hour == hour and now.minute == minute:
                        # Проверяем, не отправляли ли уже сегодня уведомление этому пользователю
                        if user_id in sent_notifications:
                            continue  # Если уже отправлено, пропускаем

                        SEMESTER_START = datetime(2024, 9, 2)
                        weeks_passed = (now - SEMESTER_START).days // 7
                        current_week = "1" if weeks_passed % 2 == 0 else "2"

                        tomorrow_day = (datetime.today() + timedelta(days=1)).strftime("%A")
                        days_map = {
                            "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
                        }

                        tomorrow_name = days_map.get(tomorrow_day, tomorrow_day)
                        response = schedule.get(current_week, {}).get(tomorrow_name, ["На завтра пар нет."])

                        try:
                            await bot.send_message(user_id, f"📅 Завтра у тебя:\n" + "\n".join(response))
                            sent_notifications.add(user_id)  # Запоминаем, что отправили
                        except Exception as e:
                            logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

        # Если уже наступил новый день – сбрасываем список отправленных уведомлений
        if now.hour == 0 and now.minute == 0:
            sent_notifications.clear()

        await asyncio.sleep(1)  # Проверяем каждую минуту





# Функция для проверки изменений в настройках
async def check_for_changes():
    previous_settings = None

    while True:
        current_settings = load_user_settings()

        if current_settings != previous_settings:
            logger.info("Изменения в настройках найдены!")
            previous_settings = current_settings
        else:
            logger.info("Изменений не найдено.")

        await asyncio.sleep(10)

# Запуск фоновой задачи для проверки изменений
async def main():
    asyncio.create_task(check_for_changes())
    asyncio.create_task(send_tomorrow_schedule())  # Запускаем задачу для отправки оповещений






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

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = {"pdf", "docx", "png", "jpeg", "jpg"}

@dp.message(HomeworkState.attaching_file, F.document)
async def receive_file(message: types.Message, state: FSMContext):
    file_name = message.document.file_name
    file_extension = file_name.split(".")[-1].lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        await message.answer("⚠ Этот формат файла не поддерживается. Разрешены только PDF, DOCX, PNG, JPEG, JPG.")
        return

    file_id = message.document.file_id
    await state.update_data(file_id=file_id, file_name=file_name)
    await state.set_state(HomeworkState.entering_due_date)
    await message.answer("Введите срок выполнения (в формате ДД.ММ.ГГГГ):")


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
        due_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        if due_date < datetime.now().date():
            await message.answer("Некорректная дата. Дата не может быть в прошлом. Введите дату в формате ДД.ММ.ГГГГ.")
            return
        if due_date > datetime(2030, 12, 31).date():
            await message.answer("Некорректная дата. Дата не может быть позже 31.12.2030. Введите дату в формате ДД.ММ.ГГГГ.")
            return
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
        "date_added": datetime.now().strftime("%d.%м.%Y"),
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
            response = (
                f"Статус: {task['status']}\n"
                f"Предмет: {task['subject']}\n"
                f"Задание: {task['task']}\n"
                f"Сделать: до {task['due_date']}\n"
                f"Дата добавления: {task['date_added']}"
            )
            
            if task.get("file_id"):
                response += f"\nПрикрепленный файл: {task['file_name']}"
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
    
    await message.answer(f"Выберите новый статус для задания:\n <b>{selected_task['task']}</b>", reply_markup=keyboard, parse_mode="HTML")

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




@dp.message(F.text == "Управление оповещениями о дедлайнах")
async def toggle_deadline_notifications(message: types.Message):
    user_id = message.from_user.id
    settings = load_user_settings(user_id)

    settings["deadline_notifications_enabled"] = not settings.get("deadline_notifications_enabled", True)
    
    save_user_settings(user_id, settings)

    status = "включены" if settings["deadline_notifications_enabled"] else "выключены"
    await message.answer(f"Оповещения о дедлайнах {status}.")

@dp.message(F.text == "Изменить время оповещения о дедлайнах")
async def change_deadline_notification_time(message: types.Message, state: FSMContext):
    await message.answer("Введите новое время оповещения о дедлайнах в формате ЧЧ:ММ:")
    await state.set_state(HomeworkState.changing_deadline_time)  # Используем новое состояние

@dp.message(HomeworkState.changing_deadline_time)
async def process_new_deadline_time(message: types.Message, state: FSMContext):
    new_time = message.text.strip()
    try:
        datetime.strptime(new_time, "%H:%M")
        user_id = message.from_user.id
        settings = load_user_settings(user_id)
        settings["deadline_notification_time"] = new_time
        save_user_settings(user_id, settings)
        await message.answer(f"Время оповещения о дедлайнах изменено на {new_time}.")
        await state.clear()  # Очищаем состояние
    except ValueError:
        await message.answer("Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.")


# Функция напоминания о дедлайнах
sent_deadline_notifications = set()  # Храним пользователей, которым уже отправили сообщение


async def send_deadline_reminders():
    global sent_deadline_notifications
    
    logger.info("Фоновая задача для отправки оповещений о дедлайнах запущена")
    
    while True:
        now = datetime.now()
        logger.info(f"Текущее время: {now.strftime('%H:%M')}")

        if os.path.exists("users_settings.json"):
            with open("users_settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)

            for user_id, user_settings in settings.items():
                if user_settings.get("deadline_notifications_enabled", True):
                    notification_time = user_settings.get("deadline_notification_time", "12:00")
                    hour, minute = map(int, notification_time.split(":"))

                    if now.hour == hour and now.minute == minute:
                        logger.info(f"Проверка уведомлений для пользователя {user_id} в {now.strftime('%H:%M')}")
                        # Проверяем, не отправляли ли уже сегодня уведомление этому пользователю
                        if user_id in sent_deadline_notifications:
                            logger.info(f"Уведомление уже отправлено пользователю {user_id} сегодня")
                            continue  # Если уже отправлено, пропускаем

                        homework = load_homework(user_id)
                        logger.info(f"Загружено {len(homework)} заданий для пользователя {user_id}")
                        for task in homework:
                            try:
                                due_date = datetime.strptime(task["due_date"], "%d.%m.%Y").date()
                                logger.info(f"Проверка задания: {task['task']} с дедлайном {due_date.strftime('%d.%m.%Y')}")
                                logger.info(f"Сравнение дат: {due_date - timedelta(days=1)} и {now.date()}")
                                if due_date - timedelta(days=1) == now.date():
                                    logger.info(f"Задание {task['task']} имеет дедлайн завтра")
                                    if task["status"] == "Не выполнено ❌":
                                        logger.info(f"Задание {task['task']} не выполнено, отправка уведомления")
                                        try:
                                            response = (
                                                "❗️Напоминание, завтра дедлайн❗️\n"
                                                f"Предмет: {task['subject']}\n"
                                                f"Задание: {task['task']}\n"
                                                f"Сделать: до {task['due_date']}\n"
                                                f"Дата добавления: {task['date_added']}"
                                            )
                                            if task.get("file_id"):
                                                response += f"\nПрикрепленный файл: {task['file_name']}"
                                                await bot.send_document(user_id, task["file_id"], caption=response)
                                            else:
                                                await bot.send_message(user_id, response)
                                            sent_deadline_notifications.add(user_id)  # Запоминаем, что отправили
                                            logger.info(f"Уведомление отправлено пользователю {user_id} по заданию {task['task']}")
                                        except Exception as e:
                                            logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
                                    else:
                                        logger.info(f"Задание {task['task']} уже выполнено")
                                else:
                                    logger.info(f"Задание {task['task']} не имеет дедлайн завтра")
                            except ValueError as e:
                                logging.error(f"Ошибка при разборе даты дедлайна для пользователя {user_id}: {e}")

        # Если уже наступил новый день – сбрасываем список отправленных уведомлений
        if now.hour == 0 and now.minute == 0:
            sent_deadline_notifications.clear()

        await asyncio.sleep(10)


@dp.message(F.text == "Настройка уведомлений")
async def notification_settings(message: types.Message):
    user_id = message.from_user.id
    settings = load_user_settings(user_id)

    notifications_status = "включено" if settings.get("notifications_enabled", True) else "выключено"
    deadline_notifications_status = "включено" if settings.get("deadline_notifications_enabled", True) else "выключено"
    notification_time = settings.get("notification_time", "20:00")
    deadline_notification_time = settings.get("deadline_notification_time", "12:00")

    response = (
        f"1. Оповещение о завтрашних парах: {notifications_status}\n"
        f"2. Время оповещения о завтрашних парах: {notification_time}\n"
        f"3. Оповещение о дедлайне: {deadline_notifications_status}\n"
        f"4. Время оповещения о дедлайне: {deadline_notification_time}\n\n"
        "Что хотите изменить?"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'Выключить' if settings.get('notifications_enabled', True) else 'Включить'} оповещение расписания", callback_data="toggle_schedule_notifications")],
        [InlineKeyboardButton(text="Время оповещения расписания", callback_data="change_schedule_notification_time")],
        [InlineKeyboardButton(text=f"{'Выключить' if settings.get('deadline_notifications_enabled', True) else 'Включить'} оповещение о дедлайне", callback_data="toggle_deadline_notifications")],
        [InlineKeyboardButton(text="Время оповещения о дедлайне", callback_data="change_deadline_notification_time")],
        [InlineKeyboardButton(text="🚫 Отмена", callback_data="cancel")]
    ])

    await message.answer(response, reply_markup=keyboard)


@dp.callback_query(lambda c: c.data in ["toggle_schedule_notifications", "change_schedule_notification_time", "toggle_deadline_notifications", "change_deadline_notification_time", "cancel"])
async def process_notification_settings(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    settings = load_user_settings(user_id)

    if callback_query.data == "toggle_schedule_notifications":
        settings["notifications_enabled"] = not settings.get("notifications_enabled", True)
        save_user_settings(user_id, settings)
        status = "включены" if settings["notifications_enabled"] else "выключены"
        await callback_query.message.edit_text(f"Оповещения о завтрашних парах {status}.")
    elif callback_query.data == "change_schedule_notification_time":
        await callback_query.message.answer("Введите новое время оповещения в формате ЧЧ:ММ:")
        await state.set_state(HomeworkState.changing_time)
    elif callback_query.data == "toggle_deadline_notifications":
        settings["deadline_notifications_enabled"] = not settings.get("deadline_notifications_enabled", True)
        save_user_settings(user_id, settings)
        status = "включены" if settings["deadline_notifications_enabled"] else "выключены"
        await callback_query.message.edit_text(f"Оповещения о дедлайнах {status}.")
    elif callback_query.data == "change_deadline_notification_time":
        await callback_query.message.answer("Введите новое время оповещения о дедлайнах в формате ЧЧ:ММ:")
        await state.set_state(HomeworkState.changing_deadline_time)
    elif callback_query.data == "cancel":
        await callback_query.message.edit_text("Действие отменено.")
        await state.clear()

    await callback_query.answer()

@dp.message(HomeworkState.changing_time)
async def process_new_time(message: types.Message, state: FSMContext):
    new_time = message.text.strip()
    try:
        datetime.strptime(new_time, "%H:%M")
        user_id = message.from_user.id
        settings = load_user_settings(user_id)
        settings["notification_time"] = new_time
        save_user_settings(user_id, settings)
        await message.answer(f"Время оповещения изменено на {new_time}.")
        await state.clear()  # Очищаем состояние
    except ValueError:
        await message.answer("Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.")

@dp.message(HomeworkState.changing_deadline_time)
async def process_new_deadline_time(message: types.Message, state: FSMContext):
    new_time = message.text.strip()
    try:
        datetime.strptime(new_time, "%H:%M")
        user_id = message.from_user.id
        settings = load_user_settings(user_id)
        settings["deadline_notification_time"] = new_time
        save_user_settings(user_id, settings)
        await message.answer(f"Время оповещения о дедлайнах изменено на {new_time}.")
        await state.clear()  # Очищаем состояние
    except ValueError:
        await message.answer("Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.")

# Запуск фоновой задачи для отправки оповещений о дедлайнах
async def main():
    asyncio.create_task(send_deadline_reminders())
    asyncio.create_task(send_tomorrow_schedule())  # Запускаем задачу для отправки оповещений
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())