from typing import Optional
from datetime import datetime
from models.user import User
from storage.json_repository import JSONRepository
from validators.user_validator import UserValidator
import getpass
import msvcrt   #  звездички при въвеждане на парола


#  Функция за въвеждане на парола със звездички (работи в CMD/PowerShell)
def input_password(prompt="Парола: "):
    print(prompt, end="", flush=True)
    password = ""

    while True:
        ch = msvcrt.getch()

        # Enter
        if ch in {b"\r", b"\n"}:
            print()
            break

        # Backspace
        if ch == b"\x08":
            if password:
                password = password[:-1]
                print("\b \b", end="", flush=True)
            continue

        # Специални клавиши (стрелки, F1 и др.)
        if ch in {b"\x00", b"\xe0"}:
            msvcrt.getch()
            continue

        # Нормален символ
        password += ch.decode("utf-8")
        print("*", end="", flush=True)

    return password


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

            # Автоматично създаване на оператор (първоначално)
            operator = User(
                first_name="Operator",
                last_name="User",
                email="operator@example.com",
                username="operator",
                password=self._hash_password("operator123"),
                role="Operator",
                status="Active",
                created=now,
                modified=now
            )
            self.users.append(operator)

            self.save_changes()

        # Ако няма оператор → създаваме един
        if not any(u.role == "Operator" for u in self.users):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            operator = User(
                first_name="Operator",
                last_name="User",
                email="operator@example.com",
                username="operator",
                password=self._hash_password("operator123"),
                role="Operator",
                status="Active",
                created=now,
                modified=now
            )
            self.users.append(operator)
            self.save_changes()

        self.logged_user: Optional[User] = None

    # PASSWORD HASHING
    @staticmethod
    def _hash_password(password: str) -> str:
        return "".join(str(ord(c)) for c in password)

    # SAVE
    def save_changes(self):
        self.repo.save([u.to_dict() for u in self.users])

    # HELPERS
    def _is_unique_username(self, username: str) -> bool:
        return not any(u.username == username for u in self.users)

    def get_by_id(self, user_id: int) -> Optional[User]:
        return next((u for u in self.users if u.user_id == user_id), None)

    # REGISTER
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
        self.save_changes()
        return new_user

    #  LOGIN — скрито въвеждане на парола (със звездички)
    def login(self, username: str, password: Optional[str] = None) -> Optional[User]:

        # Ако паролата не е подадена от main.py → искаме я тук
        if password is None:
            try:
                password = input_password("Парола: ")
            except Exception:
                #  НИКОГА не показваме видима парола
                password = getpass.getpass("Парола: ")

        hashed = self._hash_password(password)

        for user in self.users:
            if user.username == username and user.password == hashed:
                if user.status != "Active":
                    return None
                self.logged_user = user
                return user

        return None

    # CHANGE ROLE (Admin only)
    def change_role(self, acting_user: User, username: str, new_role: str):
        if acting_user.role != "Admin":
            raise PermissionError("Само администратор може да променя роли.")

        UserValidator.validate_role(new_role)

        for user in self.users:
            if user.username == username:
                user.role = new_role
                user.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.save_changes()
                return True

        return False

    # DEACTIVATE USER (Admin only)
    def deactivate_user(self, acting_user: User, username: str):
        if acting_user.role != "Admin":
            raise PermissionError("Само администратор може да деактивира потребители.")

        for user in self.users:
            if user.username == username:
                user.status = "Disabled"
                user.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.save_changes()
                return True

        return False

    # ACTIVATE USER (Admin only)
    def activate_user(self, acting_user: User, username: str):
        if acting_user.role != "Admin":
            raise PermissionError("Само администратор може да активира потребители.")

        for user in self.users:
            if user.username == username:
                user.status = "Active"
                user.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.save_changes()
                return True

        return False

    # DELETE USER (Admin only)
    def delete_user(self, acting_user: User, username: str):
        if acting_user.role != "Admin":
            raise PermissionError("Само администратор може да изтрива потребители.")

        if acting_user.username == username:
            raise ValueError("Администраторът не може да изтрие собствения си акаунт.")

        for user in self.users:
            if user.username == username:
                self.users.remove(user)
                self.save_changes()
                return True

        return False

    # LIST USERS
    def get_all(self):
        return self.users
