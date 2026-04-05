from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.category_controller import CategoryController
from models.user import User


class CategoryView:
    def __init__(self, controller: CategoryController):
        self.controller = controller
        self.menu = None  # менюто ще се създава динамично според ролята

    # Основно меню
    def show_menu(self, user: User):
        is_admin = (user is not None and user.role == "Admin")
        self.menu = self._build_menu(is_admin)

        while True:
            choice = self.menu.show()
            result = self.menu.execute(choice, user)
            if result == "break":
                break

    # Създаване на менюто отделно
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

    # Показване на дървовидна структура
    def show_all(self, _):
        categories = self.controller.get_all()

        if not categories:
            print("Няма категории.")
            return

        print("\nКатегории:\n")

        # Главни категории = тези без parent_id
        roots = []
        for c in categories:
            has_parent = hasattr(c, "parent_id") and c.parent_id
            if not has_parent:
                roots.append(c)

        for root in roots:
            print(f"- {root.name} (ID: {root.category_id})")

            # Подкатегории
            children = [c for c in categories if hasattr(c, "parent_id") and c.parent_id == root.category_id]

            for child in children:
                print(f"  * {child.name} (ID: {child.category_id})")

        print()

    # Добавяне на категория
    def add_category(self, _):
        name = input("Име на категория: ").strip()
        description = input("Описание: ").strip()

        categories = self.controller.get_all()

        print("\nОставете празно за главна категория или изберете номер на родител:")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat.name}")

        choice = input("Избор (номер): ").strip()
        parent_id = None

        if choice:
            try:
                index = int(choice) - 1
                if 0 <= index < len(categories):
                    parent_id = categories[index].category_id
            except ValueError:
                print("Невалиден избор. Категорията ще бъде главна.")

        try:
            if parent_id:
                exists = self.controller.get_by_id(parent_id)
                if not exists:
                    print(f"Грешка: Родител с ID {parent_id} не съществува.")
                    return

            self.controller.add(name=name, description=description, parent_id=parent_id)
            print("Категорията е добавена успешно!")
        except ValueError as e:
            print("Грешка:", e)


    # Редактиране на категория
    def edit_category(self, _):
        categories = self.controller.get_all()

        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat.name}")

        choice = input("\nВъведете номер на категория за редактиране: ").strip()

        try:
            index = int(choice) - 1
            category = categories[index]
        except (ValueError, IndexError):
            print("Категорията не е намерена.")
            return

        category_id = category.category_id

        print("\nОставете празно, ако не искате да променяте полето.")
        new_name = input(f"Ново име ({category.name}): ").strip()
        new_desc = input(f"Ново описание ({category.description}): ").strip()

        if hasattr(category, "parent_id") and category.parent_id:
            current_parent = category.parent_id
        else:
            current_parent = "няма"

        print(f"\nИзберете нов родител (сега: {current_parent})")
        print("Напишете 'none' за главна категория или номер от списъка:")

        for i, cat in enumerate(categories, 1):
            if cat.category_id != category_id:
                print(f"{i}. {cat.name}")

        new_parent_choice = input("Избор: ").strip()

        try:
            if new_name:
                self.controller.update_name(category_id, new_name)

            if new_desc:
                self.controller.update_description(category_id, new_desc)

            if new_parent_choice:
                if new_parent_choice.lower() == "none":
                    parent_id = None
                else:
                    parent_index = int(new_parent_choice) - 1
                    parent_id = categories[parent_index].category_id

                if parent_id:
                    exists = self.controller.get_by_id(parent_id)
                    if not exists:
                        print(f"Грешка: Родител с ID {parent_id} не съществува.")
                        return

                if hasattr(self.controller, "update_parent"):
                    self.controller.update_parent(category_id, parent_id)
                else:
                    category.parent_id = parent_id

            print("Категорията е обновена успешно!")
        except Exception as e:
            print("Грешка:", e)


    # Изтриване на категория
    def delete_category(self, _):
        categories = self.controller.get_all()

        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat.name}")

        choice = input("\nВъведете номер на категория за изтриване: ").strip()

        try:
            index = int(choice) - 1
            category = categories[index]
        except (ValueError, IndexError):
            print("Категорията не е намерена.")
            return

        category_id = category.category_id
        cat_name = category.name

        # Проверка за подкатегории
        has_children = any(hasattr(c, "parent_id") and c.parent_id == category_id for c in categories)
        if has_children:
            print(f"Грешка: '{cat_name}' има подкатегории! Изтрийте или преместете тях първо.")
            return

        confirm = input(f"Наистина ли искате да изтриете '{cat_name}'? (y/n): ").strip().lower()
        if confirm == "y":
            removed = self.controller.remove(category_id)
            if removed:
                print("Категорията е изтрита успешно!")
            else:
                print("Категорията не е намерена.")
