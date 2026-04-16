from models.user import User
from controllers.user_controller import UserController
from views.menu import Menu, MenuItem
from views.password_utils import input_password  # скрито въвеждане на парола


class UserView:
    def __init__(self, controller: UserController):
        self.controller = controller
        self.menu = None  # менюто ще се създава динамично според ролята

    # Основно меню
    def show_menu(self, user: User):
        if user.role != "Admin":
            print("Само администратор може да управлява потребители.")
            return
        self.menu = self._build_menu()
        while True:
            choice = self.menu.show()
            result = self.menu.execute(choice, user)
            if result == "break":
                break

    # Създаване на менюто отделно
    def _build_menu(self):
        return Menu("МЕНЮ ПОТРЕБИТЕЛИ",[MenuItem("1", "Списък на потребители", self.show_users),
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
        fn = input("Име: ")
        ln = input("Фамилия: ")
        email = input("Email: ")
        username = input("Потребителско име: ")
        password = input_password("Парола: ")  # скрито въвеждане
        role = input("Роля (Admin/Operator): ")
        try:
            self.controller.register(fn, ln, email, username, password, role)
            print("Потребителят е добавен!")
        except ValueError as e:
            print("Грешка:", e)

    # Промяна на роля
    def change_role(self, user):
        username = input("Потребителско име: ")
        new_role = input("Нова роля (Admin/Operator): ")
        try:
            self.controller.change_role(username, new_role)
            print("Ролята е променена.")
        except ValueError as e:
            print("Грешка:", e)


    def deactivate_user(self, user):
        username = input("Потребителско име: ")
        try:
            self.controller.change_status(user, username, "Inactive")
            print("Потребителят е деактивиран.")
        except ValueError as e:
            print("Грешка:", e)

    # Активиране на потребител
    def activate_user(self, user):
        username = input("Потребителско име: ")
        try:
            self.controller.change_status(user, username, "Active")
            print("Потребителят е активиран.")
        except ValueError as e:
            print("Грешка:", e)

    # Изтриване на потребител
    def delete_user(self, user):
        username = input("Потребителско име за изтриване: ")
        try:
            self.controller.delete_user(user, username)
            print("Потребителят е изтрит.")
        except ValueError as e:
            print("Грешка:", e)
