from views.menu import Menu, MenuItem


class CategoryView:

    def __init__(self, controller, product_controller):
        self.controller = controller
        self.product_controller = product_controller

    def show_menu(self, user):
        while True:
            is_admin = (user and user.role == "Admin")
            menu = self._build_menu(is_admin)
            choice = menu.show()
            if menu.execute(choice, user) == "break":
                break

    def _build_menu(self, is_admin):
        # Добавяме Търсене като точка 2
        items = [
            MenuItem("1", "Списък с категории", self.show_all),
            MenuItem("2", "Търсене на категория", self.search_category)
        ]

        if is_admin:
            items.extend([
                MenuItem("3", "Добавяне на категория", self.add_category),
                MenuItem("4", "Редактиране на категория", self.edit_category),
                MenuItem("5", "Изтриване на категория", self.delete_category)])

        items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Управление на категории", items)

    def show_all(self, _):
        visual_tree = self.controller.get_visual_tree()
        if not visual_tree:
            print("\nНяма дефинирани категории.")
            return

        print("\nЙЕРАРХИЯ НА КАТЕГОРИИТЕ")
        main_counter = 0

        for item in visual_tree:
            cat = item["category"]
            level = item["level"]
            short_id = str(cat.category_id)[:8]

            if level == 0:
                main_counter += 1
                print(f"\n{main_counter}. {cat.name} ({short_id})")
            else:
                indent = "  " * level
                print(f"{indent}- {cat.name} ({short_id})")

    def search_category(self, _):
        """Търсене по име или по кратко/дълго ID."""
        print("\n--- ТЪРСЕНЕ НА КАТЕГОРИЯ ---")
        query = input("Въведете име или ID (кратко/пълно): ").strip().lower()

        if not query:
            return

        # Вземаме всички категории от контролера
        all_cats = self.controller.get_all()
        results = []

        for c in all_cats:
            full_id = str(c.category_id).lower()
            short_id = full_id[:8]
            cat_name = c.name.lower()

            # Логика: Търсим в името ИЛИ проверяваме дали query съвпада с началото на ID-то
            if query in cat_name or full_id.startswith(query):
                results.append(c)

        if not results:
            print(f"\nНе бяха намерени категории по критерий: '{query}'")
            return

        print(f"\nНамерени резултати ({len(results)}):")
        print("-" * 30)
        for cat in results:
            parent = self.controller.get_by_id(cat.parent_id)
            parent_name = parent.name if parent else "ГЛАВНА"
            print(f"Име:      {cat.name}")
            print(f"ID:       {str(cat.category_id)[:8]}... (Пълно: {cat.category_id})")
            print(f"Родител:  {parent_name}")
            print(f"Описание: {cat.description}")
            print("-" * 30)

    def add_category(self, user):
        print("\nНова категория (Enter за отказ)")
        while True:
            name = input("Име на категория: ").strip()
            if not name:
                return
            if len(name) < 2:
                print("Името трябва да е поне 2 символа.")
                continue

            error = self.controller.validate_field("name", name)
            if error:
                print(f"Грешка: {error}")
                continue

            duplicate = any(c.name.lower() == name.lower() for c in self.controller.get_all())
            if duplicate:
                print(f"Категория с име '{name}' вече съществува.")
                continue
            break

        while True:
            description = input("Описание: ").strip()
            if not description:
                print("Описанието е задължително.")
                continue
            error = self.controller.validate_field("description", description)
            if error:
                print(f"Грешка: {error}")
                continue
            break

        print("\nИзберете родителска категория (Enter за ГЛАВНА):")
        parent = self.select_category()
        parent_id = parent.category_id if parent else None

        try:
            new_cat = self.controller.add({"name": name, "description": description, "parent_id": parent_id},
                                          user_id=user.user_id)
            print(f"\nКатегорията '{new_cat.name}' е добавена успешно.")
        except Exception as e:
            print(f"Грешка при запис: {e}")

    def edit_category(self, user):
        print("\nРедактиране на категория")
        category = self.select_category()
        if not category:
            return

        print(f"\nРедактиране на [{category.name}]. Оставете празно за запазване.")
        while True:
            new_name = input(f"Ново име [{category.name}]: ").strip()
            if not new_name:
                new_name = category.name
                break
            error = self.controller.validate_field("name", new_name)
            if error:
                print(f"Грешка: {error}")
                continue
            break

        while True:
            new_desc = input(f"Ново описание [{category.description}]: ").strip()
            if not new_desc:
                new_desc = category.description
                break
            error = self.controller.validate_field("description", new_desc)
            if error:
                print(f"Грешка: {error}")
                continue
            break

        print("\nИзберете нов родител (Enter за без промяна):")
        parent = self.select_category()
        new_parent_id = parent.category_id if parent else category.parent_id

        updates = {"name": new_name, "description": new_desc, "parent_id": new_parent_id}

        try:
            self.controller.update(category.category_id, updates)
            print("Промените са запазени успешно.")
        except Exception as e:
            print(f"Грешка при обновяване: {e}")

    def select_category(self):
        categories = sorted(self.controller.get_all(), key=lambda x: x.name.lower())
        if not categories:
            return None

        while True:
            print("\nНалични категории:")
            for i, cat in enumerate(categories, 1):
                print(f"{i}. {cat.name} ({str(cat.category_id)[:8]})")

            choice = input("\nИзбор (номер или ID, Enter за отказ): ").strip()
            if not choice:
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
        print("\nИзтриване на категория")
        category = self.select_category()
        if not category:
            return

        try:
            self.controller.remove(category.category_id, user.user_id, self.product_controller)
            print(f"Категорията '{category.name}' е изтрита успешно.")
        except ValueError as e:
            print(f"Грешка: {e}")
        except Exception as e:
            print(f"Неочаквана грешка: {e}")