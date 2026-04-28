from views.menu import Menu, MenuItem
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from controllers.location_controller import LocationController
from models.user import User
from views.product_sort_view import ProductSortView
from views.password_utils import require_password
from views.password_utils import format_table
from validators.product_validator import ProductValidator
from validators.movement_validator import MovementValidator


class ProductView:
    def __init__(self, product_controller: ProductController, category_controller: CategoryController,
                 location_controller: LocationController, activity_log_controller=None):

        self.product_controller = product_controller
        self.category_controller = category_controller
        self.location_controller = location_controller
        self.activity_log = activity_log_controller
        self.sort_view = ProductSortView(product_controller)

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
            MenuItem("9", "Критични наличности / Зареждане", self.low_stock),
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
        # Менюто се изгражда локално, за да отразява правата на текущия потребител
        menu = self._build_menu()
        readonly = user.role in ["Operator", "Anonymous"]
        while True:
            choice = menu.show()
            if readonly and choice in ["1", "2", "3"]:
                print(f"\n[!] Функцията не е достъпна за роля: {user.role}")
                continue
            if menu.execute(choice, user) == "break":
                break

    # CRUD
    def create_product(self, user):
        """ Създава нов продукт чрез въвеждане на име, описание, цена, количество,
        мерна единица, категория и начална локация. Валидира всички входни данни и записва продукта чрез ProductController."""
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
            quantity_raw = input("Начално количество (само за първоначално зареждане): ").strip()
            try:
                quantity = ProductValidator.parse_float(quantity_raw, "Количество")
                break
            except ValueError as e:
                print(f"[!] {e}")

        while True:
            unit = input("Мерна единица (пример: кг., бр., л., пакет): ").strip()
            try:
                ProductValidator.validate_unit(unit)
                break
            except ValueError as e:
                print(f"[!] {e}")

        categories = self.category_controller.get_all()
        if not categories:
            print("Няма категории.")
            return
        print("\nКатегории:")
        for i, c in enumerate(categories):
            print(f"{i}. {c.name} (ID: {c.category_id})")

        while True:
            cat_raw = input("Изберете категория (номер или Category ID, Enter за отказ): ").strip()
            if cat_raw == "":
                print("Операцията е отказана.")
                return
            try:
                if cat_raw.isdigit():
                    idx = int(cat_raw)
                    if idx < 0 or idx >= len(categories):
                        raise ValueError("Невалиден избор за Категория.")
                    category_id = categories[idx].category_id
                else:
                    ProductValidator.validate_uuid(cat_raw, "Category ID")
                    if not self.category_controller.get_by_id(cat_raw):
                        raise ValueError("Несъществуваща категория.")
                    category_id = cat_raw
                break
            except Exception as e:
                print(f"[!] {e}")

        locations = self.location_controller.get_all()
        if not locations:
            print("Няма складове.")
            return

        print("\nЛокации:")
        for i, loc in enumerate(locations):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")

        while True:
            loc_raw = input("Изберете локация (номер или Location ID, Enter за отказ): ").strip()
            if loc_raw == "":
                print("Операцията е отказана.")
                return
            try:
                # Използваме строгия валидатор -> нормализира към W1–Wn
                location_id = MovementValidator.validate_location_id(loc_raw, self.location_controller)
                break
            except Exception as e:
                print(f"[!] {e}")

        try:
            u_id = user.user_id
            product_data = {
                "name": name,
                "category_ids": [category_id],
                "quantity": quantity,
                "unit": unit,
                "description": description,
                "price": price,
                "supplier_id": None,
                "location_id": location_id
            }

            product = self.product_controller.add(product_data, u_id)
            print("Продуктът е създаден успешно.")

        except ValueError as e:
            print("Грешка:", e)
            print("Моля, опитайте отново.\n")

    def remove_product(self, user):
        print("\nПремахване на продукт")
        while True:
            pid = input("ID на продукт (Enter за отказ): ").strip()
            if pid == "":
                print("Операцията е отказана.")
                return

            product = self.product_controller.get_by_id(pid)
            if product:
                break
            print("Няма такъв продукт.")
            print("Моля, опитайте отново.\n")

        confirm = input(f"Сигурни ли сте, че искате да изтриете '{product.name}'? (Y/N): ").strip().lower()
        if confirm != "y":
            print("Операцията е отказана.")
            return
        self.product_controller.delete_by_id(product.product_id, user.user_id)
        print("Продуктът е премахнат.")

    def edit_product(self, user):
        """ Редактира съществуващ продукт: позволява промяна на име, описание, цена и категория.
        Количеството и локацията вече НЕ се редактират тук – те се сменят само чрез движения (IN/OUT/MOVE). """
        print("\nРедактиране на продукт")
        while True:
            pid = input("ID на продукт (Enter за отказ): ").strip()
            if pid == "":
                print("Операцията е отказана.")
                return

            product = self.product_controller.get_by_id(pid)
            if product:
                break
            print("Няма такъв продукт.")
            print("Моля, опитайте отново.\n")

        print(f"Редактиране на {product.name}")
        new_name = input(f"Ново име ({product.name}): ").strip() or product.name
        new_desc = input(f"Ново описание ({product.description}): ").strip() or product.description
        new_price_raw = input(f"Нова цена ({product.price}): ").strip()

        print("\nКатегории:")
        categories = self.category_controller.get_all()
        for i, c in enumerate(categories):
            print(f"{i}. {c.name} (ID: {c.category_id})")

        cat_raw = input("Нова категория (Enter за пропуск): ").strip()
        new_category_ids = None

        if cat_raw:
            try:
                if cat_raw.isdigit():
                    idx = int(cat_raw)
                    if idx < 0 or idx >= len(categories):
                        raise ValueError("Невалиден избор за Категория.")
                    new_category_ids = [categories[idx].category_id]
                else:
                    ProductValidator.validate_uuid(cat_raw, "Category ID")
                    if not self.category_controller.get_by_id(cat_raw):
                        raise ValueError("Несъществуваща категория.")
                    new_category_ids = [cat_raw]
            except Exception as e:
                print(f"[!] {e}")
                return

        try:
            new_price = ProductValidator.parse_float(new_price_raw, "Цена") if new_price_raw else product.price

            self.product_controller.update_product(
                product_id=pid,
                new_name=new_name,
                new_description=new_desc,
                new_price=new_price,
                new_quantity=None,
                new_unit=None,
                new_category_ids=new_category_ids,
                new_location_id=None,
                new_supplier_id=None,
                new_tags=None,
                user_id=user.user_id
            )

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

        for p in products:
            stock = self.product_controller.get_total_stock(p.product_id)
            rows.append([p.product_id, p.name, f"{stock:.2f} {p.unit}", self.format_lv(p.price)])

        print(format_table(columns, rows))

    @require_password("parola123")
    def show_all_protected(self, user):
        self.show_all(user)

    def search(self, _):
        keyword = input("Търсене (Enter за отказ): ").strip().lower()
        if keyword == "":
            print("Операцията е отказана.")
            return

        results = self.product_controller.search(keyword)
        if not results:
            print("Няма резултати.")
            return

        for p in results:
            stock = self.product_controller.get_total_stock(p.product_id)
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

        raw = input("Изберете категория (номер или Category ID, Enter за отказ): ").strip()
        if raw == "":
            print("Операцията е отказана.")
            return

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

        for p in results:
            stock = self.product_controller.get_total_stock(p.product_id)
            print(f"{p.name} | {stock} {p.unit}")

    def low_stock(self, _):
        print("   ПРОВЕРКА ЗА КРИТИЧНИ НАЛИЧНОСТИ")

        raw_threshold = input("Въведете критична граница (Enter за стандартно < 5): ").strip()
        if raw_threshold == "":
            threshold = 5.0
        else:
            try:
                threshold = float(raw_threshold)
            except ValueError:
                print("[!] Невалиден вход. Използвам граница по подразбиране: 5.0")
                threshold = 5.0

        low_products = self.product_controller.check_low_stock(threshold)

        if not low_products:
            print(
                f"\n Всичко е наред! Няма продукти под {threshold:.2f} {low_products[0].unit if low_products else ''}.")
            return

        print(f"\n[!] Намерени са {len(low_products)} продукта под лимита от {threshold:.2f}:")

        columns = ["ПРОДУКТ", "НАЛИЧНОСТ", "МЯРКА", "СТАТУС"]
        rows = []

        for p in low_products:
            stock = self.product_controller.get_total_stock(p.product_id)

            if stock == 0:
                status = " ИЗЧЕРПАН"
            elif stock <= (threshold * 0.3):
                status = " КРИТИЧНО"
            else:
                status = " НИСКО"

            rows.append([p.name, f"{stock:.2f}", p.unit, status])

        print(format_table(columns, rows))

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
        """ Филтрира продуктите по избрана категория. Позволява избор по номер или Category ID и показва наличностите."""
        products = self.product_controller.get_all()

        grouped = {}
        for p in products:
            cat = ", ".join([c.name for c in p.categories]) if p.categories else "Без категория"
            grouped.setdefault(cat, []).append(p)

        for category, items in grouped.items():
            print(f"\n--- {category} ---")
            for p in items:
                stock = self.product_controller.get_total_stock(p.product_id)
                print(f"{p.name} | {stock} {p.unit} | {p.price:.2f} лв.")

    def advanced_search(self, _):
        """ Извършва разширено търсене по множество критерии:
        ключова дума, цена, количество, категория, локация и доставчик. Валидира входните стойности и
        показва резултатите във формат таблица."""

        print("\n  Разширено търсене  ")
        keyword = input("Ключова дума (Enter за пропуск): ").strip()
        if keyword == "":
            keyword = None

        min_raw = input("Мин. цена (Enter за пропуск): ").strip()
        max_raw = input("Макс. цена (Enter за пропуск): ").strip()
        min_qty_raw = input("Мин. количество (Enter за пропуск): ").strip()
        max_qty_raw = input("Макс. количество (Enter за пропуск): ").strip()

        print("\nКатегории:")
        categories = self.category_controller.get_all()
        for i, c in enumerate(categories):
            print(f"{i}. {c.name} (ID: {c.category_id})")
        cat_raw = input("Категория (Enter за пропуск): ").strip()
        category_id = None
        if cat_raw:
            if cat_raw.isdigit():
                idx = int(cat_raw)
                if 0 <= idx < len(categories):
                    category_id = categories[idx].category_id
            else:
                category_id = cat_raw

        print("\nЛокации:")
        locations = self.location_controller.get_all()
        for i, loc in enumerate(locations):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")
        loc_raw = input("Локация (Enter за пропуск): ").strip()
        location_id = None
        if loc_raw:
            if loc_raw.isdigit():
                idx = int(loc_raw)
                if 0 <= idx < len(locations):
                    location_id = locations[idx].location_id
            else:
                location_id = loc_raw

        supplier_raw = input("Доставчик ID (Enter за пропуск): ").strip()
        supplier_id = supplier_raw if supplier_raw else None

        try:
            min_price = ProductValidator.parse_optional_float(min_raw)
            max_price = ProductValidator.parse_optional_float(max_raw)
            min_qty = ProductValidator.parse_optional_float(min_qty_raw)
            max_qty = ProductValidator.parse_optional_float(max_qty_raw)

            results = self.product_controller.search_combined(
                keyword=keyword,
                min_price=min_price,
                max_price=max_price,
                min_quantity=min_qty,
                max_quantity=max_qty,
                category_id=category_id,
                supplier_id=supplier_id,
                location_id=location_id
            )

            if not results:
                print("\n[!] Няма намерени продукти по тези критерии.\n")
                return

            print(f"\nНамерени резултати ({len(results)}):\n")

            rows = []

            for p in results:
                stock = self.product_controller.get_total_stock(p.product_id)

                # Доставчик
                supplier_name = "-"
                if p.supplier_id:
                    supplier = self.product_controller.supplier_controller.get_by_id(p.supplier_id)
                    if supplier:
                        supplier_name = supplier.name

                # Складове, в които продуктът има наличност
                warehouses = self.product_controller.inventory_controller.get_warehouses_with_product(p.name)
                warehouse_str = ", ".join(warehouses) if warehouses else "—"

                rows.append([
                    p.name,
                    f"{p.price:.2f} лв.",
                    f"{stock} {p.unit}",
                    ", ".join([c.name for c in p.categories]) if p.categories else "-",
                    warehouse_str,
                    supplier_name
                ])

            print(format_table(["Продукт", "Цена", "Наличност", "Категории", "Локации", "Доставчик"], rows))
            print()

        except ValueError as e:
            print(f"\nГрешка: {e}")
            print("Моля, опитайте отново.\n")

    def show_stock_by_warehouses(self, _):
        """ Показва наличностите на всеки продукт по всички складове. Извежда таблица с количества и
        обща наличност за продукта."""
        products = self.product_controller.get_all()
        if not products:
            print("Няма продукти.")
            return

        inventory = self.product_controller.inventory_controller.data["products"]
        all_locations = self.location_controller.get_all()

        for p in products:
            print(f"\n   {p.name}   ")

            inv_entry = inventory.get(p.product_id, None)
            if not inv_entry:
                print("  Няма наличности в нито един склад.")
                continue

            rows = []
            total = inv_entry.get("total_stock", 0)
            product_locations = inv_entry.get("locations", {})
            # Обхождаме ВСИЧКИ складове от системата
            for loc in all_locations:
                wh_id = loc.location_id
                # Количество в този склад
                qty = product_locations.get(wh_id, None)
                if qty is None:
                    # Продуктът никога не е бил тук
                    display_qty = f"0 {p.unit} (няма движение)"
                else:
                    if qty > 0:
                        display_qty = f"{qty} {p.unit}"
                    else:
                        display_qty = f"0 {p.unit} (изчерпан)"
                rows.append([wh_id, display_qty])

            print(format_table(["Склад", "Наличност"], rows))
            print(f"  Общо: {total} {p.unit}")
