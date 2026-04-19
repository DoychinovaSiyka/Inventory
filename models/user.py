import uuid
from datetime import datetime


class User:
    def __init__(self, first_name, last_name, email, username, password,
                 role="Operator", status="Active", user_id=None, created=None, modified=None):

        # ID-то може да е от JSON или да се генерира ново
        self.user_id = str(user_id) if user_id else str(uuid.uuid4())
        self.id = self.user_id  # за съвместимост със стар код

        # Основни данни за потребителя
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.username = username
        self.password = password

        # Роля в системата
        self.role = role

        # Статус на акаунта
        self.status = status

        # Дати на създаване и последна промяна
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created = created or now
        self.modified = modified or now

    def update_modified(self):
        """Обновява датата при промяна на потребителя."""
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def from_dict(data):
        """Създава User обект от JSON речник."""
        if not data:
            return None

        return User(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            email=data.get("email", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
            role=data.get("role", "Operator"),
            status=data.get("status", "Active"),
            user_id=data.get("user_id"),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def to_dict(self):
        """Конвертира User обекта към JSON речник."""
        return {
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "status": self.status,
            "created": self.created,
            "modified": self.modified
        }

    def __str__(self):
        return f"{self.username} ({self.role})"
