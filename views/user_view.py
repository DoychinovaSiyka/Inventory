from models.user import User
from controllers.user_controller import UserController
from views.menu import Menu, MenuItem
from views.password_utils import input_password, format_table


class UserView:
    def __init__(self, controller: UserController):
        self.controller = controller

    def show_menu(self, user: User):
        if user.role != "Admin":
            print("\nСамо администратор може да управлява потребители.")
            return

        while True:
            menu = self._build_menu()
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    def _build_menu(self):
        return Menu("Администрация на потребители", [
            MenuItem("1", "Списък на всички потребители", lambda u: self.show_users(u)),
            MenuItem("2", "Добавяне на нов потребител", lambda u: self.add_user(u)),
            MenuItem("3", "Промяна на роля", lambda u: self.change_role(u)),
            MenuItem("4", "Деактивиране", lambda u: self.deactivate_user(u)),
            MenuItem("5", "Активиране", lambda u: self.activate_user(u)),
            MenuItem("6", "Изтриване от системата", lambda u: self.delete_user(u)),
            MenuItem("0", "Назад", lambda u: "break")])

    def show_users(self, _):
        users = self.controller.get_all()
        if not users:
            print("\nНяма регистрирани потребители.")
            return

        print("\nСписък на потребителите")
        columns = ["ID (кратко)", "Username", "Имейл", "Роля", "Статус"]
        rows = []
        for u in users:
            rows.append([u.user_id[:8], u.username, u.email, u.role, u.status])

        print(format_table(columns, rows))
        input("\nНатиснете Enter за връщане...")

    def add_user(self, _):
        print("\nДобавяне на нов потребител")
        print("(Напишете 'отказ' за изход)")

        while True:
            username = input("Потребителско име (мин. 3 символа): ").strip()
            if username.lower() == 'отказ':
                return

            if self.controller.get_by_username(username):
                print("Това потребителско име вече съществува.")
                continue
            if len(username) < 3:
                print("Потребителското име е твърде кратко.")
                continue
            break

        while True:
            email = input("Имейл адрес: ").strip()
            if email.lower() == 'отказ':
                return
            if "@" not in email or "." not in email:
                print("Невалиден имейл.")
                continue
            break

        while True:
            password = input_password("Парола (мин. 6 символа): ").strip()
            if password.lower() == 'отказ':
                return
            if len(password) < 6:
                print("Паролата е твърде кратка.")
                continue
            break

        role = input("Роля (Admin/Operator) [по подразбиране: Operator]: ").strip().capitalize() or "Operator"
        if role not in ["Admin", "Operator"]:
            print("Невалидна роля. Зададена е по подразбиране: Operator.")
            role = "Operator"

        fn = input("Име (опционално): ").strip() or "-"
        ln = input("Фамилия (опционално): ").strip() or "-"

        try:
            self.controller.register(fn, ln, email, username, password, role)
            print(f"\nПотребител '{username}' е добавен.")
        except ValueError as e:
            print(f"Грешка: {e}")

    def change_role(self, _):
        print("\nПромяна на роля")
        target = input("Username или ID (или 'отказ'): ").strip()
        if not target or target.lower() == 'отказ':
            return

        new_role = input("Нова роля (Admin/Operator): ").strip().capitalize()
        try:
            self.controller.change_role(target, new_role)
            print("Ролята е променена.")
        except ValueError as e:
            print(f"Грешка: {e}")

    def deactivate_user(self, current_user):
        print("\nДеактивиране на потребител")
        target = input("Username или ID (или 'отказ'): ").strip()
        if not target or target.lower() == 'отказ':
            return

        try:
            self.controller.change_status(current_user, target, "Inactive")
            print("Потребителят е деактивиран.")
        except ValueError as e:
            print(f"Грешка: {e}")

    def activate_user(self, current_user):
        print("\nАктивиране на потребител")
        target = input("Username или ID (или 'отказ'): ").strip()
        if not target or target.lower() == 'отказ':
            return

        try:
            self.controller.change_status(current_user, target, "Active")
            print("Потребителят е активиран.")
        except ValueError as e:
            print(f"Грешка: {e}")

    def delete_user(self, current_user):
        print("\nИзтриване на потребител")
        target = input("Username или ID (или 'отказ'): ").strip()
        if not target or target.lower() == 'отказ':
            return

        confirm = input(f"Изтриване на '{target}'? (y/n): ").strip().lower()
        if confirm == 'y':
            try:
                self.controller.delete_user(current_user, target)
                print("Потребителят е изтрит.")
            except (ValueError, PermissionError) as e:
                print(f"Грешка: {e}")
        else:
            print("Операцията е прекратена.")
