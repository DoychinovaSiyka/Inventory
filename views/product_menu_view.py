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
        return Menu("МЕНЮ ПРОДУКТИ", [MenuItem("1", "Създаване на продукт", self.create_product),
                                      MenuItem("2", "Премахване на продукт", self.remove_product),
                                      MenuItem("3", "Редактиране на продукт", self.edit_product),
                                      MenuItem("4", "Покажи всички продукти",
                                                 self.show_all_protected if self._is_operator() else self.show_all),
                                      MenuItem("5", "Търсене", self.search),
                                      MenuItem("6", "Сортиране на продукти",
                                               self.sort_menu_protected if self._is_operator() else self.sort_menu),
                                      MenuItem("7", "Средна цена", self.average_price),
                                      MenuItem("8", "Филтриране по категория", self.filter_by_category),
                                      MenuItem("9", "Увеличаване на количество", self.increase_quantity),
                                      MenuItem("10", "Намаляване на количество", self.decrease_quantity),
                                      MenuItem("11", "Продукти с ниска наличност", self.low_stock),
                                      MenuItem("12", "Най-скъп продукт", self.most_expensive),
                                      MenuItem("13", "Най-евтин продукт", self.cheapest),
                                      MenuItem("14", "Обща стойност на склада", self.total_value),
                                      MenuItem("15", "Групиране по категории", self.group_by_category),
                                      MenuItem("16", "Разширено търсене", self.advanced_search),
                                      MenuItem("0", "Назад", lambda u: "break")])

    @staticmethod
    def _is_operator():
        return False

    def show_menu(self, user: User):
        readonly = user.role in ["Operator", "Anonymous"]
        while True:
            choice = self.menu.show()
            if readonly and choice in ["1", "2", "3", "9", "10"]:
                print(f"[!] Функцията не е достъпна за роля: {user.role}")
                continue
            if self.menu.execute(choice, user) == "break":
                break

    #  CRUD
    def create_product(self, user):
        print("\n  Създаване на продукт  ")
        name = input("Име: ").strip()
        description = input("Описание: ").strip()
        price_raw = input("Цена: ")
        quantity_raw = input("Количество: ")
        unit = input("Мерна единица (пример: кг, бр, л, пакет): ").strip()

        try:
            price = ProductValidator.parse_float(price_raw, "Цена")
            quantity = ProductValidator.parse_float(quantity_raw, "Количество")
        except ValueError as e:
            print(e)
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
            return

        try:
            u_id = user.user_id
            product_data = {"name": name, "category_ids": [category_id], "quantity": quantity, "unit": unit,
                "description": description, "price": price, "supplier_id": None, "location_id": location_id}

            self.product_controller.add(product_data, u_id)
            print("Продуктът е създаден успешно.")
        except ValueError as e:
            print("Грешка:", e)

    def remove_product(self, user):
        pid = input("ID на продукт: ").strip()
        try:
            u_id = user.user_id
            self.product_controller.remove_by_id(pid, u_id)
            print("Продуктът е премахнат.")
        except ValueError as e:
            print("Грешка:", e)

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
        new_qty_raw = input(f"Ново количество ({product.quantity}): ").strip()
        if new_qty_raw:
            for suffix in ["бр.", "бр", "кг.", "кг", "л.", "л", " пакет", "пакет"]:
                if new_qty_raw.endswith(suffix):
                    new_qty_raw = new_qty_raw.replace(suffix, "").strip()

        try:
            new_price = ProductValidator.parse_float(new_price_raw, "Цена") \
                if new_price_raw else product.price
            new_qty = ProductValidator.parse_float(new_qty_raw, "Количество") \
                if new_qty_raw else product.quantity
            self.product_controller.update_product(pid, new_name, new_desc, new_price, new_qty)
            print("Продуктът е обновен.")
        except ValueError as e:
            print("Грешка:", e)

    #  DISPLAY
    def show_all(self, _):
        products = self.product_controller.get_all()
        if not products:
            print("Няма продукти.")
            return
        columns = ["ID", "Име", "Склад", "Наличност", "Цена"]
        rows = [[p.product_id, p.name, p.location_id, f"{p.quantity} {p.unit}", self.format_lv(p.price)] for p in products]
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
        for p in results:
            print(f"{p.product_id} | {p.name} | {p.location_id} | {p.quantity} {p.unit} | {self.format_lv(p.price)}")

    def sort_menu(self, _):
        self.sort_view.show_menu()

    @require_password("parola123")
    def sort_menu_protected(self, user):
        self.sort_menu(user)

    #  REPORTS
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
            return
        results = self.product_controller.search_by_category(selected_id)
        if not results:
            print("Няма продукти.")
            return
        for p in results:
            print(f"{p.name} | {p.location_id} | {p.quantity} {p.unit}")

    def increase_quantity(self, user):
        pid = input("ID на продукт: ").strip()
        amount_raw = input("Количество за добавяне: ")
        try:
            amount = ProductValidator.parse_float(amount_raw, "Количество")
            u_id = user.user_id
            self.product_controller.increase_quantity(pid, amount, u_id)
            print("Увеличено.")
        except ValueError as e:
            print(e)

    def decrease_quantity(self, user):
        pid = input("ID на продукт: ").strip()
        amount_raw = input("Количество за изваждане: ")
        try:
            amount = ProductValidator.parse_float(amount_raw, "Количество")
            u_id = user.user_id
            self.product_controller.decrease_quantity(pid, amount, u_id)
            print("Намалено.")
        except ValueError as e:
            print(e)

    def low_stock(self, _):
        low = self.product_controller.check_low_stock()
        if not low:
            print("Няма критични продукти.")
            return
        for p in low:
            print(f"ВНИМАНИЕ: {p.name} ({p.quantity} {p.unit}) в {p.location_id}")

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

    def group_by_category(self, _):
        groups = self.product_controller.group_by_category_display()
        for cat_id, items in groups.items():
            cat = self.category_controller.get_by_id(cat_id)
            print(f"\n--- {cat.name if cat else cat_id} ---")
            for p in items:
                print(f"{p['name']} ({p['location']}) - {p['quantity']} {p['unit']}")

    def advanced_search(self, _):
        print("\n  Разширено търсене  ")
        keyword = input("Ключова дума: ").strip() or None
        min_raw = input("Мин. цена: ")
        max_raw = input("Макс. цена: ")
        try:
            min_p = ProductValidator.parse_optional_float(min_raw)
            max_p = ProductValidator.parse_optional_float(max_raw)
        except ValueError as e:
            print(e)
            return
        results = self.product_controller.search_combined(name_keyword=keyword, min_price=min_p,
                                                          max_price=max_p)
        if not results:
            print("Няма резултати.")
            return
        for p in results:
            print(f"{p.product_id} | {p.name} | {p.location_id} | {self.format_lv(p.price)}")
