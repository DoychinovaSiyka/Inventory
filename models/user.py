

import uuid
from datetime import datetime


class User:
    def __init__(self, first_name, last_name, email, username, password,
                 role="operator", status="active",
                 user_id=None, created=None, modified=None):

        self.user_id = user_id or str(uuid.uuid4())

        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.username = username
        self.password = password

        # Роля: anonymous / operator / admin
        self.role = role

        # Статус: active / inactive
        self.status = status

        self.created = created or datetime.now().isoformat()
        self.modified = modified or datetime.now().isoformat()

    def update_modified(self):
        self.modified = datetime.now().isoformat()

    @staticmethod
    def from_dict(data):
        return User(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            username=data["username"],
            password=data["password"],
            role=data.get("role", "operator"),
            status=data.get("status", "active"),
            user_id=data.get("user_id"),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def to_dict(self):
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

