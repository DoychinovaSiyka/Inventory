from views.menu import Menu, MenuItem


class CategoryView:
    def __init__(self, controller):
        self.controller = controller

    def _ask_required_string(self, prompt, min_len=2):
        while True:
            value = input(prompt).strip()
            if value.lower() == "отказ":
                return "cancel"

            if not value:
                print("Полето е празно.")
                continue

            if len(value) < min_len:
                print(f"Трябват поне {min_len} символа.")
                continue

            return value

    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice in ("0", None):
                break
            menu_obj.execute(choice, user)

    def show_menu(self, user):
        is_admin = user and getattr(user, "role", "") == "Admin"

        items = [MenuItem("1", "Списък с категории", self.show_all)]

        if is_admin:
            items.append(MenuItem("2", "Добавяне на категория", self.add_category))
            items.append(MenuItem("3", "Редактиране на категория", self.edit_category))
            items.append(MenuItem("4", "Изтриване на категория", self.delete_category))

        items.append(MenuItem("0", "Назад", lambda u: "break"))

        menu = Menu("Меню Категории", items)
        self._run_menu(menu, user)

    def show_all(self, _):
        categories = self.controller.get_all()
        if not categories:
            print("\nНяма категории.")
            return

        print("\nКатегории:")

        def print_tree(parent_id=None, level=0):
            children = [c for c in categories if c.parent_id == parent_id]
            children.sort(key=lambda x: x.name.lower())

            for child in children:
                indent = "  " * level
                prefix = "•" if level == 0 else "└─"
                print(f"{indent}{prefix} {child.name} ({child.category_id[:8]})")
                print_tree(child.category_id, level + 1)

        print_tree()
        input("\nEnter за продължение...")

    def add_category(self, user):
        print("\nНова категория")
        print("(Напишете 'отказ' за изход)")

        name = self._ask_required_string("Име: ", 2)
        if name == "cancel":
            return

        description = self._ask_required_string("Описание: ", 3)
        if description == "cancel":
            return

        print("\nИзберете родителска категория (Enter за главна):")
        parent = self.select_category()
        parent_id = parent.category_id if parent else None

        try:
            self.controller.add({"name": name, "description": description, "parent_id": parent_id}, user_id=user.user_id)
            print(f"\nКатегорията '{name}' е добавена.")
        except Exception as e:
            print(f"Неуспешен запис: {e}")

    def edit_category(self, user):
        print("\nРедактиране")
        category = self.select_category()
        if not category:
            return

        print(f"\nРедакция на: {category.name}")
        print("(Enter запазва старата стойност, 'отказ' за изход)")

        while True:
            new_name = input(f"Ново име [{category.name}]: ").strip()
            if new_name.lower() == "отказ":
                return
            if not new_name:
                new_name = category.name
                break
            if len(new_name) < 2:
                print("Името е твърде кратко.")
                continue
            break

        while True:
            new_desc = input(f"Ново описание [{category.description}]: ").strip()
            if new_desc.lower() == "отказ":
                return
            if not new_desc:
                new_desc = category.description
                break
            if len(new_desc) < 3:
                print("Описанието е твърде кратко.")
                continue
            break

        print("\nИзберете нов родител (Enter за без промяна):")
        parent = self.select_category()

        try:
            self.controller.update_name(category.category_id, new_name, user.user_id)
            self.controller.update_description(category.category_id, new_desc, user.user_id)

            if parent:
                self.controller.update_parent(category.category_id, parent.category_id, user.user_id)

            print("\nПромените са запазени.")
        except Exception as e:
            print(f"Неуспешен запис: {e}")

    def select_category(self):
        categories = sorted(self.controller.get_all(), key=lambda x: x.name.lower())
        if not categories:
            return None

        while True:
            print("\nСписък категории:")
            for i, cat in enumerate(categories, 1):
                print(f"{i}. {cat.name} ({cat.category_id[:8]})")

            choice = input("\nИзбор (номер или ID, Enter за отказ): ").strip()
            if not choice or choice.lower() == "отказ":
                return None

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    return categories[idx]

            found = self.controller.get_by_id(choice)
            if found:
                return found

            print("Невалиден избор. Опитайте пак.")

    def delete_category(self, user):
        print("\nИзтриване")
        category = self.select_category()
        if not category:
            return

        print(f"Продуктите в '{category.name}' ще останат без категория.")
        confirm = input(f"Искате ли да изтрием '{category.name}'? (y/n): ").strip().lower()
        if confirm == "y":
            try:
                self.controller.remove(category.category_id, user.user_id)
                print(f"\nКатегорията '{category.name}' е изтрита.")
            except Exception as e:
                print(f"Неуспешно изтриване: {e}")
        else:
            print("Операцията е прекратена.")
