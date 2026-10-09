from datetime import datetime
from zoneinfo import ZoneInfo

GLOBAL_SEMESTER_START = datetime(2024, 9, 2, tzinfo=ZoneInfo("Europe/Moscow"))

# Отображение дней недели
DAYS_MAP = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье"
}

# Расписание занятий
schedule = {
    "1": {
        "Четверг": [
            "13:10 - л.Основы военной подготовки. Сулейманов Р.А. https://eios.imsit.ru/course/view.php?id=12003",
            "14:50 - пр.Структуры и алгоритмы обработки данных Лисин Д.А. https://eios.imsit.ru/course/view.php?id=12007",
            "16:30 - л.Экономика Белухин В.В. https://eios.imsit.ru/course/view.php?id=12004"
        ],
        "Пятница": [
            "14:50 - пр.Иностранный язык. Чумичева Н.В. https://eios.imsit.ru/course/view.php?id=12025",
            "16:30 - л.Структуры и алгоритмы обработки данных Лисин Д.А. https://eios.imsit.ru/course/view.php?id=12007",
            "18:10 - л.Теория информации Лисин Д.А. https://eios.imsit.ru/course/view.php?id=12002"
        ],
        "Суббота": [
            "8:00 - пр.Вычислительные методы Лисина О.Ю. 1-208 https://eios.imsit.ru/course/view.php?id=12006",
            "9:40 - л.Основы национальной безопасности. Мадатова О.В. 1-303 https://eios.imsit.ru/course/view.php?id=11964"
        ]
    },
    "2": {
        "Четверг": [
            "13:10 - л.Экология Елисеева Н.В. https://eios.imsit.ru/course/view.php?id=11999",
            "14:50 - л.Экономика Белухин В.В. https://eios.imsit.ru/course/view.php?id=12004",
            "16:30 - пр.Экономика Белухин В.В. https://eios.imsit.ru/course/view.php?id=12004"
        ],
        "Пятница": [
            "14:50 - пр.Иностранный язык. Чумичева Н.В. https://eios.imsit.ru/course/view.php?id=12025",
            "16:30 - пр.Структуры и алгоритмы обработки данных Лисин Д.А. https://eios.imsit.ru/course/view.php?id=12007",
            "18:10 - пр.Теория информации Лисин Д.А. https://eios.imsit.ru/course/view.php?id=12002"
        ],
        "Суббота": [
            "8:00 - л.Вычислительные методы Лисина О.Ю. 1-208 https://eios.imsit.ru/course/view.php?id=12006",
            "9:40 - пр.Элементы алгебры и теории чисел Лисин Д.А. 1-113 https://eios.imsit.ru/course/view.php?id=12008"
        ]
    }
}

# Список предметов
schedule_subjects = [
    "Основы военной подготовки",
    "Структуры и алгоритмы обработки данных",
    "Экономика",
    "Иностранный язык",
    "Теория информации",
    "Вычислительные методы",
    "Основы национальной безопасности",
    "Экология",
    "Элементы алгебры и теории чисел"
]

ALLOWED_EXTENSIONS = {"pdf", "docx", "png", "jpeg", "jpg"}