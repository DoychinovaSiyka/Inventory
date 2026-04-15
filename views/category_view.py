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

        # Главни категории - без parent_id
        roots = [c for c in categories if c.parent_id is None]
        for root in roots:
            print(f"- {root.name} (ID: {root.category_id})")
            # Подкатегории
            children = [c for c in categories if c.parent_id == root.category_id]
            for child in children:
                print(f"  * {child.name} (ID: {child.category_id})")
        print()

    # Добавяне на категория
    def add_category(self, _):
        name = input("Име на категория: ").strip()
        description = input("Описание: ").strip()
        print("\nОставете празно за главна категория или изберете номер на родител:")
        parent = self.select_category()
        parent_id = parent.category_id if parent else None
        try:
            # подаваме данните като dict, както контролерът очаква
            self.controller.add({"name": name, "description": description, "parent_id": parent_id},
                                user_id="system")
            print("Категорията е добавена успешно!")
        except ValueError as e:
            print("Грешка:", e)

    # Редактиране на категория
    def edit_category(self, _):
        print("\nИзберете категория за редактиране:")
        category = self.select_category()
        if not category:
            return
        category_id = category.category_id
        print("\nОставете празно, ако не искате да променяте полето.")
        new_name = input(f"Ново име ({category.name}): ").strip()
        new_desc = input(f"Ново описание ({category.description}): ").strip()
        print("\nИзберете нов родител или оставете празно за главна категория:")
        parent = self.select_category()
        parent_id = parent.category_id if parent else None
        try:
            if new_name:
                self.controller.update_name(category_id, new_name, "system")
            if new_desc:
                self.controller.update_description(category_id, new_desc, "system")

            # обновяваме родителя - валидаторът ще реши дали е позволено
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

    # Помощен метод за избор на категория
    def select_category(self):
        categories = self.controller.get_all()
        if not categories:
            print("Няма категории.")
            return None

        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat.name}")

        choice = input("Въведете номер: ").strip()
        if not choice.isdigit():
            print("Невалиден избор.")
            return None

        index = int(choice) - 1
        if 0 <= index < len(categories):
            return categories[index]

        print("Невалиден избор.")
        return None
