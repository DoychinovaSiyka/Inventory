from views.menu import Menu, MenuItem
from controllers.category_controller import CategoryController
from models.user import User


class CategoryView:
    def __init__(self, controller: CategoryController):
        self.controller = controller
        self.menu = None  # менюто се създава динамично според ролята

    def show_menu(self, user: User):
        is_admin = (user is not None and user.role == "Admin")
        self.menu = self._build_menu(is_admin)
        while True:
            choice = self.menu.show()
            result = self.menu.execute(choice, user)
            if result == "break":
                break

    # Създавам менюто отделно
    def _build_menu(self, is_admin: bool):
        menu_items = [MenuItem("1", "Списък с категории (Йерархия)", self.show_all)]
        if is_admin:
            menu_items.extend([MenuItem("2", "Добавяне на категория", self.add_category),
                               MenuItem("3", "Редактиране на категория", self.edit_category),
                               MenuItem("4", "Изтриване на категория", self.delete_category)])

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Меню Категории", menu_items)



    def show_all(self, _):
        categories = self.controller.get_all()
        if not categories:
            print("Няма категории.")
            return

        print("\nКатегории (йерархия):\n")
        # намираме root категориите
        roots = [c for c in categories if c.parent_id is None]
        roots.sort(key=lambda x: x.name.lower())

        def print_tree(cat, level, prefix):
            indent = "   " * level
            if level == 0:
                # главна категория - номер
                print(f"{prefix}. {cat.name} (ID: {cat.category_id})")
            else:
                # подкатегория - тире
                print(f"{indent}- {cat.name} (ID: {cat.category_id})")

            # деца
            children = [c for c in categories if c.parent_id == cat.category_id]
            children.sort(key=lambda x: x.name.lower())

            for child in children:
                print_tree(child, level + 1, prefix)

        # извеждаме root категориите с номерация
        for i, root in enumerate(roots, 1):
            print_tree(root, 0, str(i))

        print()

    # Добавяне на категория
    def add_category(self, _):
        name = input("Име на категория: ").strip()
        description = input("Описание: ").strip()

        print("\nОставете празно за главна категория или въведете НОМЕР или ID на родител:")
        parent = self.select_category()
        parent_id = parent.category_id if parent else None

        try:
            self.controller.add({"name": name, "description": description, "parent_id": parent_id},
                                user_id="system")
            print("Категорията е добавена успешно!")
        except ValueError as e:
            print("Грешка:", e)


    def edit_category(self, _):
        print("\nИзберете категория за редактиране:")
        category = self.select_category()
        if not category:
            return

        category_id = category.category_id
        print("\nОставете празно, ако не искате да променяте полето.")
        print(f"Текущо име: {category.name}")
        new_name = input("Ново име: ").strip()

        print(f"Текущо описание: {category.description}")
        new_desc = input("Ново описание: ").strip()

        print("\nИзберете нов родител (номер или ID) или оставете празно за главна категория:")
        parent = self.select_category()
        parent_id = parent.category_id if parent else None
        try:
            if new_name:
                self.controller.update_name(category_id, new_name, "system")
            if new_desc:
                self.controller.update_description(category_id, new_desc, "system")

            self.controller.update_parent(category_id, parent_id, "system")

            print("Категорията е обновена успешно!")
        except Exception as e:
            print("Грешка:", e)

    # Изтриване на категория
    def delete_category(self, _):
        print("\nИзберете категория за изтриване:")
        category = self.select_category()
        if not category:
            return

        confirm = input(f"Наистина ли искате да изтриете '{category.name}'? (y/n): ").strip().lower()
        if confirm != "y":
            return
        try:
            self.controller.remove(category.category_id, "system")
            print("Категорията е изтрита успешно!")
        except ValueError as e:
            print("Грешка:", e)


    #  Избор по НОМЕР или по ID
    def select_category(self):
        categories = self.controller.get_all()
        if not categories:
            print("Няма категории.")
            return None

        print("\nКатегории:")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat.name} (ID: {cat.category_id})")

        while True:
            choice = input("Въведете номер или ID: ").strip()

            if choice == "":
                print("Операцията е отказана.\n")
                return None

            # избор по ID
            for cat in categories:
                if choice.lower() == cat.category_id.lower():
                    return cat

            # избор по номер
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(categories):
                    return categories[index]

            print("Невалиден избор.")
            print("Моля, опитайте отново.\n")
