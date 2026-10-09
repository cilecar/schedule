from pymongo import MongoClient
from config import MONGO_URI

# Подключение к MongoDB
client = MongoClient(MONGO_URI)
db = client["homework_bot"]
users_collection = db["users"]
settings_collection = db["settings"]
homework_collection = db["homework"]

def load_user_settings(user_id):
    default_settings = {
        "notifications_enabled": True,
        "notification_time": "20:00",
        "deadline_notifications_enabled": True,
        "deadline_notification_time": "12:00",
        "hide_completed_tasks": False
    }
    user_settings = settings_collection.find_one({"user_id": user_id})
    return user_settings or default_settings

def save_user_settings(user_id, settings_data):
    settings_collection.update_one(
        {"user_id": user_id},
        {"$set": settings_data},
        upsert=True
    )

def load_all_settings():
    return {str(doc["user_id"]): doc for doc in settings_collection.find()}

def load_users():
    return [doc["user_id"] for doc in users_collection.find()]

def save_users(users):
    users_collection.delete_many({})
    if users:
        users_collection.insert_many([{"user_id": user_id} for user_id in users])

def add_user(user_id):
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id})

def load_homework(user_id):
    return list(homework_collection.find({"user_id": user_id}))

def save_homework(user_id, homework_data):
    homework_collection.delete_many({"user_id": user_id})
    if homework_data:
        homework_collection.insert_many(
            {**task, "user_id": user_id} for task in homework_data
        )