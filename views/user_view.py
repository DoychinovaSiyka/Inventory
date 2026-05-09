from views.menu import Menu, MenuItem
from views.password_utils import input_password, format_table


class UserView:
    def __init__(self, controller):
        # Контролерът се подава отвън, без импорт на UserController
        self.controller = controller

    def show_menu(self, user):
        # Стандартна проверка за роля
        if not user or not hasattr(user, 'role') or user.role != "Admin":
            print("\n[Грешка] Само администратор може да управлява потребители.")
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

        print("\nСПИСЪК НА ПОТРЕБИТЕЛИТЕ")
        columns = ["ID (кратко)", "Username", "Имейл", "Роля", "Статус"]
        rows = []
        for u in users:
            rows.append([u.user_id[:8], u.username, u.email, u.role, u.status])

        print(format_table(columns, rows))
        input("\nНатиснете Enter за връщане...")

    def add_user(self, _):
        print("\n--- ДОБАВЯНЕ НА ПОТРЕБИТЕЛ ---")
        print("(Напишете 'отказ' за изход)")

        # Потребителско име
        while True:
            username = input("Потребителско име (мин. 3 симв.): ").strip()
            if username.lower() == 'отказ': return
            if len(username) < 3:
                print("Грешка: Твърде кратко име.")
                continue
            if self.controller.get_by_username(username):
                print("Грешка: Това име вече е заето.")
                continue
            break

        # Имейл
        while True:
            email = input("Имейл адрес: ").strip()
            if email.lower() == 'отказ': return
            if "@" not in email or "." not in email:
                print("Грешка: Невалиден имейл формат.")
                continue
            break

        # Парола
        while True:
            password = input_password("Парола (мин. 6 симв.): ").strip()
            if password.lower() == 'отказ': return
            if len(password) < 6:
                print("Грешка: Твърде кратка парола.")
                continue
            break

        # Роля
        while True:
            role_raw = input("Роля (Admin/Operator) [Operator]: ").strip().capitalize()
            if role_raw == 'Отказ': return
            if not role_raw:
                role = "Operator"
                break
            if role_raw in ["Admin", "Operator"]:
                role = role_raw
                break
            print("Грешка: Невалидна роля. Изберете 'Admin' или 'Operator'.")

        fn = input("Име (Enter за празно): ").strip() or "-"
        ln = input("Фамилия (Enter за празно): ").strip() or "-"

        try:
            self.controller.register(fn, ln, email, username, password, role)
            print(f"\n[OK] Потребител '{username}' е добавен успешно.")
        except Exception as e:
            print(f"Грешка: {e}")

    def change_role(self, _):
        print("\n--- ПРОМЯНА НА РОЛЯ ---")
        while True:
            target = input("Username или ID (или 'отказ'): ").strip()
            if not target or target.lower() == 'отказ': return

            user_obj = self.controller.get_by_id(target) or self.controller.get_by_username(target)
            if user_obj: break
            print("Грешка: Потребителят не е намерен.")

        while True:
            new_role = input(f"Нова роля за {user_obj.username} (Admin/Operator): ").strip().capitalize()
            if new_role.lower() == 'отказ': return
            if new_role in ["Admin", "Operator"]: break
            print("Грешка: Невалидна роля.")

        try:
            self.controller.change_role(user_obj.user_id, new_role)
            print(f"[OK] Ролята на {user_obj.username} вече е {new_role}.")
        except Exception as e:
            print(f"Грешка: {e}")

    def deactivate_user(self, current_user):
        print("\n--- ДЕАКТИВИРАНЕ ---")
        target = input("Username или ID за деактивиране (или 'отказ'): ").strip()
        if not target or target.lower() == 'отказ': return

        try:
            self.controller.change_status(current_user, target, "Inactive")
            print("[OK] Потребителят е деактивиран.")
        except Exception as e:
            print(f"Грешка: {e}")

    def activate_user(self, current_user):
        print("\n--- АКТИВИРАНЕ ---")
        target = input("Username или ID за активиране (или 'отказ'): ").strip()
        if not target or target.lower() == 'отказ': return

        try:
            self.controller.change_status(current_user, target, "Active")
            print("[OK] Потребителят е активиран.")
        except Exception as e:
            print(f"Грешка: {e}")

    def delete_user(self, current_user):
        print("\n--- ИЗТРИВАНЕ ОТ СИСТЕМАТА ---")
        target = input("Username или ID за изтриване (или 'отказ'): ").strip()
        if not target or target.lower() == 'отказ': return

        confirm = input(f"Сигурни ли сте, че триете '{target}' окончателно? (y/n): ").strip().lower()
        if confirm == 'y':
            try:
                self.controller.delete_user(current_user, target)
                print("[OK] Потребителят е изтрит.")
            except Exception as e:
                print(f"Грешка: {e}")
        else:
            print("Операцията е прекратена.")