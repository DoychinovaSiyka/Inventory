from typing import Optional
from datetime import datetime
from models.user import User
from storage.json_repository import JSONRepository
from validators.user_validator import UserValidator


class UserController:
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        self.users = [User.from_dict(u) for u in self.repo.load()]

        # Ако няма потребители → създаваме администратор (SRS)
        if not self.users:
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
            self.users.append(admin)
            self._save()

        self.logged_user: Optional[User] = None

    # ---------------------------------------------------------
    # PASSWORD HASHING (SRS requirement)
    # ---------------------------------------------------------
    def _hash_password(self, password: str) -> str:
        return "".join(str(ord(c) * 7) for c in password)

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------
    def _save(self):
        self.repo.save([u.to_dict() for u in self.users])

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------
    def _is_unique_username(self, username: str) -> bool:
        return not any(u.username == username for u in self.users)

    def get_by_id(self, user_id: int) -> Optional[User]:
        return next((u for u in self.users if u.user_id == user_id), None)

    # ---------------------------------------------------------
    # REGISTER (SRS: validation + timestamps)
    # ---------------------------------------------------------
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
        self._save()
        return new_user

    # ---------------------------------------------------------
    # LOGIN
    # ---------------------------------------------------------
    def login(self, username: str, password: str) -> Optional[User]:
        hashed = self._hash_password(password)

        for user in self.users:
            if user.username == username and user.password == hashed:
                if user.status != "Active":
                    return None
                self.logged_user = user
                return user

        return None

    # ---------------------------------------------------------
    # CHANGE ROLE (Admin only)
    # ---------------------------------------------------------
    def change_role(self, acting_user: User, username: str, new_role: str):
        if acting_user.role != "Admin":
            raise PermissionError("Само администратор може да променя роли.")

        UserValidator.validate_role(new_role)

        for user in self.users:
            if user.username == username:
                user.role = new_role
                user.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save()
                return True

        return False

    # ---------------------------------------------------------
    # DEACTIVATE USER (Admin only)
    # ---------------------------------------------------------
    def deactivate_user(self, acting_user: User, username: str):
        if acting_user.role != "Admin":
            raise PermissionError("Само администратор може да деактивира потребители.")

        for user in self.users:
            if user.username == username:
                user.status = "Disabled"
                user.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save()
                return True

        return False

    # ---------------------------------------------------------
    # LIST USERS
    # ---------------------------------------------------------
    def get_all(self):
        return self.users
