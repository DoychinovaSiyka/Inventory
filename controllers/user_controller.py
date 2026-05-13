import re
from typing import Optional, List
from models.user import User
from validators.user_validator import UserValidator


class UserController:
    def __init__(self, repo, activity_log_controller=None):
        self.repo = repo


        raw_data = self.repo.load()
        if not raw_data or not isinstance(raw_data, list):
            raw_data = []


        self.users: List[User] = [User.from_dict(u) for u in raw_data if isinstance(u, dict)]
        self.logged_user: Optional[User] = None


        if not self.get_by_username("admin"):
            self._create_default_admin()
        if not self.get_by_username("operator"):
            self._create_default_operator()

    def find_user_flexible(self, identifier: str) -> Optional[User]:
        # търсене по ID или username
        if not identifier:
            return None

        identifier = str(identifier).strip()
        user = self.get_by_id(identifier)
        if user:
            return user

        return self.get_by_username(identifier)

    def _hash_password(self, password: str) -> str:
        if not password:
            return ""
        return "".join(str(ord(c)) for c in password)

    def _check_password(self, stored_password_hash: str, provided_password: str) -> bool:
        return stored_password_hash == self._hash_password(provided_password)

    def is_admin(self, user):
        if not user:
            return False
        return str(user.role).lower() == "admin"

    def save_changes(self):
        # Записваме всички потребители обратно в JSON
        self.repo.save([u.to_dict() for u in self.users])

    def get_by_username(self, username: str) -> Optional[User]:
        if not username:
            return None

        username = username.strip().lower()
        for u in self.users:
            if u.username.lower() == username:
                return u
        return None

    def get_all(self):
        return self.users

    def get_by_id(self, user_id: str) -> Optional[User]:
        uid = str(user_id or "").strip()
        if not uid:
            return None

        for u in self.users:
            full_id = str(u.user_id)
            short_id = full_id[:8]

            if uid == short_id or uid == full_id:
                return u

        return None

    def login(self, username: str, password: str) -> Optional[User]:
        user = UserValidator.validate_login(username, password, self)
        if user:
            self.logged_user = user
            return user
        return None

    def register(self, first_name, last_name, email, username, password, role="Operator"):
        UserValidator.validate_user_data(username, password, email, role, "Active")
        UserValidator.validate_unique_username(username, self)

        new_user = User(user_id=None, first_name=first_name.strip(),last_name=last_name.strip(), email=email.strip(),
                        username=username.strip().lower(), password=self._hash_password(password),
                        role=role, status="Active")

        self.users.append(new_user)
        self.save_changes()
        return new_user

    def change_role(self, identifier, new_role):
        user = self.find_user_flexible(identifier)
        if not user:
            raise ValueError(f"Потребител '{identifier}' не е намерен.")

        UserValidator.validate_role(new_role)

        if user.role == new_role:
            raise ValueError(f"Потребителят вече е с роля '{new_role}'.")

        user.role = new_role
        user.update_modified()
        self.save_changes()

    # Активиране/деактивиране на потребител
    def change_status(self, acting_user: User, identifier: str, new_status: str):
        user = self.find_user_flexible(identifier)
        if not user:
            raise ValueError(f"Потребител '{identifier}' не е намерен.")

        UserValidator.confirm_admin(acting_user)
        UserValidator.validate_status(new_status)
        UserValidator.validate_not_self(acting_user.username, user.username)

        user.status = new_status
        user.update_modified()
        self.save_changes()
        return True

    def delete_user(self, acting_user: User, identifier: str):
        user = self.find_user_flexible(identifier)
        if not user:
            raise ValueError(f"Потребител '{identifier}' не е намерен.")

        UserValidator.confirm_admin(acting_user)
        UserValidator.validate_not_self(acting_user.username, user.username)
        UserValidator.validate_not_last_admin(user, self.users)

        self.users.remove(user)
        self.save_changes()
        return True


    # Създаваме администратор по подразбиране
    def _create_default_admin(self):
        admin = User(user_id=None, first_name="Admin", last_name="System", email="admin@system.local",
                     username="admin", password=self._hash_password("admin123"), role="Admin", status="Active")
        self.users.append(admin)
        self.save_changes()


    def _create_default_operator(self):
        operator = User(user_id=None, first_name="Operator", last_name="User",
                        email="operator@example.com", username="operator", password=self._hash_password("operator123"),
                        role="Operator", status="Active")
        self.users.append(operator)
        self.save_changes()


    def validate_field(self, field_type: str, value: str) -> Optional[str]:
        try:
            if field_type == "username":
                if not value or len(value.strip()) < 3:
                    raise ValueError("Потребителското име трябва да е поне 3 символа.")
                if not value.isalnum():
                    raise ValueError("Потребителското име може да съдържа само букви и цифри.")
                UserValidator.validate_unique_username(value, self)

            elif field_type == "email":
                email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
                if not re.match(email_regex, value):
                    raise ValueError(f"Невалиден формат на имейл: {value}")

            elif field_type == "password":
                if len(value) < 6:
                    raise ValueError("Паролата трябва да бъде поне 6 символа.")
                if value.isdigit() or value.isalpha():
                    raise ValueError("Паролата трябва да съдържа комбинация от букви и цифри.")

            elif field_type == "role":
                UserValidator.validate_role(value)
            return None

        except ValueError as e:
            return str(e)
