from views.menu import Menu, MenuItem
from controllers.category_controller import CategoryController
from models.user import User


class CategoryView:
    def __init__(self, controller: CategoryController):
        self.controller = controller

    def show_menu(self, user: User):
        while True:
            is_admin = (user is not None and user.role == "Admin")
            menu = self._build_menu(is_admin)
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    def _build_menu(self, is_admin: bool):
        menu_items = [MenuItem("1", "Списък с категории (Йерархия)", self.show_all)]
        if is_admin:
            menu_items.extend([
                MenuItem("2", "Добавяне на категория", self.add_category),
                MenuItem("3", "Редактиране на категория", self.edit_category),
                MenuItem("4", "Изтриване на категория", self.delete_category)
            ])

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Меню Категории", menu_items)

    def show_all(self, user: User):
        categories = self.controller.get_all()
        if not categories:
            print("\n--- Няма налични категории ---")
            return

        print("\n=== Категории (йерархия) ===")
        roots = [c for c in categories if not c.parent_id]
        roots.sort(key=lambda x: x.name.lower())

        def print_tree(cat, level, prefix):
            indent = "   " * level
            short_id = cat.category_id[:8]

            if level == 0:
                print(f"{prefix}. {cat.name} [ID: {short_id}]")
            else:
                print(f"{indent}- {cat.name} [ID: {short_id}]")

            children = [c for c in categories if c.parent_id == cat.category_id]
            children.sort(key=lambda x: x.name.lower())
            for child in children:
                print_tree(child, level + 1, prefix)

        for i, root in enumerate(roots, 1):
            print_tree(root, 0, str(i))
        print("-" * 30)

    def add_category(self, user: User):
        print("\n--- Добавяне на категория ---")
        name = input("Име на категория (Enter = отказ): ").strip()
        if not name: return

        description = input("Описание: ").strip()
        if len(description) < 3:
            print("Грешка: Описанието трябва да е поне 3 символа.")
            return

        print("\nИзберете родителска категория (Enter за Главна):")
        parent = self.select_category()
        parent_id = parent.category_id if parent else None

        try:
            current_uid = user.user_id if user else "unknown"
            self.controller.add({
                "name": name,
                "description": description,
                "parent_id": parent_id
            }, user_id=current_uid)
            print("Категорията е добавена успешно!")
        except ValueError as e:
            print("Грешка:", e)

    def edit_category(self, user: User):
        print("\n--- Редактиране на категория ---")
        category = self.select_category()
        if not category: return

        category_id = category.category_id
        current_uid = user.user_id if user else "unknown"

        print(f"\nТекущо име: {category.name}")
        new_name = input("Ново име (Enter за запазване): ").strip() or None

        print(f"Текущо описание: {category.description}")
        new_desc = input("Ново описание (Enter за запазване): ").strip() or None

        # Добавена валидация за описанието при редакция
        if new_desc and len(new_desc) < 3:
            print("Грешка: Новото описание е твърде кратко. Промяната не е записана.")
            new_desc = None

        print(f"\nИзберете нов родител за '{category.name}' (Enter за запазване):")
        parent = self.select_category()

        try:
            if new_name:
                self.controller.update_name(category_id, new_name, current_uid)
            if new_desc:
                self.controller.update_description(category_id, new_desc, current_uid)

            if parent:
                # Тук контролерът трябва да проверява за "Циклична връзка"
                # (не може категорията да е родител на себе си)
                if parent.category_id == category_id:
                    print("Грешка: Категорията не може да бъде родител на самата себе си.")
                else:
                    self.controller.update_parent(category_id, parent.category_id, current_uid)

            print("Обновяването приключи.")
        except Exception as e:
            print("Грешка:", e)

    def delete_category(self, user: User):
        print("\n--- Изтриване на категория ---")
        category = self.select_category()
        if not category: return

        print("ПРЕДУПРЕЖДЕНИЕ: Продуктите в тази категория ще останат без категория.")
        confirm = input(f"Сигурни ли сте, че триете '{category.name}'? (y/n): ").strip().lower()
        if confirm == "y":
            try:
                self.controller.remove(category.category_id, user.user_id)
                print("Изтрито успешно!")
            except ValueError as e:
                print("Грешка:", e)

    def select_category(self):
        """ Помощен метод за избор. """
        categories = self.controller.get_all()
        if not categories:
            return None

        # Сортираме за по-лесен избор
        categories.sort(key=lambda x: x.name.lower())

        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat.name} [{cat.category_id[:8]}]")

        choice = input("\nИзбор (номер или ID, Enter за отказ): ").strip()
        if not choice: return None

        # Проверка по кратко ID
        found = self.controller.get_by_id(choice)
        if found: return found

        # Проверка по номер
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(categories):
                return categories[idx]

        print("Невалиден избор.")
        return None