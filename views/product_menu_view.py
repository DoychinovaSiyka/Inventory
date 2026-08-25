from views.menu import Menu, MenuItem
from views.password_utils import format_table

from controllers.product_sort_controller import ProductSortController
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController




class ProductMenuView:
    def __init__(self, product_controller: ProductController, category_controller: CategoryController):
        self.product_controller = product_controller
        self.category_controller = category_controller
        self.sort_controller = ProductSortController(product_controller)

        self.allowed_units = ["кг.", "бр.", "л.", "пакет"]



    def _sort_menu(self, _):
        print("\nСОРТИРАНЕ НА ПРОДУКТИ")
        print("1. По име (A–Z)")
        print("2. По име (Z–A)")
        print("3. По цена (висока - ниска)")
        print("4. По цена (ниска - висока)")
        choice = input("Избор: ").strip()

        if choice == "1":
            products = self.sort_controller.sort_by_name_asc()
            self._print_products(products, "Име (A–Z)")

        elif choice == "2":
            products = self.sort_controller.sort_by_name_desc()
            self._print_products(products, "Име (Z–A)")

        elif choice == "3":
            products = self.sort_controller.sort_price_desc()
            self._print_products(products, "Цена (висока - ниска)")

        elif choice == "4":
            products = self.sort_controller.sort_price_asc()
            self._print_products(products, "Цена (ниска - висока)")





    def show_menu(self, user):
        menu = Menu("Каталог на продуктите", [
            MenuItem("1", "Създаване на продукт", self.create_product),
            MenuItem("2", "Редактиране на продукт", self.edit_product),
            MenuItem("3", "Премахване на продукт", self.remove_product),
            MenuItem("4", "Всички продукти", self.show_all),
            MenuItem("5", "Търсене по име", self.search),
            MenuItem("6", "Филтър по категория", self.filter_by_category),
            MenuItem("7", "Сортиране", self._sort_menu),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)



    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice in ("0", None):
                break
            if menu_obj.execute(choice, user) == "break":
                break




    def _print_products(self, products, title=""):
        if not products:
            print("\nНяма намерени продукти.\n")
            return

        rows = []
        for p in products:
            short_id = str(p.product_id)[:8]
            price_text = f"{float(p.price):.2f}"
            rows.append([short_id, p.name[:30], price_text])

        if title:
            print(f"\n{title.upper()}")

        print(format_table(["ID", "Име", "Цена (лв.)"], rows))




    def create_product(self, user):
        print("\nНОВ ПРОДУКТ")
        while True:
            name = input("Име на продукт: ").strip()
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

        product_data = {"name": name, "description": desc, "price": price_raw, "unit": unit_raw, "category_ids": [category_id]}

        try:
            new_product = self.product_controller.add(product_data)
            print(f"\nПродуктът '{new_product.name}' е добавен успешно.")
        except Exception as e:
            print(f"\nГрешка при запис: {e}")




    def edit_product(self, user):
        print("\nРЕДАКТИРАНЕ НА ПРОДУКТ")
        pid = input("ID на продукт: ").strip()
        product = self.product_controller.get_by_id(pid)

        if not product:
            print("Продукт с такова ID не беше намерен.")
            return

        print(f"\nРедактирате продукт: {product.name}")

        while True:
            new_name = input(f"Ново име [{product.name}]: ").strip()
            if not new_name:
                new_name = product.name
                break

            error = self.product_controller.validate_field("name", new_name, exclude_id=product.product_id)
            if error:
                print(f"Грешка: {error}")
                continue
            break

        while True:
            price_raw = input(f"Нова цена [{product.price:.2f} лв.]: ").strip()
            if not price_raw:
                new_price = product.price
                break

            error = self.product_controller.validate_field("price", price_raw)
            if error:
                print(f"Грешка: {error}")
                continue
            new_price = price_raw
            break

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

        new_unit = product.unit
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

        print("\nПромяна на категория: ")
        new_cat_id = self._select_category()
        if new_cat_id:
            new_category_ids = [new_cat_id]
        else:
            new_category_ids = [str(c.category_id) for c in product.categories]


        updates = {"name": new_name, "price": new_price, "description": new_desc,
                   "unit": new_unit, "category_ids": new_category_ids}


        try:
            if self.product_controller.update(product.product_id, updates):
                print(f"\nПродуктът '{new_name}' беше обновен.")
            else:
                print("\nПродуктът не можа да бъде обновен.")
        except Exception as e:
            print(f"\nГрешка при обновяване: {e}")




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

        sub_ids = self.category_controller.get_all_hierarchical_ids(category_id)
        all_ids = [category_id] + sub_ids

        parent = self.category_controller.get_by_id(category_id)
        print(f"\nФИЛТЪР ПО КАТЕГОРИЯ: {parent.name}")
        print("\nПодкатегории:")
        if not sub_ids:
            print(" (няма подкатегории)")
        else:
            for cid in sub_ids:
                cat = self.category_controller.get_by_id(cid)
                if cat:
                    print(f" - {cat.name}")

        results = self.product_controller.filter_by_category_hierarchy(all_ids)

        print("\nНамерени продукти:")
        self._print_products(results)
