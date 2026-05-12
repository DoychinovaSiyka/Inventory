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
        items = [MenuItem("1", "Списък с категории", self.show_all)]
        if is_admin:
            items.extend([
                MenuItem("2", "Добавяне на категория", self.add_category),
                MenuItem("3", "Редактиране на категория", self.edit_category),
                MenuItem("4", "Изтриване на категория", self.delete_category)])
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



    def add_category(self, user):
        print("\nНова категория (Enter за отказ)")
        while True:
            name = input("Име на категория: ").strip()
            if not name:
                print("Името е задължително.")
                continue
            if len(name) < 2:
                print("Името трябва да е поне 2 символа.")
                continue

            error = self.controller.validate_field("name", name)
            if error:
                print(f"Грешка: {error}")
                continue


            duplicate = False
            for c in self.controller.get_all():
                if c.name.lower() == name.lower():
                    duplicate = True
                    break

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
            new_cat = self.controller.add({"name": name, "description": description, "parent_id": parent_id}, user_id=user.user_id)
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
            if len(new_name) < 2:
                print("Името трябва да е поне 2 символа.")
                continue

            error = self.controller.validate_field("name", new_name)
            if error:
                print(f"Грешка: {error}")
                continue

            duplicate = False
            for c in self.controller.get_all():
                if c.category_id != category.category_id:
                    if c.name.lower() == new_name.lower():
                        duplicate = True
                        break

            if duplicate:
                print(f"Името '{new_name}' вече се използва.")
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
            print("Категорията е изтрита успешно.")
        except Exception as e:
            print(f"Грешка при изтриване: {e}")
