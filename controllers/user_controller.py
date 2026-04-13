from typing import Optional
from datetime import datetime
import uuid

from models.user import User
from storage.json_repository import JSONRepository
from validators.user_validator import UserValidator


class UserController:
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        self.users = [User.from_dict(u) for u in self.repo.load()]

        if not self.users:
            self._create_default_admin_and_operator()

        if not any(u.role == "Operator" for u in self.users):
            self._create_default_operator()

        self.logged_user: Optional[User] = None

    # INTERNAL HELPERS
    @staticmethod
    def _hash_password(password: str) -> str:
        return "".join(str(ord(c)) for c in password)

    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    def save_changes(self):
        self.repo.save([u.to_dict() for u in self.users])

    def _is_unique_username(self, username: str) -> bool:
        return not any(u.username == username for u in self.users)

    def get_by_id(self, user_id: str) -> Optional[User]:
        return next((u for u in self.users if u.user_id == user_id), None)

    def get_by_username(self, username: str) -> Optional[User]:
        return next((u for u in self.users if u.username == username), None)

    # DEFAULT USERS
    def _create_default_admin_and_operator(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        admin = User(
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            username="admin",
            password=self._hash_password("admin123"),
            role="Admin",
            status="Active",
            created=now,
            modified=now
        )

        operator = User(
            first_name="Operator",
            last_name="User",
            email="operator@example.com",
            username="operator",
            password=self._hash_password("operator123"),
            role="Operator",
            status="Active",
            created=now,
            modified=now
        )

        self.users.extend([admin, operator])
        self.save_changes()

    def _create_default_operator(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        operator = User(
            first_name="Operator",
            last_name="User",
            email="operator@example.com",
            username="operator",
            password=self._hash_password("operator123"),
            role="Operator",
            status="Active",
            created=now,
            modified=now
        )
        self.users.append(operator)
        self.save_changes()

    # REGISTER
    def register(self, first_name, last_name, email, username, password, role="Operator"):
        UserValidator.validate_user_data(username, password, email, role, "Active")

        if not self._is_unique_username(username):
            raise ValueError("Потребителското име вече съществува.")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            password=self._hash_password(password),
            role=role,
            status="Active",
            created=now,
            modified=now
        )

        self.users.append(new_user)
        self.save_changes()
        return new_user

    # LOGIN — паролата се подава отвън
    def login(self, username: str, password: str) -> Optional[User]:
        hashed = self._hash_password(password)

        for user in self.users:
            if user.username == username and user.password == hashed:
                if user.status != "Active":
                    return None
                self.logged_user = user
                return user

        return None

    # ROLE MANAGEMENT
    def change_role(self, acting_user: User, username: str, new_role: str):
        if acting_user.role != "Admin":
            raise PermissionError("Само администратор може да променя роли.")

        UserValidator.validate_role(new_role)

        user = self.get_by_username(username)
        if not user:
            raise ValueError("Потребителят не е намерен.")

        user.role = new_role
        user.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_changes()
        return True

    # STATUS MANAGEMENT
    def deactivate_user(self, acting_user: User, username: str):
        if acting_user.role != "Admin":
            raise PermissionError("Само администратор може да деактивира потребители.")

        user = self.get_by_username(username)
        if not user:
            raise ValueError("Потребителят не е намерен.")

        user.status = "Inactive"
        user.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_changes()
        return True

    def activate_user(self, acting_user: User, username: str):
        if acting_user.role != "Admin":
            raise PermissionError("Само администратор може да активира потребители.")

        user = self.get_by_username(username)
        if not user:
            raise ValueError("Потребителят не е намерен.")

        user.status = "Active"
        user.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_changes()
        return True

    # DELETE USER
    def delete_user(self, acting_user: User, username: str):
        if acting_user.role != "Admin":
            raise PermissionError("Само администратор може да изтрива потребители.")

        if acting_user.username == username:
            raise ValueError("Администраторът не може да изтрие собствения си акаунт.")

        user = self.get_by_username(username)
        if not user:
            raise ValueError("Потребителят не е намерен.")

        self.users.remove(user)
        self.save_changes()
        return True

    # LIST USERS
    def get_all(self):
        return self.users
