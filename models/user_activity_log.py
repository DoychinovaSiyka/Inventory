import uuid
from datetime import datetime


class UserActivityLog:
    def __init__(self, user_id, action, details="", timestamp=None, log_id=None):
        """ Модел за лог запис. timestamp се подава винаги отвън (Controller)."""
        # Уникален идентификатор на лог записа (UUID)
        self.log_id = str(log_id) if log_id else str(uuid.uuid4())
        # Кой потребител е извършил действието
        self.user_id = str(user_id)
        # Какво действие е извършено
        self.action = str(action)
        # Допълнителни детайли
        self.details = str(details)
        # Време на извършване
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {"log_id": self.log_id, "user_id": self.user_id,
                "action": self.action, "details": self.details,
                "timestamp": self.timestamp }

    @staticmethod
    def from_dict(data):
        return UserActivityLog(log_id=data.get("log_id"), user_id=data.get("user_id"),
                               action=data.get("action"), details=data.get("details", ""),
                               timestamp=data.get("timestamp"))

    def __str__(self):
        return f"[{self.timestamp}] {self.user_id} → {self.action}"
