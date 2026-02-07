from menus.menu import Menu, MenuItem
from storage.password_utils import format_table
from controllers.category_controller import CategoryController
from models.user import User


class CategoryView:
    def __init__(self, controller: CategoryController):
        self.controller = controller

    def show_menu(self, user: User):
        is_admin = (user is not None and user.role == "Admin")

        menu_items = [
            MenuItem("1", "Списък с категории", self.show_all)
        ]

        if is_admin:
            menu_items.extend([
                MenuItem("2", "Добавяне на категория", self.add_category),
                MenuItem("3", "Редактиране на категория", self.edit_category),
                MenuItem("4", "Изтриване на категория", self.delete_category)
            ])

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))

        menu = Menu("Меню Категории", menu_items)

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # 1. Списък
    def show_all(self,_):
        categories = self.controller.get_all()

        if not categories:
            print("Няма категории.")
            return

        columns = ["ID", "Име", "Описание"]
        rows = [
            [c.category_id, c.name, c.description]
            for c in categories
        ]

        print("\n" + format_table(columns, rows))

    # 2. Добавяне
    def add_category(self, _):
        name = input("Име на категория: ").strip()
        description = input("Описание: ").strip()

        try:
            self.controller.add(name=name, description=description)
            print("Категорията е добавена успешно!")
        except ValueError as e:
            print("Грешка:", e)

    # 3. Редактиране
    def edit_category(self, _):
        category_id = input("Въведете ID на категория: ").strip()

        category = self.controller.get_by_id(category_id)

        if not category:
            print("Категорията не е намерена.")
            return

        print("\nОставете празно, ако не искате да променяте полето.")
        new_name = input(f"Ново име ({category.name}): ").strip()
        new_desc = input(f"Ново описание ({category.description}): ").strip()

        try:
            if new_name:
                self.controller.update_name(category_id, new_name)
            if new_desc:
                self.controller.update_description(category_id, new_desc)

            print("Категорията е обновена успешно!")
        except ValueError as e:
            print("Грешка:", e)

    # 4. Изтриване
    def delete_category(self, _):
        category_id = input("Въведете ID на категория: ").strip()

        if self.controller.remove(category_id):
            print("Категорията е изтрита успешно!")
        else:
            print("Категорията не е намерена.")
