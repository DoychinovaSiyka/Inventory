from views.menu import Menu, MenuItem
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from models.user import User
from views.product_sort_view import ProductSortView
from views.password_utils import require_password, format_table
from validators.product_validator import ProductValidator


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

    def menu_sort(self, _):
        self.sort_view.show_menu()

    def _print_products(self, products, title=""):
        if not products:
            print("\nНяма намерени продукти за показване.\n")
            return

        rows = []
        for p in products:
            qty = self._stock(p)
            short_id = str(p.product_id)[:8]
            rows.append([short_id, p.name, f"{qty:.2f} {p.unit}", self.format_lv(p.price)])

        if title:
            print(f"\n--- {title} ---")

        print(format_table(["ID (кратко)", "Име", "Наличност", "Цена"], rows))

    def _select_category(self):
        categories = self.category_controller.get_all()
        if not categories:
            print("\nНяма налични категории в системата.")
            return None

        print("\n--- Избор на категория ---")
        for i, c in enumerate(categories):
            print(f"{i + 1}. {c.name} [ID: {c.category_id[:8]}]")

        raw = input("\nИзберете номер или въведете кратко ID (Enter за пропускане): ").strip()
        if not raw:
            return None


        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(categories):
                return categories[idx].category_id

        cat = self.category_controller.get_by_id(raw)
        if cat:
            return cat.category_id

        print("Невалиден избор на категория.")
        return None

    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice == "0" or choice is None:
                break
            menu_obj.execute(choice, user)

    def show_menu(self, user: User):
        menu = Menu("МЕНЮ ПРОДУКТИ", [
            MenuItem("1", "Операции с продукти (CRUD)", self.menu_manage_protected),
            MenuItem("2", "Списък и търсене", self.menu_search),
            MenuItem("3", "Критични наличности", self.low_stock),
            MenuItem("4", "Сортиране по критерии", self.menu_sort_protected),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)

    @require_password("parola123")
    def menu_manage_protected(self, user):
        return self.menu_manage(user)

    @require_password("parola123")
    def menu_sort_protected(self, user):
        return self.menu_sort(user)

    def menu_manage(self, user):
        submenu = Menu("УПРАВЛЕНИЕ", [
            MenuItem("1", "Създаване на продукт", self.create_product),
            MenuItem("2", "Редактиране на продукт", self.edit_product),
            MenuItem("3", "Премахване на продукт", self.remove_product),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)

    def menu_search(self, user):
        submenu = Menu("ТЪРСЕНЕ", [
            MenuItem("1", "Покажи всички продукти", self.show_all),
            MenuItem("2", "Търсене по име", self.search),
            MenuItem("3", "Филтър по категория", self.filter_by_category),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)

    def create_product(self, user):
        print("\n--- НОВ ПРОДУКТ ---")
        try:
            name = input("Име: ").strip()
            ProductValidator.validate_name(name)
            price_raw = input("Цена: ").strip()
            price = ProductValidator.parse_float(price_raw, "Цена")

            unit = input("Мерна единица (кг, кг., kg, килограм / бр, бр., брой / л, l, литър / пакет, paket, packet): ").strip()
            unit = ProductValidator.validate_unit(unit_raw)

            category_id = self._select_category()

            product_data = {"name": name, "description": "", "price": price, "unit": unit,
                            "category_ids": [category_id] if category_id else []}

            new_p = self.product_controller.add(product_data, user.user_id)
            print(f"Продуктът е създаден успешно с ID: {new_p.product_id[:8]}")
        except Exception as e:
            print(f"Грешка при създаване: {e}")

    def edit_product(self, user):
        print("\n--- РЕДАКТИРАНЕ НА ПРОДУКТ ---")
        pid = input("Въведете кратко или пълно ID: ").strip()
        if not pid:
            return

        product = self.product_controller.get_by_id(pid)
        if not product:
            print("Продуктът не е намерен.")
            return

        print(f"Редактиране на: {product.name} [{product.product_id[:8]}]")
        try:
            new_name = input(f"Ново име (Enter за запазване '{product.name}'): ").strip() or None
            new_price_raw = input(f"Нова цена (Enter за запазване {product.price}): ").strip()
            new_price = ProductValidator.parse_float(new_price_raw) if new_price_raw else None

            self.product_controller.update_product(product.product_id, new_name=new_name, new_price=new_price,
                                                   user_id=user.user_id)
            print("Продуктът е обновен успешно.")
        except Exception as e:
            print(f"Грешка при редакция: {e}")

    def remove_product(self, user):
        print("\n--- ПРЕМАХВАНЕ НА ПРОДУКТ ---")
        pid = input("Въведете ID за изтриване: ").strip()
        if not pid:
            return

        product = self.product_controller.get_by_id(pid)
        if not product:
            print("Продуктът не е намерен.")
            return

        confirm = input(f"Наистина ли искате да изтриете '{product.name}'? (y/n): ").strip().lower()
        if confirm == 'y':
            try:
                self.product_controller.delete_by_id(product.product_id, user.user_id)
                print("Продуктът е премахнат успешно.")
            except Exception as e:
                print(f"Грешка при изтриване: {e}")
        else:
            print("Операцията е отказана.")

    def show_all(self, _):
        self._print_products(self.product_controller.get_all(), "АКТУАЛЕН СПИСЪК")

    def search(self, _):
        keyword = input("\nВъведете име за търсене: ").strip()
        if keyword:
            self._print_products(self.product_controller.search(keyword), f"РЕЗУЛТАТИ ЗА '{keyword}'")

    def filter_by_category(self, _):
        cat_id = self._select_category()
        if cat_id:
            self._print_products(self.product_controller.filter_by_category(cat_id), "ФИЛТЪР ПО КАТЕГОРИЯ")

    def low_stock(self, _):
        try:
            threshold_raw = input("\nМинимална граница (Enter за 5.0): ").strip()
            threshold = float(threshold_raw) if threshold_raw else 5.0
            low_products = [p for p in self.product_controller.get_all() if self._stock(p) < threshold]

            if not low_products:
                print(f"Няма продукти с наличност под {threshold}.")
            else:
                self._print_products(low_products, f"ПРОДУКТИ ЗА ПОРЪЧКА (Под {threshold})")
        except ValueError:
            print("Грешка: Трябва да въведете валидно число.")