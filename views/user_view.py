from models.user import User
from controllers.user_controller import UserController
from views.menu import Menu, MenuItem
from views.password_utils import input_password, format_table


class UserView:
    def __init__(self, controller: UserController):
        self.controller = controller

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

    def _build_menu(self):
        return Menu("АДМИНИСТРАЦИЯ НА ПОТРЕБИТЕЛИ", [
            MenuItem("1", "Списък на всички потребители", self.show_users),
            MenuItem("2", "Добавяне на нов потребител", self.add_user),
            MenuItem("3", "Промяна на роля (Admin/Operator)", self.change_role),
            MenuItem("4", "Деактивиране (Inactive)", self.deactivate_user),
            MenuItem("5", "Активиране (Active)", self.activate_user),
            MenuItem("6", "Изтриване от системата", self.delete_user),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    def show_users(self, _):
        users = self.controller.get_all()
        if not users:
            print("\nНяма регистрирани потребители.")
            return

        print("\n--- СПИСЪК НА ПОТРЕБИТЕЛИТЕ ---")
        columns = ["ID (кратко)", "Username", "Имейл", "Роля", "Статус"]
        rows = [[u.user_id[:8], u.username, u.email, u.role, u.status] for u in users]
        print(format_table(columns, rows))

    def add_user(self, _):
        print("\n--- РЕГИСТРАЦИЯ НА НОВ ПОТРЕБИТЕЛ ---")
        username = input("Потребителско име (мин. 3 симв.): ").strip()
        if not username:
            return

        email = input("Имейл адрес: ").strip()
        if not email:
            return

        password = input_password("Парола (мин. 6 симв., букви и цифри): ").strip()
        if not password:
            return

        role = input("Роля (Admin/Operator) [Default: Operator]: ").strip() or "Operator"
        fn = input("Име (опционално): ").strip() or "-"
        ln = input("Фамилия (опционално): ").strip() or "-"

        try:
            new_user = self.controller.register(fn, ln, email, username, password, role)
            print(f"Потребител '{username}' е добавен с ID: {new_user.user_id[:8]}")
        except ValueError as e:
            print(f"[Грешка] {e}")

    def change_role(self, _):
        print("\n--- ПРОМЯНА НА РОЛЯ ---")
        target = input("Username или кратко ID на потребителя: ").strip()
        if not target:
            return

        new_role = input("Нова роля (Admin/Operator): ").strip()
        if not new_role:
            return

        try:
            self.controller.change_role(target, new_role)
            print(f"Ролята на '{target}' е променена.")
        except ValueError as e:
            print(f"[Грешка] {e}")

    def deactivate_user(self, current_user):
        print("\n--- ДЕАКТИВИРАНЕ ---")
        target = input("Username или кратко ID за деактивиране: ").strip()
        if not target:
            return

        try:
            self.controller.change_status(current_user, target, "Inactive")
            print(f"Потребителят '{target}' вече е неактивен.")
        except ValueError as e:
            print(f"[Грешка] {e}")

    def activate_user(self, current_user):
        print("\n--- АКТИВИРАНЕ ---")
        target = input("Username или кратко ID за активиране: ").strip()
        if not target:
            return

        try:
            self.controller.change_status(current_user, target, "Active")
            print(f"Потребителят '{target}' е активиран успешно.")
        except ValueError as e:
            print(f"[Грешка] {e}")


    def delete_user(self, current_user):
        print("\n--- ПРЕМАХВАНЕ НА ПОТРЕБИТЕЛ ---")
        target = input("Username или кратко ID за изтриване: ").strip()
        if not target:
            return

        confirm = input(f"ВНИМАНИЕ: Изтриването на '{target}' е окончателно! Потвърди (y/n): ").strip().lower()
        if confirm == 'y':
            try:
                self.controller.delete_user(current_user, target)
                print(f"Потребителят '{target}' е премахнат от системата.")
            except (ValueError, PermissionError) as e:
                print(f"[Грешка] {e}")
        else:
            print("Операцията е отказана.")
