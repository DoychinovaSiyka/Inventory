from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.category_controller import CategoryController
from models.user import User


class CategoryView:
    def __init__(self, controller: CategoryController):
        self.controller = controller

    def show_menu(self, user: User):
        is_admin = (user is not None and user.role == "Admin")

        # Списъкът вече показва категориите в йерархичен вид
        menu_items = [MenuItem("1", "Списък с категории (Йерархия)", self.show_all)]

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

    # Показваме категориите като дървовидна структура за по‑ясен преглед
    def show_all(self, _):
        categories = self.controller.get_all()

        if not categories:
            print("Няма категории.")
            return

        print("\nКатегории:\n")

        roots = [c for c in categories if not getattr(c, 'parent_id', None)]

        for root in roots:
            print(f"- {root.name} (ID: {root.category_id})")

            # Намираме подкатегориите на текущия корен
            children = [
                c for c in categories
                if str(getattr(c, 'parent_id', None)) == str(root.category_id)
            ]

            for child in children:
                print(f"  * {child.name} (ID: {child.category_id})")

        print()

    # Позволяваме избор на родителска категория от списък, вместо ръчно въвеждане на ID
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
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    parent_id = categories[idx].category_id
            except ValueError:
                print("Невалиден избор. Категорията ще бъде главна.")

        try:
            # Допълнителна проверка за валиден родител
            if parent_id and not self.controller.get_by_id(parent_id):
                print(f"Грешка: Родител с ID {parent_id} не съществува.")
                return

            self.controller.add(name=name, description=description, parent_id=parent_id)
            print("Категорията е добавена успешно!")
        except ValueError as e:
            print("Грешка:", e)

    # Позволяваме промяна на родителската категория
    def edit_category(self, _):
        categories = self.controller.get_all()
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat.name}")

        choice = input("\nВъведете номер на категория за редактиране: ").strip()
        try:
            idx = int(choice) - 1
            category = categories[idx]
            category_id = category.category_id
        except (ValueError, IndexError):
            print("Категорията не е намерена.")
            return

        print("\nОставете празно, ако не искате да променяте полето.")
        new_name = input(f"Ново име ({category.name}): ").strip()
        new_desc = input(f"Ново описание ({category.description}): ").strip()

        current_p = category.parent_id if getattr(category, 'parent_id', None) else "няма"

        # Избор на нов родител от списък с наличните категории
        print(f"\nИзберете нов родител (сега: {current_p})")
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
                    p_id = None
                else:
                    p_idx = int(new_parent_choice) - 1
                    p_id = categories[p_idx].category_id

                # Проверка за валиден родител
                if p_id and not self.controller.get_by_id(p_id):
                    print(f"Грешка: Родител с ID {p_id} не съществува.")
                    return

                if hasattr(self.controller, 'update_parent'):
                    self.controller.update_parent(category_id, p_id)
                else:
                    category.parent_id = p_id

            print("Категорията е обновена успешно!")
        except Exception as e:
            print("Грешка:", e)

    # Проверяваме дали категорията има подкатегории
    def delete_category(self, _):
        categories = self.controller.get_all()
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat.name}")

        choice = input("\nВъведете номер на категория за изтриване: ").strip()
        try:
            idx = int(choice) - 1
            category_id = categories[idx].category_id
            cat_name = categories[idx].name
        except (ValueError, IndexError):
            print("Категорията не е намерена.")
            return

        has_children = any(
            getattr(c, 'parent_id', None) and str(c.parent_id) == str(category_id)
            for c in categories
        )

        if has_children:
            print(f"Грешка: '{cat_name}' има подкатегории! Изтрийте или преместете тях първо.")
            return

        confirm = input(f"Наистина ли искате да изтриете '{cat_name}'? (y/n): ").strip().lower()
        if confirm == 'y':
            if self.controller.remove(category_id):
                print("Категорията е изтрита успешно!")
            else:
                print("Категорията не е намерена.")
