import uuid
from datetime import datetime


class UserActivityLog:
    def __init__(self, user_id, action, details="", timestamp=None, log_id=None):
        """ Модел за лог запис."""
        self.log_id = str(log_id) if log_id else str(uuid.uuid4())
        self.user_id = str(user_id)
        self.action = str(action) # Какво действие е извършено
        self.details = str(details) # Допълнителни детайли

        if timestamp:  # Време на извършване
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        """Превръща лог записа в речник за JSON."""
        return {"log_id": self.log_id, "user_id": self.user_id,
                "action": self.action, "details": self.details, "timestamp": self.timestamp}

    @staticmethod
    def from_dict(data):
        """Възстановява лог запис от речник."""
        if not data:
            return None
        return UserActivityLog(log_id=data.get("log_id"),
                               user_id=data.get("user_id"), action=data.get("action"),
                               details=data.get("details", ""), timestamp=data.get("timestamp"))

    def __str__(self):
        return f"[{self.timestamp}] Потребител: {self.user_id} -> Действие: {self.action}"