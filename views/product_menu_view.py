from views.menu import Menu, MenuItem
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from models.user import User
from views.product_sort_view import ProductSortView
from views.password_utils import require_password, format_table
from validators.product_validator import ProductValidator
from analytics.product_analytics import (calculate_average_price, get_most_expensive_product,
                                         get_cheapest_product, group_products_by_category)
from textwrap import wrap


def _wrap(text, width=45):
    return "\n".join(wrap(text, width=width))


class ProductMenuView:
    def __init__(self, product_controller: ProductController, category_controller: CategoryController,
                 inventory_controller, movement_controller, activity_log_controller=None):

        self.product_controller = product_controller
        self.category_controller = category_controller
        self.inventory_controller = inventory_controller
        self.movement_controller = movement_controller
        self.activity_log = activity_log_controller
        self.sort_view = ProductSortView(product_controller, inventory_controller)


    @staticmethod
    def format_lv(value):
        return f"{value:.2f} лв."

    def _stock(self, product):
        return self.inventory_controller.get_total_stock(product.product_id)

    def _print_products(self, products, title=""):
        if not products:
            print("\nНяма продукти.\n")
            return

        rows = []
        for p in products:
            qty = self._stock(p)
            rows.append([p.product_id, p.name, f"{qty:.2f} {p.unit}", self.format_lv(p.price)])

        if title:
            print(f"\n--- {title} ---")
        print(format_table(["ID", "Име", "Наличност", "Цена"], rows))

    def _select_category(self):
        categories = self.category_controller.get_all()
        print("\nКатегории:")
        for i, c in enumerate(categories):
            print(f"{i}. {c.name}")

        raw = input("Категория: ").strip()
        if not raw:
            return None
        if raw.isdigit() and int(raw) < len(categories):
            return categories[int(raw)].category_id
        return raw


    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice == "0" or choice is None:
                break
            menu_obj.execute(choice, user)


    def show_menu(self, user: User):
        menu = Menu("МЕНЮ ПРОДУКТИ", [
            MenuItem("1", "Операции с продукти (CRUD)", self.menu_manage),
            MenuItem("2", "Списък и Търсене", self.menu_search),
            MenuItem("3", "Наличности и Анализи", self.menu_analytics),
            MenuItem("4", "Сортиране", self.menu_sort),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)


    def menu_manage(self, user):
        submenu = Menu("ОПЕРАЦИИ С ПРОДУКТИ", [
            MenuItem("1", "Създаване", self.create_product),
            MenuItem("2", "Редактиране", self.edit_product),
            MenuItem("3", "Премахване", self.remove_product),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)


    def menu_search(self, user):
        submenu = Menu("СПИСЪК И ТЪРСЕНЕ", [
            MenuItem("1", "Покажи всички продукти", self.show_all),
            MenuItem("2", "Бързо търсене (име)", self.search),
            MenuItem("3", "Разширено търсене", self.advanced_search),
            MenuItem("4", "Филтър по категория", self.filter_by_category),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)


    def menu_analytics(self, user):
        submenu = Menu("НАЛИЧНОСТИ И АНАЛИЗИ", [
            MenuItem("1", "Критични наличности", self.low_stock),
            MenuItem("2", "Разпределение по складове", self.show_stock_by_warehouses),
            MenuItem("3", "Ценова статистика", self.show_price_stats),
            MenuItem("4", "Категорийни справки", self.category_reports),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)


    def show_price_stats(self, _):
        products = self.product_controller.get_all()
        avg = calculate_average_price(products)
        p_max = get_most_expensive_product(products)
        p_min = get_cheapest_product(products)

        print("\n--- ЦЕНОВИ АНАЛИЗ ---")
        print(f"Средна цена: {self.format_lv(avg)}")
        if p_max:
            print(f"Най-скъп продукт: {p_max.name} ({self.format_lv(p_max.price)})")
        if p_min:
            print(f"Най-евтин продукт: {p_min.name} ({self.format_lv(p_min.price)})")
        input("\nEnter за продължение...")

    def category_reports(self, user):
        submenu = Menu("КАТЕГОРИЙНИ СПРАВКИ", [
            MenuItem("1", "Филтър по категория (избор на една)", self.filter_by_category),
            MenuItem("2", "Групиране по всички категории", self.group_by_category),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)

    def menu_sort(self, user):
        self.sort_view.show_menu()


    def create_product(self, user):
        print("\n  Създаване на продукт  ")
        while True:
            name = input("Име: ").strip()
            try:
                ProductValidator.validate_name(name)
                break
            except ValueError as e:
                print(f"Грешка: {e}")

        while True:
            description = input("Описание: ").strip()
            try:
                ProductValidator.validate_description(description)
                break
            except ValueError as e:
                print(f"Грешка: {e}")

        while True:
            price_raw = input("Цена: ").strip()
            try:
                price = ProductValidator.parse_float(price_raw, "Цена")
                break
            except ValueError as e:
                print(f"Грешка: {e}")

        while True:
            unit = input("Мерна единица (кг, бр., л., пакет): ").strip()
            try:
                ProductValidator.validate_unit(unit)
                break
            except ValueError as e:
                print(f"Грешка: {e}")

        category_id = self._select_category()

        try:
            product_data = {"name": name, "description": description,
                            "price": price, "unit": unit,
                            "category_ids": [category_id] if category_id else []}

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
            print(f"Продукт с ID {pid} не съществува.")
            return
        confirm = input(f"Изтриване на '{product.name}'? (y/n): ").strip().lower()
        if confirm != "y":
            print("Отказано.")
            return
        try:
            self.product_controller.delete_by_id(pid, user.user_id)
            print(f"Продуктът '{product.name}' беше премахнат.")
        except Exception as e:
            print(f"Грешка: {e}")


    def edit_product(self, user):
        print("\n  Редактиране на продукт  ")
        pid = input("ID: ").strip()
        product = self.product_controller.get_by_id(pid)
        if not product:
            print("Няма такъв продукт.")
            return

        new_name = input(f"Ново име ({product.name}): ").strip() or None
        new_description = input(f"Ново описание ({product.description}): ").strip() or None

        new_price = None
        while True:
            raw = input(f"Нова цена ({product.price}): ").strip()
            if raw == "":
                break
            try:
                new_price = ProductValidator.parse_float(raw, "Цена")
                break
            except ValueError as e:
                print(f"Грешка: {e}")

        try:
            ok = self.product_controller.update_product(product_id=pid, new_name=new_name, new_description=new_description,
                                                        new_price=new_price, user_id=user.user_id)
            print("Продуктът е обновен." if ok else "Неуспешно обновяване.")
        except Exception as e:
            print(f"Грешка: {e}")


    def show_all(self, _):
        products = self.product_controller.get_all()
        self._print_products(products, "Всички продукти")

    @require_password("parola123")
    def show_all_protected(self, user):
        return self.show_all(user)

    def search(self, _):
        keyword = input("Търсене: ").strip()
        results = self.product_controller.search(keyword)
        self._print_products(results, "Резултати от търсене")

    def average_price(self, _):
        avg = calculate_average_price(self.product_controller.get_all())
        print(f"Средна цена: {self.format_lv(avg)}")

    def filter_by_category(self, _):
        category_id = self._select_category()
        results = self.product_controller.filter_by_category(category_id)
        self._print_products(results, "Филтриране по категория")

    def low_stock(self, _):
        threshold = float(input("Граница (Enter за 5): ") or 5.0)
        products = self.product_controller.get_all()
        low = [p for p in products if self._stock(p) < threshold]
        rows = []
        for p in low:
            qty = self._stock(p)
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

    def group_by_category(self, _):
        grouped = group_products_by_category(self.product_controller.get_all())
        for cat, items in grouped.items():
            print(f"\n--- {cat} ---")
            for p in items:
                qty = self._stock(p)
                print(f"{p.name} | {qty} {p.unit}")

    def advanced_search(self, _):
        print("\n  Разширено търсене  ")
        keyword = input("Ключово слово: ").strip() or None
        raw_min = input("Мин. цена: ").strip()
        try:
            min_price = ProductValidator.parse_optional_float(raw_min)
        except ValueError:
            min_price = None

        raw_max = input("Макс. цена: ").strip()
        try:
            max_price = ProductValidator.parse_optional_float(raw_max)
        except ValueError:
            max_price = None

        category_id = self._select_category()

        results = self.product_controller.search_combined(keyword=keyword, min_price=min_price, max_price=max_price,
                                                          category_id=category_id,
                                                          inventory_controller=self.inventory_controller)

        if not results:
            print("\nНяма резултати.\n")
            return

        rows = []
        for p in results:
            stock = self._stock(p)
            rows.append([p.name, f"{p.price:.2f} лв.", f"{stock} {p.unit}", ", ".join([c.name for c in p.categories])
            if p.categories else "-"])

        print(f"\nНамерени резултати ({len(results)}):")
        print(format_table(["Продукт", "Цена", "Наличност", "Категории"], rows))

    def show_stock_by_warehouses(self, _):
        products = self.product_controller.get_all()
        if not products:
            print("Няма продукти.")
            return

        all_locations = self.movement_controller.location_controller.get_all()

        for p in products:
            print(f"\n   {p.name}\n")

            inv_entry = self.inventory_controller.data.get("products", {}).get(p.product_id, {})
            product_locations = inv_entry.get("locations", {})
            total = sum(float(q) for q in product_locations.values())
            if total == 0:
                rows = [[loc.name, "0 (няма наличност)"] for loc in all_locations]
                print(format_table(["Склад", "Наличност"], rows))
                print(f"\nОбщо: 0.0 {p.unit}\n")
                continue

            rows = []
            for loc in all_locations:
                wh_id = loc.location_id
                qty = float(product_locations.get(wh_id, 0))
                rows.append([loc.name, f"{qty} {p.unit}"])

            print(format_table(["Склад", "Наличност"], rows))
            print(f"\nОбщо: {total:.1f} {p.unit}\n")
