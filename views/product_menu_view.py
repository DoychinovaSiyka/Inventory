import uuid
from datetime import datetime
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
        all_categories = self.category_controller.get_all()
        if not all_categories:
            print("\nНяма налични категории.")
            return None

        # Филтрираме само категориите без родител
        main_categories = [c for c in all_categories if not c.parent_id or str(c.parent_id).lower() == "none"]
        print("\nИЗБОР НА ГЛАВНА КАТЕГОРИЯ")
        for i, c in enumerate(main_categories):
            print(f"{i + 1}. {c.name}")

        while True:
            raw = input("\nИзберете номер или име (Enter за назад): ").strip()
            if not raw:
                return None

            selected_cat = None

            # Проверка по номер
            if raw.isdigit():
                idx = int(raw) - 1
                if 0 <= idx < len(main_categories):
                    selected_cat = main_categories[idx]

            # Проверка по име
            if not selected_cat:
                for c in main_categories:
                    if raw.lower() in c.name.lower():
                        selected_cat = c
                        break

            if selected_cat:
                # Вземаме всички подкатегории рекурсивно чрез контролера
                sub_cats = self.category_controller.filter_by_parent(selected_cat.category_id)

                all_related_ids = [c.category_id for c in sub_cats]
                all_related_ids.append(selected_cat.category_id)  # Добавяме и избрания родител

                # ВРЪЩАМЕ СПИСЪК ОТ ID-та
                return all_related_ids

            print("Невалиден избор. Моля, изберете номер от списъка.")


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

    def _select_unit(self):
        units = [("1", "Килограм (кг.)", "кг"), ("2", "Брой (бр.)", "бр"), ("3", "Литър (л.)", "л"), ("4", "Пакет", "пакет")]
        print("\nИзберете мерна единица:")
        for num, display, _ in units:
            print(f"{num}. {display}")

        while True:
            choice = input("Изберете номер (1-4) или 'отказ': ").strip()
            if choice.lower() == 'отказ':
                return 'отказ'
            for num, _, code in units:
                if choice == num:
                    return code
            print("Невалиден избор. Моля, натиснете 1, 2, 3 или 4.")

    def create_product(self, user):
        print("\nНов продукт (Напишете 'отказ' за прекратяване)")
        try:

            while True:
                name = input("Име: ").strip()
                if name.lower() == 'отказ':
                    return
                try:
                    ProductValidator.validate_name(name)
                    break
                except Exception as e: print(f"Грешка: {e}")


            while True:
                price_raw = input("Цена: ").strip()
                if price_raw.lower() == 'отказ':
                    return
                try:
                    price = ProductValidator.parse_float(price_raw, "Цена")
                    break
                except Exception as e: print(f"Грешка: {e}")


            while True:
                description = input("Описание: ").strip()
                if description.lower() == 'отказ':
                    return
                if len(description) >= 3:
                    break
                print("Описанието трябва да е поне 3 символа.")


            unit_code = self._select_unit()
            if unit_code == 'отказ':
                return
            unit = ProductValidator.validate_unit(unit_code)


            category_id = self._select_category()


            product_data = {"name": name, "description": description, "price": price,
                            "unit": unit, "categories": [category_id] if category_id else []}

            new_p = self.product_controller.add(product_data, user.user_id)
            print(f"\nПродуктът '{new_p.name}' е създаден успешно!")

        except Exception as e:
            print(f"\nГрешка при създаване: {e}")

    def edit_product(self, user):
        print("\nРедактиране на продукт")
        pid = input("Въведете ID: ").strip()
        if not pid: return

        product = self.product_controller.get_by_id(pid)
        if not product:
            print("Продуктът не е намерен.")
            return

        print(f"Редактиране на: {product.name}")
        try:

            while True:
                new_name = input(f"Ново име [{product.name}]: ").strip()
                if new_name.lower() == 'отказ': return
                if not new_name:
                    new_name = None
                    break
                try:
                    ProductValidator.validate_name(new_name)
                    break
                except Exception as e: print(f"Грешка: {e}")


            while True:
                new_price_raw = input(f"Нова цена [{product.price}]: ").strip()
                if new_price_raw.lower() == 'отказ': return
                if not new_price_raw:
                    new_price = None
                    break
                try:
                    new_price = ProductValidator.parse_float(new_price_raw)
                    break
                except Exception as e: print(f"Грешка: {e}")


            while True:
                new_desc = input(f"Ново описание [{product.description}]: ").strip()
                if new_desc.lower() == 'отказ': return
                if not new_desc:
                    new_desc = None
                    break
                if len(new_desc) >= 3:
                    break
                print("Описанието трябва да е поне 3 символа.")

            self.product_controller.update_product(product.product_id, new_name=new_name, new_description=new_desc,
                                                   new_price=new_price, user_id=user.user_id)
            print("Продуктът е обновен.")
        except Exception as e:
            print(f"Грешка при редакция: {e}")

    def remove_product(self, user):
        pid = input("\nID за премахване: ").strip()
        if not pid: return
        product = self.product_controller.get_by_id(pid)
        if not product:
            print("Продуктът не е намерен.")
            return

        confirm = input(f"Сигурни ли сте, че триете '{product.name}'? (y/n): ").strip().lower()
        if confirm == 'y':
            self.product_controller.delete_by_id(product.product_id, user.user_id)
            print("Продуктът е премахнат.")

    def show_all(self, _):
        self._print_products(self.product_controller.get_all(), "Списък на всички продукти")

    def search(self, _):
        keyword = input("\nВъведете име за търсене: ").strip()
        if keyword:
            self._print_products(self.product_controller.search(keyword), f"Резултати за '{keyword}'")

    def filter_by_category(self, _):
        cat_id = self._select_category()
        if cat_id:
            # Вече ще работи рекурсивно, ако си сложила оправения филтър в контролера
            self._print_products(self.product_controller.filter_by_category(cat_id), "Продукти в категорията")

    def low_stock(self, _):
        while True:
            threshold_raw = input("\nМинимална граница (Enter за 5.0): ").strip()
            if threshold_raw.lower() == 'отказ': return
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

        self._print_products(low_products, f"Критични наличности (под {threshold})")