from typing import Optional, List
from models.user import User
from validators.user_validator import UserValidator


class UserController:
    """Контролерът управлява потребителите. При първо стартиране създава админ и оператор."""

    def __init__(self, repo):
        self.repo = repo
        raw_data = self.repo.load()
        if not raw_data or not isinstance(raw_data, list):
            raw_data = []

        # Зареждам потребителите от JSON файла
        self.users: List[User] = []
        for u in raw_data:
            if isinstance(u, dict):
                self.users.append(User.from_dict(u))

        self.logged_user: Optional[User] = None

        # Проверявам дали има админ и оператор – по студентски, без any()
        has_admin = False
        has_operator = False

        for u in self.users:
            if u.role == "Admin":
                has_admin = True
            if u.role == "Operator":
                has_operator = True

        # Ако няма потребители – създавам и двамата
        if not self.users:
            self._create_default_admin()
            self._create_default_operator()
        else:
            if not has_admin:
                self._create_default_admin()
            if not has_operator:
                self._create_default_operator()

    def _hash_password(self, password: str) -> str:
        """Прост хеш механизъм за пароли."""
        return "".join(str(ord(c)) for c in password)

    def save_changes(self):
        """Записва промените в JSON файла."""
        self.repo.save([u.to_dict() for u in self.users])

    # READ операции
    def get_by_username(self, username: str) -> Optional[User]:
        for u in self.users:
            if u.username == username:
                return u
        return None

    def get_all(self):
        return self.users

    def get_by_id(self, user_id: str) -> Optional[User]:
        user_id = str(user_id)
        for u in self.users:
            if u.user_id == user_id:
                return u
        return None

    # Логин логика
    def login(self, username: str, password: str) -> Optional[User]:
        if not self.users:
            return None

        user = UserValidator.validate_login(username, password, self)
        hashed = self._hash_password(password)

        if user.password == hashed:
            self.logged_user = user
            return user
        return None

    # Администраторски действия
    def register(self, first_name, last_name, email, username, password, role="Operator"):
        UserValidator.validate_user_data(username, password, email, role, "Active")
        UserValidator.validate_unique_username(username, self)


        new_user = User(first_name=first_name.strip(), last_name=last_name.strip(),
                        email=email.strip(), username=username.strip(),
                        password=self._hash_password(password), role=role, status="Active")

        self.users.append(new_user)
        self.save_changes()
        return new_user

    def change_role(self, username, new_role):
        user = UserValidator.validate_exists(username, self)
        UserValidator.validate_role(new_role)

        if user.role == new_role:
            raise ValueError(f"Потребителят вече има роля '{new_role}'.")

        user.role = new_role
        user.update_modified()
        self.save_changes()

    def change_status(self, acting_user: User, target_username: str, new_status: str):
        UserValidator.confirm_admin(acting_user)
        UserValidator.validate_status(new_status)

        user = UserValidator.validate_exists(target_username, self)
        if user.status == new_status:
            raise ValueError(f"Потребителят вече е в статус '{new_status}'.")

        user.status = new_status
        user.update_modified()
        self.save_changes()
        return True

    def delete_user(self, acting_user: User, target_username: str):
        UserValidator.confirm_admin(acting_user)
        UserValidator.validate_not_self(acting_user.username, target_username)

        user = UserValidator.validate_exists(target_username, self)
        UserValidator.validate_not_last_admin(user, self.users)

        self.users.remove(user)
        self.save_changes()
        return True

    # Създаване на начални потребители
    def _create_default_admin(self):
        admin = User(first_name="Admin", last_name="System",
                     email="admin@system.local", username="admin",
                     password=self._hash_password("admin123"), role="Admin", status="Active")
        self.users.append(admin)
        self.save_changes()

    def _create_default_operator(self):
        operator = User(first_name="Operator", last_name="User", email="operator@example.com",
                        username="operator", password=self._hash_password("operator123"),
                        role="Operator", status="Active")
        self.users.append(operator)
        self.save_changes()


    # Анонимен потребител
    def create_anonymous_user(self) -> User:
        now = User.now()
        return User(user_id="guest-0000", first_name="Anonymous", last_name="",
                    email="", username="guest", password="", role="Anonymous", status="Active",
                    created=now, modified=now)