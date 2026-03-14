import datetime
import uuid

class UserActivityLog:
    def __init__(self, user_id, action, details="", timestamp=None, log_id=None):
        # Уникален идентификатор на лог записа (UUID)
        self.log_id = log_id or str(uuid.uuid4())

        # Кой потребител е извършил действието
        self.user_id = user_id

        # Какво действие е извършено
        self.action = action

        # Допълнителни детайли
        self.details = details

        # Време на извършване
        self.timestamp = timestamp or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "user_id": self.user_id,
            "action": self.action,
            "details": self.details,
            "timestamp": self.timestamp
        }

    @staticmethod
    def from_dict(data):
        return UserActivityLog(
            log_id=data.get("log_id"),
            user_id=data["user_id"],
            action=data["action"],
            details=data.get("details", ""),
            timestamp=data.get("timestamp")
        )
