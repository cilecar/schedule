import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

TOKEN = os.getenv("TOKEN")
HOMEWORK_DIR = os.getenv("HOMEWORK_DIR")
USERS_FILE = os.getenv("USERS_FILE")
SETTINGS_FILE = os.getenv("SETTINGS_FILE")
PAGE_SIZE = int(os.getenv("PAGE_SIZE", "5"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MONGO_URI = os.getenv("MONGO_URI")