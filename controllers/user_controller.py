from typing import List
from datetime import datetime
import uuid
from models.user import User
from validators.user_validator import UserValidator


class UserController:
    """Контролерът управлява потребителите. Работи коректно при празен users.json.
    При първо стартиране създава един администратор и един оператор."""
    def __init__(self, repo):
        self.repo = repo
        raw_data = self.repo.load()
        if raw_data is None or not isinstance(raw_data, list):
            raw_data = []

        self.users: List[User] = []

        # Зареждане на потребителите от JSON
        for item in raw_data:
            if isinstance(item, dict):
                user = User.from_dict(item)
                self.users.append(user)

        self.logged_user = None

        # Проверка за начални потребители
        if len(self.users) == 0:
            self._create_default_admin()
            self._create_default_operator()
        else:
            admin_exists = False
            operator_exists = False

            for u in self.users:
                if u.role == "Admin":
                    admin_exists = True
                if u.role == "Operator":
                    operator_exists = True

            if not admin_exists:
                self._create_default_admin()


            if not operator_exists:
                self._create_default_operator()

    def _get_now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _hash_password(self, password: str) -> str:
        result = ""
        for c in password:
            result += str(ord(c))
        return result

    def save_changes(self):
        data = []
        for u in self.users:
            data.append(u.to_dict())
        self.repo.save(data)

    # READ операции
    def get_by_username(self, username: str):
        for u in self.users:
            if u.username == username:
                return u
        return None

    def get_all(self):
        return self.users

    def get_by_id(self, user_id: str):
        for u in self.users:
            if u.user_id == user_id:
                return u
        return None

    # Логин
    def login(self, username: str, password: str):
        if len(self.users) == 0:
            return None

        user = UserValidator.validate_login(username, password, self)
        hashed = self._hash_password(password)
        if user.password == hashed:
            self.logged_user = user
            return user

        return None

    # Регистрация
    def register(self, first_name, last_name, email, username, password, role="Operator"):
        UserValidator.validate_user_data(username, password, email, role, "Active")
        UserValidator.validate_unique_username(username, self)

        new_user = User(user_id=str(uuid.uuid4()), first_name=first_name.strip(),
                        last_name=last_name.strip(), email=email.strip(),
                        username=username.strip(),
                        password=self._hash_password(password),
                        role=role, status="Active", created=self._get_now(),
                        modified=self._get_now())

        self.users.append(new_user)
        self.save_changes()
        return new_user

    # Смяна на роля
    def change_role(self, username, new_role):
        user = UserValidator.validate_exists(username, self)
        UserValidator.validate_role(new_role)

        if user.role == new_role:
            raise ValueError("Потребителят вече има тази роля.")

        user.role = new_role
        user.modified = self._get_now()
        self.save_changes()

    # Смяна на статус
    def change_status(self, acting_user, target_username, new_status):
        UserValidator.confirm_admin(acting_user)
        UserValidator.validate_status(new_status)

        user = UserValidator.validate_exists(target_username, self)
        if user.status == new_status:
            raise ValueError("Потребителят вече е в този статус.")

        user.status = new_status
        user.modified = self._get_now()
        self.save_changes()
        return True

    # Изтриване
    def delete_user(self, acting_user, target_username):
        UserValidator.confirm_admin(acting_user)
        UserValidator.validate_not_self(acting_user.username, target_username)

        user = UserValidator.validate_exists(target_username, self)
        UserValidator.validate_not_last_admin(user, self.users)
        self.users.remove(user)
        self.save_changes()
        return True

    # Начални потребители
    def _create_default_admin(self):
        """Създава администратор при първо стартиране."""
        admin = User(user_id=str(uuid.uuid4()), first_name="Admin",
                     last_name="System", email="admin@system.local",
                     username="admin", password=self._hash_password("admin123"),
                     role="Admin", status="Active", created=self._get_now(),
                     modified=self._get_now())

        self.users.append(admin)
        self.save_changes()

    def _create_default_operator(self):
        """Създава оператор, ако липсва такъв."""
        operator = User(user_id=str(uuid.uuid4()), first_name="Operator",
                        last_name="User", email="operator@example.com",
                        username="operator",
                        password=self._hash_password("operator123"),
                        role="Operator", status="Active",
                        created=self._get_now(), modified=self._get_now())

        self.users.append(operator)
        self.save_changes()

    # Гост потребител
    def create_anonymous_user(self):
        now = self._get_now()
        return User(user_id="guest-0000", first_name="Anonymous", last_name="",
                    email="", username="guest", password="", role="Anonymous",
                    status="Active", created=now, modified=now)

