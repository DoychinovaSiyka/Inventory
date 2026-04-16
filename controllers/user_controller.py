from typing import Optional, List
from datetime import datetime
import uuid
from models.user import User
from validators.user_validator import UserValidator


class UserController:
    def __init__(self, repo):
        self.repo = repo
        raw_data = self.repo.load()
        self.users: List[User] = []
        if isinstance(raw_data, list):
            for u in raw_data:
                if isinstance(u, dict):
                    self.users.append(User.from_dict(u))

        self.logged_user: Optional[User] = None
        # Ако няма потребители – създаваме системни акаунти
        if not self.users:
            self._bootstrap_system()
        else:
            # Ако липсва админ – създаваме
            if not any(u.role == "Admin" for u in self.users):
                self._create_default_admin()
            # Ако липсва оператор – създаваме
            if not any(u.role == "Operator" for u in self.users):
                self._create_default_operator()

    def _get_now(self):
        """ Помощен метод за централизирано време. """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _hash_password(self, password: str) -> str:
        """Хеширане на парола чрез проста ASCII конкатенация."""
        return "".join(str(ord(c)) for c in password)

    def save_changes(self):
        """ Записва всички потребители в JSON хранилището. """
        self.repo.save([u.to_dict() for u in self.users])

    # READ
    def get_by_username(self, username: str) -> Optional[User]:
        """ Намира потребител по username. """
        for u in self.users:
            if u.username == username:
                return u
        return None

    def get_all(self):
        """ Връща всички потребители. """
        return self.users
    def get_by_id(self, user_id: str) -> Optional[User]:
        """ Намира потребител по неговото ID. """
        for u in self.users:
            if u.user_id == user_id:
                return u
        return None


    # AUTH
    def login(self, username: str, password: str) -> Optional[User]:
        """ Логин логика:
        - валидира входа чрез UserValidator
        - хешира паролата
        - сравнява с хешираната в модела """
        user = UserValidator.validate_login(username, password, self)
        hashed = self._hash_password(password)
        if user.password == hashed:
            self.logged_user = user
            return user

        return None

    # ADMIN ACTIONS
    def register(self, first_name, last_name, email, username, password, role="Operator"):
        """Регистрира нов потребител. Контролерът НЕ валидира сам – използва UserValidator."""
        UserValidator.validate_user_data(username, password, email, role, "Active")
        UserValidator.validate_unique_username(username, self)
        new_user = User(user_id=str(uuid.uuid4()), first_name=first_name.strip(),
                        last_name=last_name.strip(), email=email.strip(), username=username.strip(),
                        password=self._hash_password(password), role=role, status="Active",
                        created=self._get_now(), modified=self._get_now())

        self.users.append(new_user)
        self.save_changes()
        return new_user

    def change_role(self, username, new_role):
        """ Променя роля на потребител.Валидацията е изцяло във UserValidator."""

        user = UserValidator.validate_exists(username, self)
        UserValidator.validate_role(new_role)
        if user.role == new_role:
            raise ValueError(f"Потребителят вече има роля '{new_role}'.")

        user.role = new_role
        user.modified = self._get_now()
        self.save_changes()

    def change_status(self, acting_user: User, target_username: str, new_status: str):
        """ Променя статус на потребител. Само админ може да го прави."""

        UserValidator.confirm_admin(acting_user)
        UserValidator.validate_status(new_status)
        user = UserValidator.validate_exists(target_username, self)
        if user.status == new_status:
            raise ValueError(f"Потребителят вече е в статус '{new_status}'.")

        user.status = new_status
        user.modified = self._get_now()
        self.save_changes()
        return True

    def delete_user(self, acting_user: User, target_username: str):
        """ Изтрива потребител.
        - админ проверка
        - забрана за самоизтриване
        - забрана за изтриване на последния админ"""
        UserValidator.confirm_admin(acting_user)
        UserValidator.validate_not_self(acting_user.username, target_username)
        user = UserValidator.validate_exists(target_username, self)
        UserValidator.validate_not_last_admin(user, self.users)

        self.users.remove(user)
        self.save_changes()
        return True

    # BOOTSTRAP LOGIC
    def _bootstrap_system(self):
        """ Създава системни акаунти при първо стартиране. """
        self._create_default_admin()
        self._create_default_operator()

    def _create_default_admin(self):
        """ Създава дефолтен администратор. """
        self.register("Admin", "System", "admin@stock.com",
                      "admin", "admin123", role="Admin")

    def _create_default_operator(self):
        """ Създава дефолтен оператор. """
        self.register("Ivan", "Petrov", "ivan@example.com", "ivan",
                      "test123", role="Operator")

    # ANONYMOUS USER FACTORY - Създава анонимен потребител (гост).
    def create_anonymous_user(self) -> User:
        now = self._get_now()
        return User(user_id="guest-0000", first_name="Anonymous", last_name="", email="",
                    username="guest", password="", role="Anonymous", status="Active",
                    created=now, modified=now)
