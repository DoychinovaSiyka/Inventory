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
        try:
            return f"{float(value):.2f} лв."
        except:
            return "0.00 лв."

    def _stock(self, product):
        return self.inventory_controller.get_total_stock(product.product_id)

    def _print_products(self, products, title=""):
        if not products:
            print("\nНяма намерени продукти.\n")
            return

        rows = []
        for p in products:
            qty = self._stock(p)
            short_id = str(p.product_id)[:8]
            rows.append([short_id, p.name, f"{qty:.2f} {p.unit}", self.format_lv(p.price)])

        if title:
            print(f"\n{title}")

        print(format_table(["ID (кратко)", "Име", "Наличност", "Цена"], rows))

    def _select_category(self):
        categories = self.category_controller.get_all()
        if not categories:
            print("\nНяма налични категории.")
            return None

        print("\nИзбор на категория:")
        for i, c in enumerate(categories):
            print(f"{i + 1}. {c.name} (ID: {c.category_id[:8]})")

        while True:
            raw = input("\nИзберете номер или въведете ID (Enter за пропускане): ").strip()
            if not raw:
                return None

            if raw.isdigit():
                idx = int(raw) - 1
                if 0 <= idx < len(categories):
                    return categories[idx].category_id

            cat = self.category_controller.get_by_id(raw)
            if cat:
                return cat.category_id

            print("Невалиден избор. Опитайте отново.")

    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice == "0" or choice is None:
                break
            menu_obj.execute(choice, user)

    def show_menu(self, user: User):
        menu = Menu("Меню продукти", [
            MenuItem("1", "Операции с продукти", self.menu_manage_protected),
            MenuItem("2", "Списък и търсене", self.menu_search),
            MenuItem("3", "Критични наличности", self.low_stock),
            MenuItem("4", "Сортиране", self.menu_sort_protected),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)

    @require_password("parola123")
    def menu_manage_protected(self, user):
        return self.menu_manage(user)

    @require_password("parola123")
    def menu_sort_protected(self, user):
        return self.sort_view.show_menu()

    def menu_manage(self, user):
        submenu = Menu("Управление", [
            MenuItem("1", "Създаване на продукт", self.create_product),
            MenuItem("2", "Редактиране на продукт", self.edit_product),
            MenuItem("3", "Премахване на продукт", self.remove_product),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)

    def menu_search(self, user):
        submenu = Menu("Търсене", [
            MenuItem("1", "Покажи всички продукти", self.show_all),
            MenuItem("2", "Търсене по име", self.search),
            MenuItem("3", "Филтър по категория", self.filter_by_category),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)

    def create_product(self, user):
        print("\nНов продукт")
        print("(Напишете 'отказ' за прекратяване)")

        try:
            while True:
                name = input("Име: ").strip()
                if name.lower() == 'отказ':
                    return
                try:
                    ProductValidator.validate_name(name)
                    break
                except Exception as e:
                    print(f"Грешка: {e}")

            while True:
                price_raw = input("Цена: ").strip()
                if price_raw.lower() == 'отказ':
                    return
                try:
                    price = ProductValidator.parse_float(price_raw, "Цена")
                    break
                except Exception as e:
                    print(f"Грешка: {e}")

            while True:
                unit_raw = input("Мерна единица (кг, бр, л, пакет): ").strip()
                if unit_raw.lower() == 'отказ':
                    return
                try:
                    unit = ProductValidator.validate_unit(unit_raw)
                    break
                except Exception as e:
                    print(f"Грешка: {e}")

            category_id = self._select_category()

            product_data = {
                "name": name,
                "description": "",
                "price": price,
                "unit": unit,
                "category_ids": [category_id] if category_id else []
            }

            new_p = self.product_controller.add(product_data, user.user_id)
            print(f"\nПродуктът '{new_p.name}' е създаден.")
        except Exception as e:
            print(f"\nГрешка при създаване: {e}")

    def edit_product(self, user):
        print("\nРедактиране на продукт")
        pid = input("Въведете ID: ").strip()
        if not pid:
            return

        product = self.product_controller.get_by_id(pid)
        if not product:
            print("Продуктът не е намерен.")
            return

        print(f"Редактиране на: {product.name} ({product.product_id[:8]})")
        print("(Enter запазва старата стойност, 'отказ' за изход)")

        try:
            while True:
                new_name = input(f"Ново име [{product.name}]: ").strip()
                if new_name.lower() == 'отказ':
                    return
                if not new_name:
                    new_name = None
                    break
                try:
                    ProductValidator.validate_name(new_name)
                    break
                except Exception as e:
                    print(f"Грешка: {e}")

            while True:
                new_price_raw = input(f"Нова цена [{product.price}]: ").strip()
                if new_price_raw.lower() == 'отказ':
                    return
                if not new_price_raw:
                    new_price = None
                    break
                try:
                    new_price = ProductValidator.parse_float(new_price_raw)
                    break
                except Exception as e:
                    print(f"Грешка: {e}")

            self.product_controller.update_product(
                product.product_id,
                new_name=new_name,
                new_price=new_price,
                user_id=user.user_id
            )

            print("Продуктът е обновен.")
        except Exception as e:
            print(f"Грешка при редакция: {e}")

    def remove_product(self, user):
        print("\nПремахване на продукт")
        pid = input("Въведете ID: ").strip()
        if not pid:
            return

        product = self.product_controller.get_by_id(pid)
        if not product:
            print("Продуктът не е намерен.")
            return

        print(f"Продукт '{product.name}' ще бъде премахнат от каталога.")
        confirm = input("Потвърдете (y/n): ").strip().lower()

        if confirm == 'y':
            try:
                self.product_controller.delete_by_id(product.product_id, user.user_id)
                print("Продуктът е премахнат.")
            except Exception as e:
                print(f"Грешка: {e}")
        else:
            print("Операцията е прекратена.")

    def show_all(self, _):
        self._print_products(self.product_controller.get_all(), "Списък на продуктите")

    def search(self, _):
        keyword = input("\nВъведете име: ").strip()
        if keyword:
            self._print_products(self.product_controller.search(keyword), f"Резултати за '{keyword}'")

    def filter_by_category(self, _):
        cat_id = self._select_category()
        if cat_id:
            self._print_products(self.product_controller.filter_by_category(cat_id), "Филтър по категория")

    def low_stock(self, _):
        while True:
            threshold_raw = input("\nМинимална граница (Enter за 5.0): ").strip()
            if threshold_raw.lower() == 'отказ':
                return
            if not threshold_raw:
                threshold = 5.0
                break
            try:
                threshold = float(threshold_raw)
                break
            except ValueError:
                print("Моля, въведете валидно число.")

        low_products = []
        for p in self.product_controller.get_all():
            if self._stock(p) < threshold:
                low_products.append(p)

        if not low_products:
            print(f"Няма продукти под {threshold}.")
        else:
            self._print_products(low_products, f"Продукти под {threshold}")
