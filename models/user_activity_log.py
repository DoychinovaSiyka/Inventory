import uuid
from datetime import datetime


class UserActivityLog:
    def __init__(self, user_id, action, details="", timestamp=None, log_id=None):
        """ Модел за лог запис. Проследява действията на потребителите. """

        # СИНХРОНИЗАЦИЯ: 8 символа за ID на самия лог
        if not log_id:
            self.log_id = str(uuid.uuid4())[:8]
        else:
            self.log_id = str(log_id)

        # СИНХРОНИЗАЦИЯ: user_id трябва да е 8 символа, за да съвпада с модела User
        self.user_id = str(user_id)[:8]

        self.action = str(action)  # Напр: "LOGIN", "CREATE_PRODUCT", "SALE"
        self.details = str(details)  # Допълнителна инфо (напр. "Продукт: Ябълки")

        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        """Превръща лог записа в речник за JSON съхранение."""
        return {
            "log_id": self.log_id,
            "user_id": self.user_id,
            "action": self.action,
            "details": self.details,
            "timestamp": self.timestamp
        }

    @staticmethod
    def from_dict(data):
        """Възстановява лог запис от речник."""
        if not data:
            return None
        return UserActivityLog(
            log_id=data.get("log_id"),
            user_id=data.get("user_id"),
            action=data.get("action"),
            details=data.get("details", ""),
            timestamp=data.get("timestamp")
        )

    def __str__(self):
        # Оптимизиран изглед за конзолата
        return f"[{self.timestamp}] Потр. ID: {self.user_id} | Действие: {self.action} | Детайли: {self.details}"