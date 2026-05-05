from views.menu import Menu, MenuItem
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from controllers.location_controller import LocationController
from models.user import User
from views.product_sort_view import ProductSortView
from views.password_utils import require_password, format_table
from validators.product_validator import ProductValidator
from textwrap import wrap
from analytics.product_analytics import (calculate_average_price, calculate_total_inventory_value,
                                         get_most_expensive_product, get_cheapest_product, group_products_by_category)


def _wrap(text, width=45):
    return "\n".join(wrap(text, width=width))


class ProductMenuView:
    def __init__(self, product_controller: ProductController, category_controller: CategoryController,
                 location_controller: LocationController, inventory_controller, supplier_controller=None, activity_log_controller=None):

        self.product_controller = product_controller
        self.category_controller = category_controller
        self.location_controller = location_controller
        self.inventory_controller = inventory_controller
        self.supplier_controller = supplier_controller
        self.activity_log = activity_log_controller
        self.sort_view = ProductSortView(product_controller, inventory_controller)

    @staticmethod
    def format_lv(value):
        return f"{value:.2f} лв."

    def _build_menu(self):
        return Menu("МЕНЮ ПРОДУКТИ", [
            MenuItem("1", "Създаване на продукт", self.create_product),
            MenuItem("2", "Премахване на продукт", self.remove_product),
            MenuItem("3", "Редактиране на продукт", self.edit_product),
            MenuItem("4", "Покажи всички продукти", self.show_all_protected if self._is_operator() else self.show_all),
            MenuItem("5", "Търсене", self.search),
            MenuItem("6", "Сортиране на продукти", self.sort_menu_protected if self._is_operator() else self.sort_menu),
            MenuItem("7", "Средна цена", self.average_price),
            MenuItem("8", "Филтриране по категория", self.filter_by_category),
            MenuItem("9", "Критични наличности / Зареждане", self.low_stock),
            MenuItem("10", "Най-скъп продукт", self.most_expensive),
            MenuItem("11", "Най-евтин продукт", self.cheapest),
            MenuItem("12", "Обща стойност на склада", self.total_value),
            MenuItem("13", "Групиране по категории", self.group_by_category),
            MenuItem("14", "Разширено търсене", self.advanced_search),
            MenuItem("15", "Наличности по складове", self.show_stock_by_warehouses),
            MenuItem("0", "Назад", lambda u: "break")])

    @staticmethod
    def _is_operator():
        return False

    def show_menu(self, user: User):
        while True:
            menu = self._build_menu()
            choice = menu.show()
            if choice == "0":
                break
            menu.execute(choice, user)

    def create_product(self, user):
        print("\n  Създаване на продукт  ")
        while True:
            name = input("Име: ").strip()
            try:
                ProductValidator.validate_name(name)
                break
            except ValueError as e:
                print(f"[!] {e}")

        while True:
            description = input("Описание: ").strip()
            try:
                ProductValidator.validate_description(description)
                break
            except ValueError as e:
                print(f"[!] {e}")

        while True:
            price_raw = input("Цена: ").strip()
            try:
                price = ProductValidator.parse_float(price_raw, "Цена")
                break
            except ValueError as e:
                print(f"[!] {e}")

        while True:
            quantity_raw = input("Начално количество: ").strip()
            try:
                quantity = ProductValidator.parse_float(quantity_raw, "Количество")
                break
            except ValueError as e:
                print(f"[!] {e}")

        while True:
            unit = input("Мерна единица (кг, кг., kg, килограм / бр, бр., брой / л, l, литър / пакет, paket, packet): ").strip()
            try:
                ProductValidator.validate_unit(unit)
                break
            except ValueError as e:
                print(f"[!] {e}")

        categories = self.category_controller.get_all()
        print("\nКатегории:")
        for i, c in enumerate(categories):
            print(f"{i}. {c.name}")

        cat_raw = input("Изберете категория (номер): ").strip()
        category_id = categories[int(cat_raw)].category_id if cat_raw.isdigit() and int(cat_raw) < len(categories) else None

        locations = self.location_controller.get_all()
        print("\nЛокации:")
        for i, loc in enumerate(locations, start=1):
            print(f"{i}. {loc.name}")

        loc_raw = input("Изберете локация (номер): ").strip()
        location_id = locations[int(loc_raw) - 1].location_id if loc_raw.isdigit() and 0 < int(loc_raw) <= len(locations) else None

        supplier_id = None
        if self.supplier_controller:
            suppliers = self.supplier_controller.get_all()
            print("\nДоставчици:")
            for i, s in enumerate(suppliers):
                print(f"{i}. {s.name} (ID: {s.supplier_id})")

            supp_raw = input("Изберете доставчик (номер или Enter за пропуск): ").strip()
            if supp_raw.isdigit() and int(supp_raw) < len(suppliers):
                supplier_id = suppliers[int(supp_raw)].supplier_id

        try:
            product_data = {"name": name, "category_ids": [category_id] if category_id else [],
                             "quantity": quantity, "unit": unit,
                             "description": description, "price": price, "supplier_id": supplier_id,
                             "location_id": location_id}

            product_data["inventory_controller"] = self.inventory_controller

            self.product_controller.add(product_data, user.user_id)
            print("Продуктът е създаден успешно.")

        except Exception as e:
            print(f"Грешка: {e}")

    def remove_product(self, user):
        print("\n  Премахване на продукт  ")
        pid = input("ID на продукт: ").strip()
        if not pid:
            return
        product = self.product_controller.get_by_id(pid)
        if not product:
            print(f"[!] Продукт с ID {pid} не съществува.")
            return
        confirm = input(f"Сигурни ли сте, че искате да изтриете '{product.name}'? (y/n): ").strip().lower()
        if confirm != "y":
            print("Операцията е отказана.")
            return
        try:
            self.product_controller.delete_by_id(pid, user.user_id)
            print(f"[+] Продуктът '{product.name}' беше премахнат успешно.")
        except Exception as e:
            print(f"[!] Грешка при премахване: {e}")

    def edit_product(self, user):
        print("\n  Редактиране на продукт  ")
        pid = input("Въведете ID на продукт: ").strip()
        product = self.product_controller.get_by_id(pid)
        if not product:
            print(f"[!] Продукт с ID {pid} не съществува.")
            return

        new_name = input(f"Ново име ({product.name}) [Enter за запазване]: ").strip() or None
        new_description = input(f"Ново описание ({product.description or 'няма'}) [Enter за запазване]: ").strip() or None

        new_price = None
        while True:
            new_price_raw = input(f"Нова цена ({product.price}) [Enter за запазване]: ").strip()
            if new_price_raw == "":
                new_price = None
                break
            try:
                new_price = ProductValidator.parse_float(new_price_raw, "Цена")
                break
            except ValueError as e:
                print(f"[!] {e}")

        new_supplier_id = product.supplier_id
        if self.supplier_controller:
            print("\nСмяна на доставчик:")
            suppliers = self.supplier_controller.get_all()
            for i, s in enumerate(suppliers):
                print(f"{i}. {s.name}")

            supp_raw = input(f"Изберете номер на доставчик (Текущ: {product.supplier_id or 'няма'}) [Enter за запазване]: ").strip()
            if supp_raw.isdigit() and int(supp_raw) < len(suppliers):
                new_supplier_id = suppliers[int(supp_raw)].supplier_id

        try:
            success = self.product_controller.update_product(
                product_id=pid,
                new_name=new_name,
                new_description=new_description,
                new_price=new_price,
                new_supplier_id=new_supplier_id,
                user_id=user.user_id
            )

            if success:
                print(f"\n[+] Продуктът '{product.name}' беше обновен успешно!")
            else:
                print("\n[!] Нещо се обърка при обновяването.")

        except Exception as e:
            print(f"\n[!] Критична грешка при редактиране: {e}")

    def show_all(self, _):
        products = self.product_controller.get_all()
        if not products:
            print("Няма продукти.")
            return

        rows = []
        for p in products:
            qty = self.inventory_controller.get_total_stock(p.product_id)
            rows.append([p.product_id, p.name, f"{qty:.2f} {p.unit}", self.format_lv(p.price)])

        print(format_table(["ID", "Име", "Наличност", "Цена"], rows))

    @require_password("parola123")
    def show_all_protected(self, user):
        return self.show_all(user)

    def search(self, _):
        keyword = input("Търсене: ").strip()
        results = self.product_controller.search(keyword)
        for p in results:
            print(f"{p.name} | {self.inventory_controller.get_total_stock(p.product_id)} {p.unit}")

    def sort_menu(self, _):
        self.sort_view.show_menu()

    @require_password("parola123")
    def sort_menu_protected(self, user):
        return self.sort_menu(user)

    def average_price(self, _):
        avg = calculate_average_price(self.product_controller.get_all())
        print(f"Средна цена: {self.format_lv(avg)}")

    def filter_by_category(self, _):
        categories = self.category_controller.get_all()
        print("\nКатегории:")
        for i, c in enumerate(categories):
            print(f"{i}. {c.name} (ID: {c.category_id})")

        raw = input("Категория (номер или ID): ").strip()
        if not raw:
            return

        if raw.isdigit():
            idx = int(raw)
            if 0 <= idx < len(categories):
                category_id = categories[idx].category_id
            else:
                print("[!] Невалиден номер на категория.")
                return
        else:
            category_id = raw

        results = self.product_controller.filter_by_category(category_id)

        if not results:
            print("Няма продукти в тази категория.")
            return

        for p in results:
            qty = self.inventory_controller.get_total_stock(p.product_id)
            print(f"{p.name} | {qty} {p.unit}")

    def low_stock(self, _):
        threshold = float(input("Граница (Enter за 5): ") or 5.0)
        products = self.product_controller.get_all()
        low = []

        for p in products:
            qty = self.inventory_controller.get_total_stock(p.product_id)
            if qty < threshold:
                low.append(p)

        rows = []
        for p in low:
            qty = self.inventory_controller.get_total_stock(p.product_id)
            rows.append([p.name, f"{qty:.2f}", p.unit])

        print(format_table(["ПРОДУКТ", "НАЛИЧНОСТ", "МЯРКА"], rows))

    def most_expensive(self, _):
        p = get_most_expensive_product(self.product_controller.get_all())
        if p:
            print(f"Най-скъп: {p.name} - {self.format_lv(p.price)}")

    def cheapest(self, _):
        p = get_cheapest_product(self.product_controller.get_all())
        if p:
            print(f"Най-евтин: {p.name} - {self.format_lv(p.price)}")

    def total_value(self, _):
        m_controller = self.inventory_controller.movement_controller
        if not m_controller:
            print("[!] Грешка: Системата не може да зареди движенията за изчисление.")
            return

        total = self.inventory_controller.get_total_inventory_value_fifo(m_controller)

        print(f"\nОбща стойност на склада (по средна закупна цена):")
        print(f"--------------------------------------------------")
        print(f"Общо: {self.format_lv(total)}")
        print(f"--------------------------------------------------")
        input("\nНатиснете Enter за продължение...")

    def group_by_category(self, _):
        grouped = group_products_by_category(self.product_controller.get_all())

        for cat, items in grouped.items():
            print(f"\n--- {cat} ---")
            for p in items:
                qty = self.inventory_controller.get_total_stock(p.product_id)
                print(f"{p.name} | {qty} {p.unit}")

    def advanced_search(self, _):
        print("\n  Разширено търсене  ")
        keyword = input("Ключово слово (Enter за пропуск): ").strip() or None

        raw_min = input("Мин. цена: ").strip()
        try:
            min_price = ProductValidator.parse_optional_float(raw_min)
        except ValueError as e:
            print(f"[!] {e} → игнорирам мин. цена.")
            min_price = None

        raw_max = input("Макс. цена: ").strip()
        try:
            max_price = ProductValidator.parse_optional_float(raw_max)
        except ValueError as e:
            print(f"[!] {e} → игнорирам макс. цена.")
            max_price = None

        print("\nКатегории:")
        categories = self.category_controller.get_all()
        for i, c in enumerate(categories):
            print(f"{i}. {c.name}")

        cat_raw = input("Категория (Номер или ID, Enter за пропуск): ").strip()
        category_id = None

        if cat_raw:
            if cat_raw.isdigit() and int(cat_raw) < len(categories):
                category_id = categories[int(cat_raw)].category_id
            else:
                category_id = cat_raw

        print("\nЛокации:")
        locations = self.location_controller.get_all()
        for i, loc in enumerate(locations):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")

        loc_raw = input("Локация (Номер или ID, Enter за пропуск): ").strip()
        location_id = None

        if loc_raw:
            if loc_raw.isdigit() and int(loc_raw) < len(locations):
                location_id = locations[int(loc_raw)].location_id
            else:
                location_id = loc_raw

        results = self.product_controller.search_combined(
            keyword=keyword,
            min_price=min_price,
            max_price=max_price,
            category_id=category_id,
            location_id=location_id,
            inventory_controller=self.inventory_controller
        )

        if not results:
            print("\n[!] Няма резултати.\n")
            return

        rows = []
        for p in results:
            stock = self.inventory_controller.get_total_stock(p.product_id)

            if p.supplier_id and self.supplier_controller:
                supplier_obj = self.supplier_controller.get_by_id(p.supplier_id)
                supplier_name = supplier_obj.name if supplier_obj else p.supplier_id
            else:
                supplier_name = "—"

            supplier_name = supplier_name.replace('"', '')

            inv = self.inventory_controller.data["products"].get(p.product_id, {})
            loc_data = inv.get("locations", {})
            warehouse_lines = []

            for lid, q in loc_data.items():
                if float(q) > 0:
                    loc_obj = self.location_controller.get_by_id(lid)
                    loc_name = loc_obj.name if loc_obj else lid
                    warehouse_lines.append(f"{loc_name} ({q} {p.unit})")

            if not warehouse_lines:
                warehouse_lines = ["—"]

            rows.append([
                p.name,
                f"{p.price:.2f} лв.",
                f"{stock} {p.unit}",
                ", ".join([c.name for c in p.categories]) if p.categories else "-",
                warehouse_lines[0],
                supplier_name
            ])

            for line in warehouse_lines[1:]:
                rows.append(["", "", "", "", line, ""])

        print(f"\nНамерени резултати ({len(results)}):")
        headers = ["Продукт", "Цена", "Наличност", "Категории", "Локации", "Доставчик"]
        print(format_table(headers, rows))

    def show_stock_by_warehouses(self, _):
        products = self.product_controller.get_all()
        if not products:
            print("Няма продукти.")
            return

        all_locations = self.location_controller.get_all()

        for p in products:
            print(f"\n   {p.name}\n")
            inv_entry = self.inventory_controller.data.get("products", {}).get(p.product_id, {})
            product_locations = inv_entry.get("locations", {})

            rows = []
            total = 0.0

            for loc in all_locations:
                wh_id = loc.location_id
                qty = float(product_locations.get(wh_id, 0))
                if qty > 0:
                    display_qty = f"{qty} {p.unit}"
                else:
                    display_qty = f"0 {p.unit} (няма движение)"

                rows.append([loc.name, display_qty])
                total += qty

            print(format_table(["Склад", "Наличност"], rows))
            print(f"\n  Общо: {total:.1f} {p.unit}\n")
