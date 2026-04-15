import uuid
from datetime import datetime


class User:
    def __init__(self, first_name, last_name, email, username, password,
                 role="Operator", status="Active", user_id=None, created=None, modified=None):

        """ Модел за потребител. ID-то идва от контролера или от JSON файла.
        Ако липсва, се генерира нов UUID. Датите (created/modified) също се подават от контролера,
        за да има синхрон в системата. """

        self.user_id = str(user_id) if user_id else str(uuid.uuid4())
        self.id = self.user_id  # съвместимост със стар код
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.username = username
        self.password = password
        # Роля: Admin / Operator / Anonymous
        self.role = role
        # Статус: Active / Disabled / Blocked
        self.status = status
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created = created or now
        self.modified = modified or now

    def update_modified(self):
        """Обновява датата на последна промяна."""
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def from_dict(data):
        """Създава User от JSON речник."""
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
        """Конвертира User към JSON речник."""
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
