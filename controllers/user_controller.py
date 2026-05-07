from typing import Optional, List
from models.user import User
from validators.user_validator import UserValidator


class UserController:
    def __init__(self, repo, activity_log_controller=None):
        self.repo = repo
        self.activity_log = activity_log_controller

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
        """Търси потребител по пълно ID, кратко ID или Username."""
        if not identifier: return None
        target = str(identifier).strip()


        user = self.get_by_id(target)
        if user:
            return user

        return self.get_by_username(target)

    def _hash_password(self, password: str) -> str:
        if not password: return ""
        return "".join(str(ord(c)) for c in password)

    def _check_password(self, stored_password_hash: str, provided_password: str) -> bool:
        return stored_password_hash == self._hash_password(provided_password)

    def save_changes(self):
        self.repo.save([u.to_dict() for u in self.users])

    def get_by_username(self, username: str) -> Optional[User]:
        if not username: return None
        search_name = username.strip().lower()
        for u in self.users:
            if u.username.lower() == search_name:
                return u
        return None

    def get_all(self):
        return self.users

    def get_by_id(self, user_id: str) -> Optional[User]:
        target_id = str(user_id).strip()
        if not target_id: return None
        for u in self.users:
            if u.user_id == target_id or u.user_id.startswith(target_id):
                return u
        return None

    def login(self, username: str, password: str) -> Optional[User]:
        user = UserValidator.validate_login(username, password, self)
        if user:
            self.logged_user = user
            if self.activity_log:
                self.activity_log.log_action(user.user_id, "LOGIN", f"Успешен вход: {user.username}")
            return user
        return None

    def register(self, first_name, last_name, email, username, password, role="Operator"):
        UserValidator.validate_user_data(username, password, email, role, "Active")
        UserValidator.validate_unique_username(username, self)

        new_user = User(user_id=None, first_name=first_name.strip(), last_name=last_name.strip(),
                        email=email.strip(), username=username.strip().lower(),
                        password=self._hash_password(password), role=role, status="Active")
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

        if self.activity_log:
            self.activity_log.log_action(acting_user.user_id, "DELETE_USER", f"Изтрит потребител: {user.username}")
        return True

    def _create_default_admin(self):
        admin = User(user_id=None, first_name="Admin", last_name="System", email="admin@system.local",
                     username="admin", password=self._hash_password("admin123"), role="Admin", status="Active")
        self.users.append(admin)
        self.save_changes()

    def _create_default_operator(self):
        operator = User(user_id=None, first_name="Operator", last_name="User", email="operator@example.com",
                        username="operator", password=self._hash_password("operator123"), role="Operator",
                        status="Active")
        self.users.append(operator)
        self.save_changes()