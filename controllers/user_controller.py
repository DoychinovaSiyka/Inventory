from typing import Optional, List
from datetime import datetime
import uuid
from models.user import User
from validators.user_validator import UserValidator


class UserController:
    def __init__(self, repo):
        self.repo = repo
        self.users: List[User] = [User.from_dict(u) for u in self.repo.load()]
        self.logged_user: Optional[User] = None

        # Ако няма потребители, създаваме начални (може да се изнесе и в setup скрипт)
        if not self.users:
            self._bootstrap_system()

    def _get_now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _hash_password(self, password: str) -> str:
        # В реална среда тук би имало bcrypt/hashlib
        return "".join(str(ord(c)) for c in password)

    def save_changes(self):
        self.repo.save([u.to_dict() for u in self.users])

    # --- READ ---
    def get_by_username(self, username: str) -> Optional[User]:
        return next((u for u in self.users if u.username == username), None)

    def get_all(self):
        return self.users

    # --- AUTH ---
    def login(self, username: str, password: str) -> Optional[User]:
        hashed = self._hash_password(password)
        user = self.get_by_username(username)

        if user and user.password == hashed and user.status == "Active":
            self.logged_user = user
            return user
        return None

    # --- ADMIN ACTIONS ---
    def register(self, first_name, last_name, email, username, password, role="Operator"):
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

    def change_role(self, username, new_role):
        user = self.get_by_username(username)
        if not user:
            raise ValueError("Няма такъв потребител.")

        if new_role not in ["Admin", "Operator"]:
            raise ValueError("Невалидна роля.")

        user.role = new_role
        user.modified = self._get_now()
        self.save_changes()

    def change_status(self, acting_user: User, target_username: str, new_status: str):
        UserValidator.confirm_admin(acting_user)

        user = self.get_by_username(target_username)
        if not user:
            raise ValueError("Потребителят не е намерен.")

        user.status = new_status
        user.modified = self._get_now()
        self.save_changes()
        return True

    def delete_user(self, acting_user: User, target_username: str):
        UserValidator.confirm_admin(acting_user)
        UserValidator.validate_not_self(acting_user.username, target_username)

        user = self.get_by_username(target_username)
        if not user:
            raise ValueError("Потребителят не е намерен.")

        self.users.remove(user)
        self.save_changes()
        return True

    def _bootstrap_system(self):
        """ Създава начален администратор, ако базата е празна. """
        self.register("Admin", "System", "admin@stock.com", "admin", "admin123", role="Admin")
