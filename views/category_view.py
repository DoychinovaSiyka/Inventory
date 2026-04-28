from views.menu import Menu, MenuItem
from controllers.category_controller import CategoryController
from models.user import User


class CategoryView:
    def __init__(self, controller: CategoryController):
        self.controller = controller

    def show_menu(self, user: User):
        while True:
            # Проверявам ролята на потребителя
            is_admin = (user is not None and user.role == "Admin")
            menu = self._build_menu(is_admin)
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    def _build_menu(self, is_admin: bool):
        menu_items = [MenuItem("1", "Списък с категории (Йерархия)", self.show_all)]
        # Проверка за права - само за администратори
        if is_admin:
            menu_items.extend([MenuItem("2", "Добавяне на категория", self.add_category),
                               MenuItem("3", "Редактиране на категория", self.edit_category),
                               MenuItem("4", "Изтриване на категория", self.delete_category)])

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Меню Категории", menu_items)

    def show_all(self, user: User):
        categories = self.controller.get_all()
        if not categories:
            print("Няма категории.")
            return

        print("\nКатегории (йерархия):\n")
        # взимам главните категории - без родител
        roots = [c for c in categories if c.parent_id is None]
        roots.sort(key=lambda x: x.name.lower())

        def print_tree(cat, level, prefix):
            indent = "   " * level
            if level == 0:
                print(f"{prefix}. {cat.name} (ID: {cat.category_id})")
            else:
                print(f"{indent}- {cat.name} (ID: {cat.category_id})")

            # рекурсивно намирам децата
            children = [c for c in categories if c.parent_id == cat.category_id]
            children.sort(key=lambda x: x.name.lower())
            for child in children:
                print_tree(child, level + 1, prefix)

        for i, root in enumerate(roots, 1):
            print_tree(root, 0, str(i))

        print()

    def add_category(self, user: User):
        name = input("Име на категория (Enter = отказ): ").strip()
        if not name:
            print("Операцията е отказана.")
            return
        description = input("Описание (Enter = отказ): ").strip()
        if not description:
            print("Операцията е отказана.")
            return
        if len(description) < 3:
            print("Грешка: Описанието е твърде кратко (минимум 3 символа).")
            return

        print("\nОставете празно за главна категория или въведете НОМЕР или ID на родител:")
        parent = self.select_category()
        parent_id = parent.category_id if parent else None

        try:
            # Използвам актуалното ID на потребителя вместо "system"
            current_uid = user.user_id if user else "unknown"
            self.controller.add({"name": name, "description": description, "parent_id": parent_id},
                                user_id=current_uid)
            print("Категорията е добавена успешно!")
        except ValueError as e:
            print("Грешка:", e)

    def edit_category(self, user: User):
        print("\nИзберете категория за редактиране:")
        category = self.select_category()
        if not category:
            return

        category_id = category.category_id
        current_uid = user.user_id if user else "unknown"
        print("\nОставете празно, ако не искате да променяте полето.")
        print(f"Текущо име: {category.name}")
        new_name = input("Ново име: ").strip()
        print(f"Текущо описание: {category.description}")
        new_desc = input("Ново описание: ").strip()
        if new_desc and len(new_desc) < 3:
            print("Грешка: Описанието е твърде кратко (минимум 3 символа).")
            return

        print("\nИзберете нов родител (номер или ID) или оставете празно за главна категория:")
        parent = self.select_category()
        parent_id = parent.category_id if parent else None

        try:
            if new_name:
                self.controller.update_name(category_id, new_name, current_uid)
            if new_desc:
                self.controller.update_description(category_id, new_desc, current_uid)

            self.controller.update_parent(category_id, parent_id, current_uid)
            print("Категорията е обновена успешно!")
        except Exception as e:
            print("Грешка:", e)


    def delete_category(self, user: User):
        print("\nИзберете категория за изтриване:")
        category = self.select_category()
        if not category:
            return

        confirm = input(f"Наистина ли искате да изтриете '{category.name}'? (y/n): ").strip().lower()
        if confirm != "y":
            return
        current_uid = user.user_id if user else "unknown"
        try:
            self.controller.remove(category.category_id, current_uid)
            print("Категорията е изтрита успешно!")
        except ValueError as e:
            print("Грешка:", e)

    def select_category(self):
        """ Помощен метод за избор на категория от списък. """
        categories = self.controller.get_all()
        if not categories:
            print("Няма категории.")
            return None
        print("\nНалични категории:")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat.name} (ID: {cat.category_id})")

        while True:
            choice = input("Въведете номер или ID (Enter = отказ): ").strip()
            if choice == "":
                return None

            # Търсене по ID
            for cat in categories:
                if choice.lower() == cat.category_id.lower():
                    return cat

            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(categories):
                    return categories[index]

            print("[!] Невалиден избор. Опитайте отново.\n")