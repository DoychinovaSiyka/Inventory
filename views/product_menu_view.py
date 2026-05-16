from views.menu import Menu, MenuItem
from views.password_utils import format_table
from views.product_sort_view import ProductSortView




class ProductMenuView:
    def __init__(self, product_controller, category_controller):
        self.product_controller = product_controller
        self.category_controller = category_controller

        self.allowed_units = ["кг.", "бр.", "л.", "пакет"]
        self.sort_view = ProductSortView(product_controller, self)

    def _print_products(self, products, title=""):
        if not products:
            print("\nНяма намерени продукти.\n")
            return

        rows = []
        for p in products:
            short_id = str(p.product_id)[:8]
            price_text = f"{float(p.price):.2f} лв."
            rows.append([short_id, p.name[:30], price_text])

        if title:
            print(f"\n{title.upper()}")

        print(format_table(["ID", "Име", "Цена"], rows))

    def _select_parent_category(self):
        all_categories = self.category_controller.get_all()
        categories = [c for c in all_categories if not c.parent_id]
        categories = sorted(categories, key=lambda x: x.name.lower())

        if not categories:
            print("\nНяма дефинирани главни категории.")
            return None

        while True:
            print("\nИЗБОР НА ГЛАВНА КАТЕГОРИЯ")
            for i, cat in enumerate(categories, start=1):
                sid = str(cat.category_id)[:8]
                print(f"{i}. {cat.name} ({sid})")

            choice = input("\nИзберете номер, име или съкратено ID (Enter за отказ): ").strip()
            if not choice:
                return None

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    return categories[idx].category_id

            for cat in categories:
                sid = str(cat.category_id)[:8]
                if choice.lower() == cat.name.lower() or choice.lower() == sid:
                    return cat.category_id

            print("Невалидна категория. Опитайте отново.")

    def _select_category(self):
        categories = sorted(self.category_controller.get_all(), key=lambda x: x.name.lower())
        if not categories:
            print("\nНяма дефинирани категории.")
            return None

        while True:
            print("\nИЗБОР НА КАТЕГОРИЯ")
            for i, cat in enumerate(categories, start=1):
                short_id = str(cat.category_id)[:8]
                print(f"{i}. {cat.name} ({short_id})")

            choice = input("\nИзберете номер, име или съкратено ID: ").strip()
            if not choice:
                return None
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    return categories[idx].category_id

            for cat in categories:
                short_id = str(cat.category_id)[:8]
                if choice.lower() == cat.name.lower() or choice.lower() == short_id:
                    return cat.category_id

            print("Невалидна категория. Опитайте отново.")

    def show_menu(self, user):
        menu = Menu("Каталог на продуктите", [
            MenuItem("1", "Създаване на продукт", self.create_product),
            MenuItem("2", "Редактиране на продукт", self.edit_product),
            MenuItem("3", "Премахване на продукт", self.remove_product),
            MenuItem("4", "Всички продукти", self.show_all),
            MenuItem("5", "Търсене по име", self.search),
            MenuItem("6", "Филтър по категория", self.filter_by_category),
            MenuItem("7", "Сортиране", lambda u: self.sort_view.show_menu()),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)

    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice in ("0", None):
                break
            if menu_obj.execute(choice, user) == "break":
                break

    def create_product(self, user):
        print("\nНОВ ПРОДУКТ")
        while True:
            name = input("Име на продукт: ").strip()
            # Контролерът вече проверява и за дължина, и за уникалност
            error = self.product_controller.validate_field("name", name)
            if error:
                print(f"Грешка: {error}")
                continue
            break

        while True:
            price_raw = input("Цена (напр. 2.50): ").strip()
            error = self.product_controller.validate_field("price", price_raw)
            if error:
                print(f"Грешка: {error}")
                continue
            break

        while True:
            desc = input("Описание: ").strip()
            error = self.product_controller.validate_field("description", desc)
            if error:
                print(f"Грешка: {error}")
                continue
            break

        # Избор на мерна единица
        unit_raw = "бр."
        while True:
            print("\nИзберете мерна единица:")
            for i, u in enumerate(self.allowed_units, start=1):
                print(f"{i}. {u}")
            unit_choice = input("Номер: ").strip()
            if unit_choice.isdigit():
                idx = int(unit_choice) - 1
                if 0 <= idx < len(self.allowed_units):
                    unit_raw = self.allowed_units[idx]
                    break
            print("Невалидна мерна единица.")

        category_id = self._select_category()
        if not category_id:
            print("Категорията е задължителна.")
            return

        product_data = {
            "name": name,
            "description": desc,
            "price": price_raw,
            "unit": unit_raw,
            "category_ids": [category_id]
        }

        try:
            new_product = self.product_controller.add(product_data)
            print(f"\nПродуктът '{new_product.name}' е добавен успешно.")
        except Exception as e:
            print(f"\nГрешка при запис: {e}")
    def edit_product(self, user):
        print("\nРЕДАКТИРАНЕ НА ПРОДУКТ")
        pid = input("ID на продукт (кратко или пълно): ").strip()
        product = self.product_controller.get_by_id(pid)

        if not product:
            print("Грешка: Продукт с такова ID не беше намерен.")
            return

        print(f"\nРедактирате продукт: {product.name}")
        print("Оставете полето празно (Enter), ако не искате промяна.")

        # 1. Име
        while True:
            new_name = input(f"Ново име [{product.name}]: ").strip()
            if not new_name:
                new_name = product.name
                break

            # Проверка чрез контролера (exclude_id е важно, за да не се кара със себе си)
            error = self.product_controller.validate_field("name", new_name, exclude_id=product.product_id)
            if error:
                print(f"Грешка: {error}")
                continue
            break

        # 2. Цена
        while True:
            price_raw = input(f"Нова цена [{product.price:.2f} лв.]: ").strip()
            if not price_raw:
                new_price = product.price
                break

            error = self.product_controller.validate_field("price", price_raw)
            if error:
                print(f"Грешка: {error}")
                continue
            new_price = price_raw  # Контролерът ще го парсне по-късно
            break

        # 3. Описание
        while True:
            new_desc = input(f"Ново описание [{product.description}]: ").strip()
            if not new_desc:
                new_desc = product.description
                break

            error = self.product_controller.validate_field("description", new_desc)
            if error:
                print(f"Грешка: {error}")
                continue
            break

        # 4. Мерна единица
        new_unit = product.unit  # По подразбиране е старата
        while True:
            print("\nИзберете мерна единица:")
            for i, u in enumerate(self.allowed_units, start=1):
                print(f"{i}. {u}")

            unit_choice = input(f"Избор на номер [{product.unit}]: ").strip()
            if not unit_choice:
                break

            if unit_choice.isdigit():
                idx = int(unit_choice) - 1
                if 0 <= idx < len(self.allowed_units):
                    new_unit = self.allowed_units[idx]
                    break

            print("Невалиден избор. Опитайте пак.")


        print("\nПромяна на категория (Enter за запазване на текущата):")
        new_cat_id = self._select_category()


        if new_cat_id:
            new_category_ids = [new_cat_id]
        else:
            new_category_ids = [str(c.category_id) for c in product.categories]


        updates = {
            "name": new_name,
            "price": new_price,
            "description": new_desc,
            "unit": new_unit,
            "category_ids": new_category_ids
        }

        # Изпълнение на редакцията
        try:
            if self.product_controller.update(product.product_id, updates):
                print(f"\nУспех: Продуктът '{new_name}' беше обновен.")
            else:
                print("\nГрешка: Продуктът не можа да бъде обновен.")
        except Exception as e:
            print(f"\nКритична грешка при обновяване: {e}")


    def remove_product(self, user):
        print("\nИЗТРИВАНЕ НА ПРОДУКТ")
        pid = input("ID на продукт: ").strip()
        product = self.product_controller.get_by_id(pid)
        if not product:
            print("Продуктът не е намерен.")
            return

        try:
            self.product_controller.delete_by_id(product.product_id)
            print("Продуктът е изтрит успешно.")
        except Exception as e:
            print("Грешка при изтриване:", e)


    def show_all(self, _):
        self._print_products(self.product_controller.get_all(), "Каталог на продуктите")



    def search(self, _):
        keyword = input("\nТърсене (име, описание или категория): ").strip()
        if keyword:
            results = self.product_controller.search(keyword)
            self._print_products(results, f"Резултати за '{keyword}'")


    def filter_by_category(self, _):
        category_id = self._select_parent_category()
        if not category_id:
            return

        all_ids = [category_id] + self.category_controller.get_all_hierarchical_ids(category_id)
        results = self.product_controller.filter_by_category_hierarchy(all_ids)
        self._print_products(results, "Резултати")
