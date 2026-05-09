from views.menu import Menu, MenuItem


class CategoryView:
    def __init__(self, controller):
        self.controller = controller

    # --- Помощни методи за конзолна валидация ---

    def _ask_required_string(self, prompt, min_len=2):
        """Принуждава потребителя да въведе текст с минимална дължина."""
        while True:
            val = input(prompt).strip()
            if val.lower() == 'отказ':
                return 'cancel'
            if not val:
                print("Грешка: Полето не може да бъде празно!")
                continue
            if len(val) < min_len:
                print(f"Грешка: Текстът трябва да е поне {min_len} символа!")
                continue
            return val

    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice == "0" or choice is None:
                break
            menu_obj.execute(choice, user)

    # --- Основни методи ---

    def show_menu(self, user):
        is_admin = user is not None and getattr(user, 'role', None) == "Admin"

        menu_items = [MenuItem("1", "Списък с категории", self.show_all)]

        if is_admin:
            menu_items.append(MenuItem("2", "Добавяне на категория", self.add_category))
            menu_items.append(MenuItem("3", "Редактиране на категория", self.edit_category))
            menu_items.append(MenuItem("4", "Изтриване на категория", self.delete_category))

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))

        menu = Menu("Меню Категории", menu_items)
        self._run_menu(menu, user)

    def show_all(self, _):
        categories = self.controller.get_all()
        if not categories:
            print("\nНяма налични категории.")
            return

        print("\nЙерархия на категориите:")

        def print_tree(parent_id=None, level=0):
            children = [c for c in categories if c.parent_id == parent_id]
            children.sort(key=lambda x: x.name.lower())

            for child in children:
                indent = "  " * level
                prefix = "•" if level == 0 else "└─"
                print(f"{indent}{prefix} {child.name} ({child.category_id[:8]})")
                print_tree(child.category_id, level + 1)

        print_tree()
        input("\nНатиснете Enter за продължение...")

    def add_category(self, user):
        print("\n--- НОВА КАТЕГОРИЯ ---")
        print("(Напишете 'отказ' за прекратяване)")

        name = self._ask_required_string("Име на категория: ", min_len=2)
        if name == 'cancel': return

        description = self._ask_required_string("Описание: ", min_len=3)
        if description == 'cancel': return

        print("\nИзберете родителска категория (Enter за главна):")
        parent = self.select_category()
        parent_id = parent.category_id if parent else None

        try:
            self.controller.add(
                {"name": name, "description": description, "parent_id": parent_id},
                user_id=user.user_id
            )
            print(f"\n[OK] Категорията '{name}' е създадена успешно.")
        except Exception as e:
            print(f"Грешка: {e}")

    def edit_category(self, user):
        print("\n--- РЕДАКТИРАНЕ ---")
        category = self.select_category()
        if not category: return

        print(f"\nРедактирате: {category.name}")
        print("(Enter запазва старата стойност, 'отказ' за изход)")

        while True:
            new_name = input(f"Ново име [{category.name}]: ").strip()
            if new_name.lower() == 'отказ': return
            if not new_name:
                new_name = category.name
                break
            if len(new_name) < 2:
                print("Грешка: Името трябва да е поне 2 символа!")
                continue
            break

        while True:
            new_desc = input(f"Ново описание [{category.description}]: ").strip()
            if new_desc.lower() == 'отказ': return
            if not new_desc:
                new_desc = category.description
                break
            if len(new_desc) < 3:
                print("Грешка: Описанието трябва да е поне 3 символа!")
                continue
            break

        print("\nИзберете нов родител (Enter за без промяна):")
        parent = self.select_category()

        try:
            self.controller.update_name(category.category_id, new_name, user.user_id)
            self.controller.update_description(category.category_id, new_desc, user.user_id)
            if parent:
                self.controller.update_parent(category.category_id, parent.category_id, user.user_id)
            print("\n[OK] Промените са запазени.")
        except Exception as e:
            print(f"Грешка: {e}")

    def select_category(self):
        """Метод за избор с вграден While True цикъл за защита."""
        while True:
            categories = sorted(self.controller.get_all(), key=lambda x: x.name.lower())
            if not categories: return None

            print("\nСписък категории:")
            for i, cat in enumerate(categories, 1):
                print(f"{i}. {cat.name} ({cat.category_id[:8]})")

            choice = input("\nИзбор (номер или ID, Enter за отказ): ").strip()
            if not choice: return None
            if choice.lower() == 'отказ': return None

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    return categories[idx]

            found = self.controller.get_by_id(choice)
            if found: return found

            print("Грешка: Невалиден избор. Моля, изберете съществуващ номер или ID.")

    def delete_category(self, user):
        print("\n--- ИЗТРИВАНЕ ---")
        category = self.select_category()
        if not category: return

        print(f"ВНИМАНИЕ: Продуктите в '{category.name}' ще останат без категория.")
        confirm = input(f"Сигурни ли сте, че триете '{category.name}'? (y/n): ").strip().lower()

        if confirm == 'y':
            try:
                self.controller.remove(category.category_id, user.user_id)
                print(f"\n[OK] Категорията '{category.name}' е изтрита.")
            except Exception as e:
                print(f"Грешка: {e}")
        else:
            print("Операцията е прекратена.")