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

    def _is_operator(self, user):
        return True

    def menu_sort(self, _):
        self.sort_view.show_menu()

    def _print_products(self, products, title=""):
        if not products:
            print("\nНяма продукти за показване.\n")
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
        raw = input("Изберете категория (номер): ").strip()
        if not raw: return None
        if raw.isdigit() and int(raw) < len(categories):
            return categories[int(raw)].category_id
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
            MenuItem("2", "Списък и Бързо търсене", self.menu_search),
            MenuItem("3", "Критични наличности", self.low_stock),
            MenuItem("4", "Сортиране (Избор на алгоритъм)", self.menu_sort_protected),
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
            MenuItem("1", "Създаване", self.create_product),
            MenuItem("2", "Редактиране", self.edit_product),
            MenuItem("3", "Премахване", self.remove_product),
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
            unit = input("Мерна единица (бр/кг): ").strip()
            ProductValidator.validate_unit(unit)

            category_id = self._select_category()

            product_data = {"name": name, "description": "", "price": price,
                            "unit": unit, "category_ids": [category_id] if category_id else []}

            self.product_controller.add(product_data, user.user_id)
            print("[+] Продуктът е създаден успешно.")
        except Exception as e:
            print(f"[!] Грешка: {e}")

    def edit_product(self, user):
        pid = input("ID за редакция: ").strip()
        product = self.product_controller.get_by_id(pid)
        if not product: return print("[!] Не е намерен.")

        new_name = input(f"Ново име [{product.name}]: ").strip() or None
        new_price_raw = input(f"Нова цена [{product.price}]: ").strip()
        new_price = ProductValidator.parse_float(new_price_raw) if new_price_raw else None

        self.product_controller.update_product(pid, new_name=new_name, new_price=new_price, user_id=user.user_id)
        print("[+] Обновено.")

    def remove_product(self, user):
        pid = input("ID за изтриване: ").strip()
        if input("Сигурни ли сте? (y/n): ").lower() == 'y':
            self.product_controller.delete_by_id(pid, user.user_id)
            print("[+] Премахнат.")

    def show_all(self, _):
        self._print_products(self.product_controller.get_all(), "АКТУАЛЕН СПИСЪК")

    def search(self, _):
        keyword = input("Търсене по име: ").strip()
        self._print_products(self.product_controller.search(keyword), f"РЕЗУЛТАТИ ЗА '{keyword}'")

    def filter_by_category(self, _):
        cat_id = self._select_category()
        if cat_id:
            self._print_products(self.product_controller.filter_by_category(cat_id), "ПО КАТЕГОРИЯ")

    def low_stock(self, _):
        """Важна оперативна справка за поръчки"""
        try:
            threshold = float(input("Минимална граница (Enter за 5.0): ") or 5.0)
            low = [p for p in self.product_controller.get_all() if self._stock(p) < threshold]

            print(f"\n--- ПРОДУКТИ ЗА ПОРЪЧКА (Под {threshold}) ---")
            rows = [[p.name, f"{self._stock(p):.2f}", p.unit] for p in low]
            print(format_table(["ПРОДУКТ", "НАЛИЧНОСТ", "МЯРКА"], rows))
        except ValueError:
            print("[!] Невалидна стойност.")

