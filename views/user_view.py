from models.user import User
from controllers.user_controller import UserController
from views.menu import Menu, MenuItem
from views.password_utils import input_password  # скрито въвеждане на парола


class UserView:
    def __init__(self, controller: UserController):
        self.controller = controller

    # Основно меню
    def show_menu(self, user: User):
        if user.role != "Admin":
            print("\n[Достъп отказан] Само администратор може да управлява потребители.")
            return

        menu = self._build_menu()
        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # Създаване на менюто отделно
    def _build_menu(self):
        return Menu("МЕНЮ ПОТРЕБИТЕЛИ", [
            MenuItem("1", "Списък на потребители", self.show_users),
            MenuItem("2", "Добавяне на потребител", self.add_user),
            MenuItem("3", "Промяна на роля", self.change_role),
            MenuItem("4", "Деактивиране на потребител", self.deactivate_user),
            MenuItem("5", "Активиране на потребител", self.activate_user),
            MenuItem("6", "Премахване на потребител", self.delete_user),
            MenuItem("0", "Назад", lambda u: "break")])

    # Показване на всички потребители
    def show_users(self, _):
        users = self.controller.get_all()
        for u in users:
            print(f"{u.username} | {u.role} | {u.status}")

    # Добавяне на потребител
    def add_user(self, _):
        print("\n--- РЕГИСТРАЦИЯ НА НОВ ПОТРЕБИТЕЛ ---")
        fn = input("Име (Enter за отказ): ").strip()
        if not fn:
            print("Операцията е отказана.\n")
            return

        ln = input("Фамилия (Enter за отказ): ").strip()
        if not ln:
            print("Операцията е отказана.")
            return

        email = input("Email (Enter за отказ): ").strip()
        if not email:
            print("Операцията е отказана.\n")
            return

        username = input("Потребителско име (Enter за отказ): ").strip()
        if not username:
            print("Операцията е отказана.\n")
            return

        password = input_password("Парола (Enter за отказ): ").strip()
        if not password:
            print("Операцията е отказана.\n")
            return

        role = input("Роля (Admin/Operator, Enter за отказ): ").strip()
        if not role:
            print("Операцията е отказана.\n")
            return

        try:
            self.controller.register(fn, ln, email, username, password, role)
            print("[Успех] Потребителят е добавен успешно!")
        except ValueError as e:
            print(f"[Грешка] {e}")

    # Промяна на роля
    def change_role(self, user):
        print("\n--- ПРОМЯНА НА ПОТРЕБИТЕЛСКА РОЛЯ ---")
        username = input("Потребителско име (Enter за отказ): ").strip()
        if not username:
            print("Операцията е отказана.\n")
            return

        new_role = input("Нова роля (Admin/Operator, Enter за отказ): ").strip()
        if not new_role:
            print("Операцията е отказана.\n")
            return

        try:
            self.controller.change_role(username, new_role)
            print(f"[Успех] Ролята на '{username}' е променена на {new_role}.")
        except ValueError as e:
            print(f"[Грешка] {e}")

    # Деактивиране на потребител
    def deactivate_user(self, user):
        print("\n--- ДЕАКТИВИРАНЕ НА ПОТРЕБИТЕЛ ---")
        username = input("Потребителско име (Enter за отказ): ").strip()
        if not username:
            print("Операцията е отказана.\n")
            return

        try:
            self.controller.change_status(user, username, "Inactive")
            print(f"[Успех] Потребителят '{username}' е деактивиран.")
        except ValueError as e:
            print(f"[Грешка] {e}")

    def activate_user(self, user):
        print("\n--- АКТИВИРАНЕ НА ПОТРЕБИТЕЛ ---")
        username = input("Потребителско име (Enter за отказ): ").strip()
        if not username:
            print("Операцията е отказана.\n")
            return

        try:
            self.controller.change_status(user, username, "Active")
            print(f"[Успех] Потребителят '{username}' е активиран.")
        except ValueError as e:
            print(f"[Грешка] {e}")

    # Изтриване на потребител
    def delete_user(self, user):
        print("\n--- ПРЕМАХВАНЕ НА ПОТРЕБИТЕЛ ---")
        username = input("Потребителско име за изтриване (Enter за отказ): ").strip()
        if not username:
            print("Операцията е отказана.\n")
            return

        confirm = input(f"Наистина ли искате окончателно да изтриете '{username}'? (y/n): ").strip().lower()
        if confirm != "y":
            print("Операцията е отказана.")
            return

        try:
            self.controller.delete_user(user, username)
            print(f"[Успех] Потребителят '{username}' е изтрит от системата.")
        except ValueError as e:
            print(f"[Грешка] {e}")