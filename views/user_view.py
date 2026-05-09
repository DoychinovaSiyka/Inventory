from views.menu import Menu, MenuItem
from views.password_utils import input_password, format_table


class UserView:
    def __init__(self, controller):
        self.controller = controller

    def show_menu(self, user):
        if not user or not hasattr(user, 'role') or user.role != "Admin":
            print("\nСамо администратор може да управлява потребители.")
            return

        while True:
            menu = self._build_menu()
            choice = menu.show()
            if menu.execute(choice, user) == "break":
                break

    def _build_menu(self):
        return Menu("Администрация на потребители", [
            MenuItem("1", "Списък на всички потребители", self.show_users),
            MenuItem("2", "Добавяне на нов потребител", self.add_user),
            MenuItem("3", "Промяна на роля", self.change_role),
            MenuItem("4", "Деактивиране", self.deactivate_user),
            MenuItem("5", "Активиране", self.activate_user),
            MenuItem("6", "Изтриване от системата", self.delete_user),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    def show_users(self, _):
        users = self.controller.get_all()
        if not users:
            print("\nНяма регистрирани потребители.")
            return

        print("\nСписък на потребителите")
        columns = ["ID", "Username", "Имейл", "Роля", "Статус"]
        rows = []
        for u in users:
            rows.append([u.user_id[:8], u.username, u.email, u.role, u.status])

        print(format_table(columns, rows))
        input("\nEnter за връщане...")

    def add_user(self, _):
        print("\nНов потребител")
        print("(Напишете 'отказ' за изход)")

        while True:
            username = input("Потребителско име (мин. 3 символа): ").strip()
            if username.lower() == 'отказ':
                return
            if len(username) < 3:
                print("Името е твърде кратко.")
                continue
            if self.controller.get_by_username(username):
                print("Това име вече е заето.")
                continue
            break

        while True:
            email = input("Имейл: ").strip()
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

        while True:
            role_raw = input("Роля (Admin/Operator) [Operator]: ").strip().capitalize()
            if role_raw == 'Отказ':
                return
            if not role_raw:
                role = "Operator"
                break
            if role_raw in ["Admin", "Operator"]:
                role = role_raw
                break
            print("Невалидна роля.")

        fn = input("Име (Enter за празно): ").strip() or "-"
        ln = input("Фамилия (Enter за празно): ").strip() or "-"

        try:
            self.controller.register(fn, ln, email, username, password, role)
            print(f"\nПотребител '{username}' е добавен.")
        except Exception as e:
            print(f"Проблем при запис: {e}")

    def change_role(self, _):
        print("\nПромяна на роля")

        while True:
            target = input("Username или ID (или 'отказ'): ").strip()
            if not target or target.lower() == 'отказ':
                return

            user_obj = self.controller.get_by_id(target) or self.controller.get_by_username(target)
            if user_obj:
                break
            print("Няма такъв потребител.")

        while True:
            new_role = input(f"Нова роля за {user_obj.username} (Admin/Operator): ").strip().capitalize()
            if new_role.lower() == 'отказ':
                return
            if new_role in ["Admin", "Operator"]:
                break
            print("Невалидна роля.")

        try:
            self.controller.change_role(user_obj.user_id, new_role)
            print(f"Ролята на {user_obj.username} е променена на {new_role}.")
        except Exception as e:
            print(f"Проблем при промяна: {e}")

    def deactivate_user(self, current_user):
        print("\nДеактивиране на потребител")

        target = input("Username или ID (или 'отказ'): ").strip()
        if not target or target.lower() == 'отказ':
            return

        try:
            self.controller.change_status(current_user, target, "Inactive")
            print("Потребителят е деактивиран.")
        except Exception as e:
            print(f"Проблем при деактивиране: {e}")

    def activate_user(self, current_user):
        print("\nАктивиране на потребител")

        target = input("Username или ID (или 'отказ'): ").strip()
        if not target or target.lower() == 'отказ':
            return

        try:
            self.controller.change_status(current_user, target, "Active")
            print("Потребителят е активиран.")
        except Exception as e:
            print(f"Проблем при активиране: {e}")

    def delete_user(self, current_user):
        print("\nИзтриване на потребител")

        target = input("Username или ID (или 'отказ'): ").strip()
        if not target or target.lower() == 'отказ':
            return

        confirm = input(f"Искате ли да изтрием '{target}'? (y/n): ").strip().lower()
        if confirm == 'y':
            try:
                self.controller.delete_user(current_user, target)
                print("Потребителят е изтрит.")
            except Exception as e:
                print(f"Проблем при изтриване: {e}")
        else:
            print("Операцията е прекратена.")
