from views.menu import Menu, MenuItem
from controllers.category_controller import CategoryController
from models.user import User


class CategoryView:
    def __init__(self, controller: CategoryController):
        self.controller = controller

    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice == "0" or choice is None:
                break
            menu_obj.execute(choice, user)

    def show_menu(self, user: User):
        is_admin = False
        if user is not None and user.role == "Admin":
            is_admin = True

        menu_items = [MenuItem("1", "Списък с категории", self.show_all)]

        if is_admin:
            menu_items.append(MenuItem("2", "Добавяне на категория", self.add_category))
            menu_items.append(MenuItem("3", "Редактиране на категория", self.edit_category))
            menu_items.append(MenuItem("4", "Изтриване на категория", self.delete_category))

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))

        menu = Menu("Меню категории", menu_items)
        self._run_menu(menu, user)

    def show_all(self, user: User):
        categories = self.controller.get_all()
        if not categories:
            print("\nНяма налични категории.")
            return

        print("\nКатегории (йерархия):")

        roots = []
        for c in categories:
            if not c.parent_id:
                roots.append(c)

        roots.sort(key=lambda x: x.name.lower())

        def print_tree(cat, level, prefix):
            indent = "   " * level
            short_id = cat.category_id[:8]

            if level == 0:
                print(f"{prefix}. {cat.name} (ID: {short_id})")
            else:
                print(f"{indent}- {cat.name} (ID: {short_id})")

            children = []
            for c in categories:
                if c.parent_id == cat.category_id:
                    children.append(c)

            children.sort(key=lambda x: x.name.lower())

            for child in children:
                print_tree(child, level + 1, prefix)

        index = 1
        for root in roots:
            print_tree(root, 0, str(index))
            index += 1

    def add_category(self, user: User):
        print("\nНова категория")
        print("(Напишете 'отказ' за изход)")

        while True:
            name = input("Име на категория: ").strip()
            if name.lower() == 'отказ':
                return
            if name == "":
                print("Името не може да бъде празно.")
                continue
            break

        while True:
            description = input("Описание (мин. 3 символа): ").strip()
            if description.lower() == 'отказ':
                return
            if len(description) < 3:
                print("Описанието е твърде кратко.")
                continue
            break

        print("\nИзберете родителска категория (Enter за главна):")
        parent = self.select_category()

        parent_id = None
        if parent is not None:
            parent_id = parent.category_id

        try:
            current_uid = "unknown"
            if user is not None:
                current_uid = user.user_id

            self.controller.add(
                {"name": name, "description": description, "parent_id": parent_id},
                user_id=current_uid)
            print(f"Категорията '{name}' е добавена.")
        except Exception as e:
            print(f"Грешка: {e}")

    def edit_category(self, user: User):
        print("\nРедактиране на категория")
        category = self.select_category()
        if category is None:
            return

        current_uid = "unknown"
        if user is not None:
            current_uid = user.user_id

        print(f"\nРедактирате: {category.name}")
        print("(Enter запазва старата стойност, 'отказ' за изход)")

        new_name = None
        while True:
            name_input = input(f"Ново име [{category.name}]: ").strip()
            if name_input.lower() == 'отказ':
                return
            if name_input == "":
                break
            new_name = name_input
            break

        new_desc = None
        while True:
            desc_input = input(f"Ново описание [{category.description}]: ").strip()
            if desc_input.lower() == 'отказ':
                return
            if desc_input == "":
                break
            if len(desc_input) < 3:
                print("Описанието трябва да е поне 3 символа.")
                continue
            new_desc = desc_input
            break

        print("Изберете нов родител (Enter за без промяна):")
        parent = self.select_category()

        try:
            if new_name is not None:
                self.controller.update_name(category.category_id, new_name, current_uid)

            if new_desc is not None:
                self.controller.update_description(category.category_id, new_desc, current_uid)

            if parent is not None:
                if parent.category_id != category.category_id:
                    self.controller.update_parent(category.category_id, parent.category_id, current_uid)

            print("Категорията е обновена.")
        except Exception as e:
            print(f"Грешка: {e}")

    def select_category(self):
        categories = self.controller.get_all()
        if not categories:
            return None

        categories.sort(key=lambda x: x.name.lower())

        index = 1
        for cat in categories:
            print(f"{index}. {cat.name} ({cat.category_id[:8]})")
            index += 1

        while True:
            choice = input("\nИзбор (номер или ID, Enter за отказ): ").strip()
            if choice == "":
                return None

            found = self.controller.get_by_id(choice)
            if found is not None:
                return found

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    return categories[idx]

            print("Невалиден избор. Опитайте отново.")

    def delete_category(self, user: User):
        print("\nИзтриване на категория")
        category = self.select_category()
        if category is None:
            return

        print(f"Продуктите в '{category.name}' ще останат без категория.")
        confirm = input("Потвърждавате ли изтриването? (y/n): ").strip().lower()

        if confirm == "y":
            try:
                self.controller.remove(category.category_id, user.user_id)
                print("Категорията е изтрита.")
            except Exception as e:
                print(f"Грешка: {e}")
        else:
            print("Операцията е прекратена.")
