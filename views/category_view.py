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
        is_admin = (user is not None and user.role == "Admin")
        menu_items = [MenuItem("1", "Списък с категории", self.show_all)]

        if is_admin:
            menu_items.extend([
                MenuItem("2", "Добавяне на категория", self.add_category),
                MenuItem("3", "Редактиране на категория", self.edit_category),
                MenuItem("4", "Изтриване на категория", self.delete_category)
            ])

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))
        menu = Menu("Меню категории", menu_items)
        self._run_menu(menu, user)

    def show_all(self, user: User):
        categories = self.controller.get_all()
        if not categories:
            print("\nНяма налични категории.")
            return

        print("\nКатегории (йерархия):")
        roots = [c for c in categories if not c.parent_id]
        roots.sort(key=lambda x: x.name.lower())

        def print_tree(cat, level, prefix):
            indent = "   " * level
            short_id = cat.category_id[:8]
            if level == 0:
                print(f"{prefix}. {cat.name} (ID: {short_id})")
            else:
                print(f"{indent}- {cat.name} (ID: {short_id})")

            children = [c for c in categories if c.parent_id == cat.category_id]
            children.sort(key=lambda x: x.name.lower())
            for child in children:
                print_tree(child, level + 1, prefix)

        for i, root in enumerate(roots, 1):
            print_tree(root, 0, str(i))

    def add_category(self, user: User):
        print("\nНова категория")
        print("(Напишете 'отказ' за изход)")

        while True:
            name = input("Име на категория: ").strip()
            if name.lower() == 'отказ':
                return
            if not name:
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
        parent_id = parent.category_id if parent else None

        try:
            current_uid = user.user_id if user else "unknown"
            self.controller.add(
                {"name": name, "description": description, "parent_id": parent_id},
                user_id=current_uid
            )
            print(f"Категорията '{name}' е добавена.")
        except Exception as e:
            print(f"Грешка: {e}")

    def edit_category(self, user: User):
        print("\nРедактиране на категория")
        category = self.select_category()
        if not category:
            return

        current_uid = user.user_id if user else "unknown"
        print(f"\nРедактирате: {category.name}")
        print("(Enter запазва старата стойност, 'отказ' за изход)")

        while True:
            new_name = input(f"Ново име [{category.name}]: ").strip()
            if new_name.lower() == 'отказ':
                return
            if not new_name:
                new_name = None
                break
            break

        while True:
            new_desc = input(f"Ново описание [{category.description}]: ").strip()
            if new_desc.lower() == 'отказ':
                return
            if not new_desc:
                new_desc = None
                break
            if len(new_desc) < 3:
                print("Описанието трябва да е поне 3 символа.")
                continue
            break

        print("Изберете нов родител (Enter за без промяна):")
        parent = self.select_category()

        try:
            if new_name:
                self.controller.update_name(category.category_id, new_name, current_uid)
            if new_desc:
                self.controller.update_description(category.category_id, new_desc, current_uid)
            if parent and parent.category_id != category.category_id:
                self.controller.update_parent(category.category_id, parent.category_id, current_uid)

            print("Категорията е обновена.")
        except Exception as e:
            print(f"Грешка: {e}")

    def select_category(self):
        categories = self.controller.get_all()
        if not categories:
            return None

        categories.sort(key=lambda x: x.name.lower())
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat.name} ({cat.category_id[:8]})")

        while True:
            choice = input("\nИзбор (номер или ID, Enter за отказ): ").strip()
            if not choice:
                return None

            found = self.controller.get_by_id(choice)
            if found:
                return found

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    return categories[idx]

            print("Невалиден избор. Опитайте отново.")

    def delete_category(self, user: User):
        print("\nИзтриване на категория")
        category = self.select_category()
        if not category:
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
