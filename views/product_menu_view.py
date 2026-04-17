from views.menu import Menu, MenuItem
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from controllers.location_controller import LocationController
from models.user import User
from views.product_sort_view import ProductSortView
from views.password_utils import require_password
from views.password_utils import format_table
from validators.product_validator import ProductValidator


class ProductView:
    def __init__(self, product_controller: ProductController,
                 category_controller: CategoryController,
                 location_controller: LocationController,
                 activity_log_controller=None):

        self.product_controller = product_controller
        self.category_controller = category_controller
        self.location_controller = location_controller
        self.activity_log = activity_log_controller
        self.sort_view = ProductSortView(product_controller)
        self.menu = self._build_menu()

    @staticmethod
    def format_lv(value):
        return f"{value:.2f} лв."

    def _build_menu(self):
        return Menu("МЕНЮ ПРОДУКТИ", [
            MenuItem("1", "Създаване на продукт", self.create_product),
            MenuItem("2", "Премахване на продукт", self.remove_product),
            MenuItem("3", "Редактиране на продукт", self.edit_product),
            MenuItem("4", "Покажи всички продукти",
                     self.show_all_protected if self._is_operator() else self.show_all),
            MenuItem("5", "Търсене", self.search),
            MenuItem("6", "Сортиране на продукти",
                     self.sort_menu_protected if self._is_operator() else self.sort_menu),
            MenuItem("7", "Средна цена", self.average_price),
            MenuItem("8", "Филтриране по категория", self.filter_by_category),
            MenuItem("9", "Продукти с ниска наличност", self.low_stock),
            MenuItem("10", "Най-скъп продукт", self.most_expensive),
            MenuItem("11", "Най-евтин продукт", self.cheapest),
            MenuItem("12", "Обща стойност на склада", self.total_value),
            MenuItem("13", "Групиране по категории", self.group_by_category),
            MenuItem("14", "Разширено търсене", self.advanced_search),
            MenuItem("15", "Наличности по складове", self.show_stock_by_warehouses),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    @staticmethod
    def _is_operator():
        return False

    def show_menu(self, user: User):
        readonly = user.role in ["Operator", "Anonymous"]
        while True:
            choice = self.menu.show()
            if readonly and choice in ["1", "2", "3"]:
                print(f"[!] Функцията не е достъпна за роля: {user.role}")
                continue
            if self.menu.execute(choice, user) == "break":
                break


    # CRUD
    def create_product(self, user):
        print("\n  Създаване на продукт  ")
        name = input("Име: ").strip()
        description = input("Описание: ").strip()
        price_raw = input("Цена: ")
        quantity_raw = input("Начално количество (само за първоначално зареждане): ")
        unit = input("Мерна единица (пример: кг., бр., л., пакет): ").strip()

        try:
            price = ProductValidator.parse_float(price_raw, "Цена")
            quantity = ProductValidator.parse_float(quantity_raw, "Количество")
        except ValueError as e:
            print(e)
            print("Моля, опитайте отново.\n")
            return

        categories = self.category_controller.get_all()
        if not categories:
            print("Няма категории.")
            return

        print("\nКатегории:")
        for i, c in enumerate(categories):
            print(f"{i}. {c.name} (ID: {c.category_id})")

        cat_raw = input("Изберете категория (номер или Category ID): ").strip()

        try:
            if cat_raw.isdigit():
                cat_idx = ProductValidator.parse_int(cat_raw, "Категория")
                if cat_idx < 0 or cat_idx >= len(categories):
                    raise ValueError("Невалиден избор за Категория.")
                category_id = categories[cat_idx].category_id
            else:
                ProductValidator.validate_uuid(cat_raw, "Category ID")
                category_id = cat_raw
        except Exception as e:
            print(e)
            print("Моля, опитайте отново.\n")
            return

        locations = self.location_controller.get_all()
        if not locations:
            print("Няма складове.")
            return

        print("\nЛокации:")
        for i, loc in enumerate(locations):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")

        loc_raw = input("Изберете локация (номер или Location ID): ").strip()

        try:
            if loc_raw.isdigit():
                loc_idx = ProductValidator.parse_int(loc_raw, "Локация")
                if loc_idx < 0 or loc_idx >= len(locations):
                    raise ValueError("Невалиден избор за Локация.")
                location_id = locations[loc_idx].location_id
            else:
                if not isinstance(loc_raw, str) or loc_raw.strip() == "":
                    raise ValueError("Невалиден Location ID.")
                location_id = loc_raw
        except Exception as e:
            print(e)
            print("Моля, опитайте отново.\n")
            return

        try:
            u_id = user.user_id
            product_data = {"name": name, "category_ids": [category_id],
                            "quantity": quantity, "unit": unit, "description": description,
                            "price": price, "supplier_id": None, "location_id": location_id}

            product = self.product_controller.add(product_data, u_id)
            print("Продуктът е създаден успешно.")

        except ValueError as e:
            print("Грешка:", e)
            print("Моля, опитайте отново.\n")

    def remove_product(self, user):
        pid = input("ID на продукт: ").strip()
        try:
            u_id = user.user_id
            self.product_controller.delete_by_id(pid, u_id)
            print("Продуктът е премахнат.")
        except ValueError as e:
            print("Грешка:", e)
            print("Моля, опитайте отново.\n")

    def edit_product(self, _):
        pid = input("ID на продукт: ").strip()
        product = self.product_controller.get_by_id(pid)
        if not product:
            print("Няма такъв продукт.")
            return

        print(f"Редактиране на {product.name}")
        new_name = input(f"Ново име ({product.name}): ").strip() or product.name
        new_desc = input(f"Ново описание ({product.description}): ").strip() or product.description
        new_price_raw = input(f"Нова цена ({product.price}): ").strip()

        try:
            new_price = ProductValidator.parse_float(new_price_raw, "Цена") if new_price_raw else product.price
            self.product_controller.update_product(pid, new_name, new_desc, new_price)
            print("Продуктът е обновен.")
        except ValueError as e:
            print("Грешка:", e)
            print("Моля, опитайте отново.\n")



    def show_all(self, _):
        products = self.product_controller.get_all()
        if not products:
            print("Няма продукти.")
            return

        columns = ["ID", "Име", "Наличност", "Цена"]
        rows = []

        inventory = self.product_controller.inventory_controller.data["products"]

        for p in products:
            inv_entry = inventory.get(p.product_id, None)

            if inv_entry:
                stock = inv_entry.get("total_stock", 0)
            else:
                stock = 0

            rows.append([
                p.product_id,
                p.name,
                f"{stock} {p.unit}",
                self.format_lv(p.price)
            ])

        print(format_table(columns, rows))

    @require_password("parola123")
    def show_all_protected(self, user):
        self.show_all(user)


    def search(self, _):
        keyword = input("Търсене: ").strip().lower()
        results = self.product_controller.search(keyword)
        if not results:
            print("Няма резултати.")
            return

        inventory = self.product_controller.inventory_controller.data["products"]

        for p in results:
            stock = inventory.get(p.product_id, {}).get("total_stock", 0)
            print(f"{p.product_id} | {p.name} | {stock} {p.unit} | {self.format_lv(p.price)}")


    def sort_menu(self, _):
        self.sort_view.show_menu()

    @require_password("parola123")
    def sort_menu_protected(self, user):
        self.sort_menu(user)


    # REPORTS
    def average_price(self, _):
        avg = self.product_controller.average_price()
        print(f"Средна цена: {self.format_lv(avg)}")

    def filter_by_category(self, _):
        categories = self.category_controller.get_all()
        if not categories:
            print("Няма категории.")
            return

        print("\nКатегории:")
        for i, c in enumerate(categories):
            print(f"{i}. {c.name} (ID: {c.category_id})")

        raw = input("Изберете категория (номер или Category ID): ").strip()

        try:
            if raw.isdigit():
                idx = ProductValidator.parse_int(raw, "Категория")
                if idx < 0 or idx >= len(categories):
                    raise ValueError("Невалиден избор за Категория.")
                selected_id = categories[idx].category_id
            else:
                ProductValidator.validate_uuid(raw, "Category ID")
                selected_id = raw
        except Exception as e:
            print(e)
            print("Моля, опитайте отново.\n")
            return

        results = self.product_controller.search_by_category(selected_id)
        if not results:
            print("Няма продукти.")
            return

        inventory = self.product_controller.inventory_controller.data["products"]

        for p in results:
            stock = inventory.get(p.product_id, {}).get("total_stock", 0)
            print(f"{p.name} | {stock} {p.unit}")

    def low_stock(self, _):
        low = self.product_controller.check_low_stock()
        if not low:
            print("Няма критични продукти.")
            return

        inventory = self.product_controller.inventory_controller.data["products"]

        for p in low:
            stock = inventory.get(p.product_id, {}).get("total_stock", 0)
            print(f"ВНИМАНИЕ: {p.name} ({stock} {p.unit})")

    def most_expensive(self, _):
        p = self.product_controller.most_expensive()
        if p:
            print(f"Най-скъп: {p.name} - {self.format_lv(p.price)}")

    def cheapest(self, _):
        p = self.product_controller.cheapest()
        if p:
            print(f"Най-евтин: {p.name} - {self.format_lv(p.price)}")

    def total_value(self, _):
        print(f"Обща стойност: {self.format_lv(self.product_controller.total_values())}")

    def group_by_category(self, user):
        products = self.product_controller.get_all()
        inventory = self.product_controller.inventory_controller.data["products"]

        grouped = {}
        for p in products:
            # ПОПРАВКА: Извличане на имената на категориите от списъка p.categories
            cat = ", ".join([c.name for c in p.categories]) if p.categories else "Без категория"
            grouped.setdefault(cat, []).append(p)

        for category, items in grouped.items():
            print(f"\n--- {category} ---")
            for p in items:
                # ПОПРАВКА: Използване на p.product_id вместо p.id за съвместимост с модела
                stock = inventory.get(p.product_id, {}).get("total_stock", 0)
                print(f"{p.name} | {stock} {p.unit} | {p.price:.2f} лв.")

    def advanced_search(self, _):
        print("\n  Разширено търсене  ")

        keyword = input("Ключова дума: ").strip() or None
        min_raw = input("Мин. цена: ").strip()
        max_raw = input("Макс. цена: ").strip()

        try:
            # Парсване на числа (или None)
            min_p = ProductValidator.parse_optional_float(min_raw)
            max_p = ProductValidator.parse_optional_float(max_raw)
            results = self.product_controller.search_combined(
                keyword=keyword,
                min_price=min_p,
                max_price=max_p
            )

            # --- Няма резултати ---
            if not results:
                print("\n[!] Няма намерени продукти по тези критерии.\n")
                return

            # --- Показване на резултатите ---
            print(f"\nНамерени резултати ({len(results)}):\n")

            inventory = self.product_controller.inventory_controller.data["products"]

            for p in results:
                stock = inventory.get(p.product_id, {}).get("total_stock", 0)
                price = f"{p.price:.2f} лв."
                print(f"{p.name} | Цена: {price} | Наличност: {stock} {p.unit}")

            print()

        except ValueError as e:
            print(f"\nГрешка: {e}")
            print("Моля, опитайте отново.\n")

    # НАЛИЧНОСТИ ПО СКЛАДОВЕ
    def show_stock_by_warehouses(self, _):
        products = self.product_controller.get_all()
        if not products:
            print("Няма продукти.")
            return

        inventory = self.product_controller.inventory_controller.data["products"]

        for p in products:
            print(f"\n   {p.name}   ")

            inv_entry = inventory.get(p.product_id, None)

            if not inv_entry:
                print("  Няма наличности в нито един склад.")
                continue

            rows = []
            total = inv_entry.get("total_stock", 0)

            for wh, qty in inv_entry.get("locations", {}).items():
                rows.append([wh, f"{qty} {p.unit}"])

            print(format_table(["Склад", "Наличност"], rows))
            print(f"  Общо: {total} {p.unit}")