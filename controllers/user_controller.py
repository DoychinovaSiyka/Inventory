from typing import Optional
from models.user import User
from storage.json_repository import JSONRepository


class UserController:
    def __init__(self, user_repo: JSONRepository):
        self.user_repo = user_repo

        # Зареждаме потребителите от JSON
        self.users = [User.from_dict(u) for u in self.user_repo.load()]

        # Ако няма НИТО един потребител → създаваме първия администратор
        if not self.users:
            default_admin = User(
                first_name="Admin",
                last_name="User",
                email="admin@example.com",
                username="admin",
                password="admin",
                role="admin",
                status="active"
            )
            self.users.append(default_admin)
            self._save()

        # Текущо логнат потребител
        self.logged_user: Optional[User] = None

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Проверява дали има потребител с това име и парола.
        Ако има → задава logged_user и връща User.
        Ако няма → връща None.
        """
        for user in self.users:
            if (
                user.username == username
                and user.password == password
                and user.status == "active"
            ):
                self.logged_user = user
                return user
        return None

    def add_user(self, user: User):
        """Добавя нов потребител и записва в JSON."""
        self.users.append(user)
        self._save()

    def get_all(self):
        """Връща всички потребители."""
        return self.users

    def _save(self):
        """Записва всички потребители обратно в JSON."""
        self.user_repo.save([u.to_dict() for u in self.users])
