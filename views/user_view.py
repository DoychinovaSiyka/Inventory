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
        print("\nНОВ ПОТРЕБИТЕЛ (Enter за отказ)")
        while True:
            username = input("Потребителско име: ").strip()
            if not username: return
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



    def delete_user(self, current_user):
        print("\nИЗТРИВАНЕ")
        target = input("Username или ID за изтриване: ").strip()
        if not target:
            return

        try:
            self.controller.delete_user(current_user, target)
            print("Потребителят е изтрит.")
        except (ValueError, PermissionError) as e:
            print(f"Грешка: {e}")