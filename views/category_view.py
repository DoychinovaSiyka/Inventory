from views.menu import Menu, MenuItem


class CategoryView:

    def __init__(self, controller, product_controller):
        self.controller = controller
        self.product_controller = product_controller

    def _ask_required_string(self, prompt, min_len=2):
        while True:
            value = input(prompt).strip()
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
            if menu_obj.execute(choice, user) == "break":
                break

    def show_menu(self, user):
        is_admin = (user is not None and user.role == "Admin")
        items = [MenuItem("1", "Списък с категории", self.show_all)]

        if is_admin:
            items.append(MenuItem("2", "Добавяне на категория", self.add_category))
            items.append(MenuItem("3", "Редактиране на категория", self.edit_category))
            items.append(MenuItem("4", "Изтриване", lambda u: self.delete_category(u)))

        items.append(MenuItem("0", "Назад", lambda u: "break"))
        menu = Menu("Меню Категории", items)
        self._run_menu(menu, user)

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
        print("\nНОВА КАТЕГОРИЯ")
        while True:
            name = self._ask_required_string("Име: ", 2)

            all_cats = self.controller.get_all()
            duplicate = False
            for c in all_cats:
                if c.name.lower() == name.lower():
                    duplicate = True
                    break

            if duplicate:
                print("Категория с такова име вече съществува.")
                continue

            break


        description = self._ask_required_string("Описание: ", 3)

        print("\nИзберете родителска категория (Enter за ГЛАВНА категория):")
        parent = self.select_category()
        parent_id = parent.category_id if parent else None

        try:
            self.controller.add({"name": name, "description": description, "parent_id": parent_id}, user_id=user.user_id)
            print(f"\nКатегорията '{name}' е добавена успешно.")
        except Exception as e:
            print(f"\nГрешка при добавяне: {e}")



    def edit_category(self, user):
        print("\nРЕДАКТИРАНЕ НА КАТЕГОРИЯ")
        category = self.select_category()
        if not category:
            return

        print(f"\nРедакция на: {category.name} (Оставете празно за запазване)")


        while True:
            new_name = input(f"Ново име [{category.name}]: ").strip()
            if not new_name:
                new_name = category.name
                break
            if len(new_name) < 2:
                print("Името трябва да е поне 2 символа.")
                continue

            all_cats = self.controller.get_all()
            duplicate = False
            for c in all_cats:
                if c.category_id != category.category_id:
                    if c.name.lower() == new_name.lower():
                        duplicate = True
                        break

            if duplicate:
                print("Категория с такова име вече съществува.")
                continue

            break


        while True:
            new_desc = input(f"Ново описание [{category.description}]: ").strip()
            if not new_desc:
                new_desc = category.description
                break
            if len(new_desc) < 3:
                print("Описанието трябва да е поне 3 символа.")
                continue
            break


        print("\nИзберете нов родител")
        parent = self.select_category()
        new_parent_id = parent.category_id if parent else category.parent_id

        if parent and parent.category_id == category.category_id:
            print("Категория не може да бъде родител сама на себе си.")
            return


        current = parent
        while current:
            if current.category_id == category.category_id:
                print("Невалидна йерархия. Това ще създаде цикъл.")
                return
            current = self.controller.get_by_id(current.parent_id)

        try:
            updates = {"name": new_name, "description": new_desc, "parent_id": new_parent_id}
            if self.controller.update(category.category_id, updates):
                print("\nПромените са запазени успешно.")
            else:
                print("\nКатегорията не беше намерена.")

        except Exception as e:
            print(f"\nНеуспешен запис: {e}")


    def select_category(self):
        categories = sorted(self.controller.get_all(), key=lambda x: x.name.lower())
        if not categories:
            return None

        while True:
            print("\nНалични категории:")
            for i, cat in enumerate(categories, 1):
                print(f"{i}. {cat.name} ({str(cat.category_id)[:8]})")

            choice = input("\nИзбор (номер или ID, Enter за отказ/главна): ").strip()
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
        print("\nИЗТРИВАНЕ НА КАТЕГОРИЯ")
        category = self.select_category()
        if not category:
            return

        try:
            if self.controller.remove(category.category_id, user.user_id, self.product_controller):
                print(f"\nКатегорията '{category.name}' е изтрита успешно.")
            else:
                print("\nКатегорията не беше намерена в базата.")
        except Exception as e:
            print(f"\nНеуспешно изтриване: {e}")
