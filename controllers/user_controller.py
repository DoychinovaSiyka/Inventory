from typing import Optional, List
from datetime import datetime
import uuid
from models.user import User
from validators.user_validator import UserValidator


class UserController:
    def __init__(self, repo):
        self.repo = repo
        # Зареждаме потребителите от репозиторито
        raw_data = self.repo.load()
        self.users: List[User] = []

        if isinstance(raw_data, list):
            for u in raw_data:
                if isinstance(u, dict):
                    self.users.append(User.from_dict(u))

        self.logged_user: Optional[User] = None

        # Ако няма потребители -> създаваме начален администратор и оператор
        if not self.users:
            self._bootstrap_system()
        else:
            # Ако няма администратор -> създаваме
            if not any(u.role == "Admin" for u in self.users):
                self._create_default_admin()

            # Ако няма оператор -> създаваме
            if not any(u.role == "Operator" for u in self.users):
                self._create_default_operator()

    def _get_now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _hash_password(self, password: str) -> str:
        return "".join(str(ord(c)) for c in password)

    # Запис в JSON
    def save_changes(self):
        self.repo.save([u.to_dict() for u in self.users])

    # READ
    def get_by_username(self, username: str) -> Optional[User]:
        for u in self.users:
            if u.username == username:
                return u
        return None

    def get_all(self):
        return self.users

    # AUTH
    def login(self, username: str, password: str) -> Optional[User]:
        hashed = self._hash_password(password)
        user = self.get_by_username(username)

        if user and user.password == hashed and user.status == "Active":
            self.logged_user = user
            return user

        return None

    # ADMIN ACTIONS
    def register(self, first_name, last_name, email, username, password, role="Operator"):
        # Комплексна валидация
        UserValidator.validate_user_data(username, password, email, role, "Active")

        if self.get_by_username(username):
            raise ValueError("Потребителското име вече съществува.")

        new_user = User(
            user_id=str(uuid.uuid4()),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=email.strip(),
            username=username.strip(),
            password=self._hash_password(password),
            role=role,
            status="Active",
            created=self._get_now(),
            modified=self._get_now()
        )

        self.users.append(new_user)
        self.save_changes()
        return new_user

    # Промяна на роля (реалистична логика)
    def change_role(self, username, new_role):
        user = self.get_by_username(username)
        if not user:
            raise ValueError("Няма такъв потребител.")
        # Не може да сменяш роля със същата
        if user.role == new_role:
            raise ValueError(f"Потребителят вече има роля '{new_role}'.")

        if new_role not in ["Admin", "Operator"]:
            raise ValueError("Невалидна роля.")

        user.role = new_role
        user.modified = self._get_now()
        self.save_changes()

    # Промяна на статус
    def change_status(self, acting_user: User, target_username: str, new_status: str):
        UserValidator.confirm_admin(acting_user)
        UserValidator.validate_status(new_status)
        user = self.get_by_username(target_username)
        if not user:
            raise ValueError("Потребителят не е намерен.")

        # Не може да сменяш със същия статус
        if user.status == new_status:
            raise ValueError(f"Потребителят вече е в статус '{new_status}'.")

        user.status = new_status
        user.modified = self._get_now()
        self.save_changes()
        return True

    # Изтриване на потребител
    def delete_user(self, acting_user: User, target_username: str):
        UserValidator.confirm_admin(acting_user)
        UserValidator.validate_not_self(acting_user.username, target_username)

        user = self.get_by_username(target_username)
        if not user:
            raise ValueError("Потребителят не е намерен.")

        # Защита от премахване на последния админ
        UserValidator.validate_not_last_admin(user, self.users)
        self.users.remove(user)
        self.save_changes()
        return True

    # BOOTSTRAP LOGIC
    def _bootstrap_system(self):
        self._create_default_admin()
        self._create_default_operator()

    def _create_default_admin(self):
        self.register(
            "Admin",
            "System",
            "admin@stock.com",
            "admin",
            "admin123",
            role="Admin"
        )

    def _create_default_operator(self):
        self.register(
            "Ivan",
            "Petrov",
            "ivan@example.com",
            "ivan",
            "test123",
            role="Operator"
        )

    # ANONYMOUS USER FACTORY
    def create_anonymous_user(self) -> User:
        now = self._get_now()
        return User(
            user_id="guest-0000",
            first_name="Anonymous",
            last_name="",
            email="",
            username="guest",
            password="",
            role="Anonymous",
            status="Active",
            created=now,
            modified=now
        )
