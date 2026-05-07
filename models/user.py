import uuid
from datetime import datetime

class User:
    def __init__(self, first_name, last_name, email, username, password,
                 role="Operator", status="Active", user_id=None, created=None, modified=None):

        # 1. ГЕНЕРИРАНЕ: Вече пазим пълното 36-символно UUID за сигурност в базата
        if not user_id:
            self.user_id = str(uuid.uuid4())
        else:
            self.user_id = str(user_id)

        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.username = username
        self.password = password
        self.role = role # Роля: Admin, Operator и т.н.
        self.status = status # Статус: Active, Inactive

        now_val = User.now()
        self.created = created or now_val
        self.modified = modified or now_val

    @staticmethod
    def now():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def update_modified(self):
        """Обновява датата при промяна на потребителя."""
        self.modified = User.now()

    @staticmethod
    def from_dict(data):
        """Превръща речник от JSON в обект User."""
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
        """Връща User като речник за JSON запис (с пълното ID)."""
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
        # 2. ВИЗУАЛИЗАЦИЯ: Само тук показваме първите 8 символа
        short_id = self.user_id[:8]
        return f"Потребител: {self.username} [ID: {short_id}] | Роля: {self.role} | Статус: {self.status}"