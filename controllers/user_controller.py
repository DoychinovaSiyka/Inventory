from typing import Optional
from models.user import User
from storage.json_repository import JSONRepository


class UserController:
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        self.users = [User.from_dict(u) for u in self.repo.load()]

        # Ако няма потребители → създаваме администратор
        if not self.users:
            admin = User(
                first_name="Admin",
                last_name="User",
                email="admin@example.com",
                username="admin",
                password=self._hash_password("admin"),
                role="admin",
                status="active"
            )
            self.users.append(admin)
            self._save()

        self.logged_user: Optional[User] = None

    # ---------------------------------------------------
    #   ПРОСТ "ХЕШ" БЕЗ НИКАКВИ ИМПОРТИ
    # ---------------------------------------------------
    def _hash_password(self, password: str) -> str:
        # Превръща всеки символ в ASCII код и ги слепва
        return "".join(str(ord(c) * 7) for c in password)

    # ---------------------------------------------------
    #   ПОМОЩНИ МЕТОДИ
    # ---------------------------------------------------
    def _save(self):
        self.repo.save([u.to_dict() for u in self.users])

    def _is_unique_username(self, username: str) -> bool:
        return not any(u.username == username for u in self.users)

    def get_by_id(self, user_id: int) -> Optional[User]:
        for u in self.users:
            if u.id == user_id:
                return u
        return None

    # ---------------------------------------------------
    #   РЕГИСТРАЦИЯ
    # ---------------------------------------------------
    def register(self, first_name, last_name, email, username, password, role="operator"):
        if not self._is_unique_username(username):
            raise ValueError("Потребителското име вече съществува.")

        hashed = self._hash_password(password)

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            password=hashed,
            role=role,
            status="active"
        )

        self.users.append(new_user)
        self._save()
        return new_user

    # ---------------------------------------------------
    #   ЛОГИН
    # ---------------------------------------------------
    def login(self, username: str, password: str) -> Optional[User]:
        hashed = self._hash_password(password)

        for user in self.users:
            if user.username == username and user.password == hashed and user.status == "active":
                self.logged_user = user
                return user

        return None

    # ---------------------------------------------------
    #   ПРОМЯНА НА РОЛЯ
    # ---------------------------------------------------
    def change_role(self, username: str, new_role: str):
        for user in self.users:
            if user.username == username:
                user.role = new_role
                self._save()
                return True
        return False

    # ---------------------------------------------------
    #   ДЕАКТИВИРАНЕ
    # ---------------------------------------------------
    def deactivate_user(self, username: str):
        for user in self.users:
            if user.username == username:
                user.status = "inactive"
                self._save()
                return True
        return False

    # ---------------------------------------------------
    #   СПИСЪК
    # ---------------------------------------------------
    def get_all(self):
        return self.users
