from views.menu import Menu, MenuItem
from views.password_utils import input_password, format_table


class UserView:
    def __init__(self, controller):
        self.controller = controller


    def show_menu(self, user):
        if not self.controller.is_admin(user):
            print("\nНямате администраторски права.")
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
            MenuItem("0", "Назад", lambda u: "break")])


    def show_users(self, _):
        users = self.controller.get_all()
        if not users:
            print("\nНяма регистрирани потребители.")
            return

        print("\nСПИСЪК НА ПОТРЕБИТЕЛИТЕ")
        columns = ["ID", "Username", "Имейл", "Роля", "Статус"]
        rows = [[u.user_id[:8], u.username, u.email, u.role, u.status] for u in users]
        print(format_table(columns, rows))


    def add_user(self, _):
        print("\nНОВ ПОТРЕБИТЕЛ")

        while True:
            username = input("Потребителско име: ").strip()
            if not username:
                return
            error = self.controller.validate_field("username", username)
            if not error:
                break
            print(f"Грешка: {error}")

        while True:
            email = input("Имейл: ").strip()
            error = self.controller.validate_field("email", email)
            if not error:
                break
            print(f"Грешка: {error}")

        while True:
            password = input_password("Парола: ").strip()
            error = self.controller.validate_field("password", password)
            if not error:
                break
            print(f"Грешка: {error}")

        while True:
            role = input("Роля (Admin/Operator) [Operator]: ").strip().capitalize() or "Operator"
            error = self.controller.validate_field("role", role)
            if not error:
                break
            print(f"Грешка: {error}")

        fn = input("Име (Enter за '-' ): ").strip() or "-"
        ln = input("Фамилия (Enter за '-' ): ").strip() or "-"

        try:
            self.controller.register(fn, ln, email, username, password, role)
            print(f"\nПотребител '{username}' е добавен успешно.")
        except Exception as e:
            print(f"\nГрешка при запис: {e}")



    def change_role(self, current_user):
        print("\nПРОМЯНА НА РОЛЯ")
        target = input("Въведете Username или ID: ").strip()
        if not target:
            return

        user_obj = self.controller.find_user_flexible(target)
        if not user_obj:
            print(f"Грешка: Потребител '{target}' не е намерен.")
            return

        print(f"Текуща роля: {user_obj.role}")
        new_role = input("Нова роля (Admin/Operator): ").strip().capitalize()

        if new_role not in ["Admin", "Operator"]:
            print("Грешка: Невалидна роля. Разрешени: Admin, Operator.")
            return

        try:
            self.controller.change_role(current_user, user_obj.user_id, new_role)
            print(f"Ролята на '{user_obj.username}' е променена на {new_role}.")
        except Exception as e:
            print(f"Грешка: {e}")



    def deactivate_user(self, current_user):
        print("\nДЕАКТИВИРАНЕ НА ПОТРЕБИТЕЛ")

        target = input("Username или ID: ").strip()
        if not target:
            return

        try:
            self.controller.deactivate_user(current_user, target)
            print(f"Потребител '{target}' е деактивиран.")
        except Exception as e:
            print(f"Грешка: {e}")



    def activate_user(self, current_user):
        print("\nАКТИВИРАНЕ НА ПОТРЕБИТЕЛ")

        target = input("Username или ID: ").strip()
        if not target:
            return

        try:
            self.controller.activate_user(current_user, target)
            print(f"Потребител '{target}' е активиран.")
        except Exception as e:
            print(f"Грешка: {e}")



    def delete_user(self, current_user):
        print("\nИЗТРИВАНЕ")

        while True:
            target = input("Username или ID за изтриване: ").strip()
            if not target:
                return

            user_to_delete = self.controller.find_user_flexible(target)
            if not user_to_delete:
                print(f"Потребител '{target}' не съществува.")
                continue

            break

        try:
            self.controller.delete_user(current_user, target)
            print(f"Потребителят '{target}' е изтрит успешно.")
        except Exception as e:
            print(f"Грешка: {e}")
