import logging

class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Если поля отсутствуют, задаем значение по умолчанию
        if not hasattr(record, 'user_id'):
            record.user_id = 'N/A'
        if not hasattr(record, 'action'):
            record.action = 'N/A'
        if not hasattr(record, 'bot_response'):
            record.bot_response = 'N/A'
        return super().format(record)

# Создаем логгер для действий пользователей
logger = logging.getLogger("user_actions")
logger.setLevel(logging.INFO)

# Обработчик, который пишет логи в файл с поддержкой русских символов
file_handler = logging.FileHandler("/data/user_actions.log", encoding="utf-8")
file_handler.setLevel(logging.INFO)

# Задаем формат, включающий нужные поля
formatter = CustomFormatter('%(asctime)s, %(user_id)s, %(action)s, %(bot_response)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Адаптер для удобного логирования с дополнительными данными
class ActionLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = self.extra.copy()
        extra.update(kwargs.get("extra", {}))
        kwargs["extra"] = extra
        return msg, kwargs

action_logger = ActionLoggerAdapter(logger, {"user_id": "", "action": "", "bot_response": ""})

def log_action(user_id: int, action: str, bot_response: str):
    """Логирует действие пользователя."""
    action_logger.info("", extra={"user_id": user_id, "action": action, "bot_response": bot_response})