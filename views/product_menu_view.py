from views.menu import Menu, MenuItem
from views.password_utils import format_table


class ProductMenuView:
    def __init__(self, product_controller, category_controller,
                 inventory_controller, movement_controller, activity_log_controller=None):

        self.product_controller = product_controller
        self.category_controller = category_controller
        self.inventory_controller = inventory_controller
        self.movement_controller = movement_controller
        self.activity_log = activity_log_controller

        # Сортировката обикновено също е View, подаваме контролерите
        from views.product_sort_view import ProductSortView
        self.sort_view = ProductSortView(product_controller, inventory_controller)

    # ============================================================
    # ПОМОЩНИ МЕТОДИ
    # ============================================================

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
            # Стандартен достъп до атрибутите p.price и p.name
            price_text = f"{float(p.price):.2f} лв."
            rows.append([short_id, p.name[:30], f"{qty:.2f} {p.unit}", price_text])

        if title:
            print(f"\n{title.upper()}")
        print(format_table(["ID", "Име", "Наличност", "Цена"], rows))
        input("\nНатиснете Enter за продължение...")

    def _select_category(self):
        """Избор на категория с While True цикъл."""
        categories = self.category_controller.get_all()
        if not categories:
            print("\nНяма налични категории.")
            return None

        # Стандартна филтрация на root категории
        root_categories = [c for c in categories if not c.parent_id]

        while True:
            print("\nИЗБОР НА КАТЕГОРИЯ")
            for i, c in enumerate(root_categories, start=1):
                print(f"{i}. {c.name}")

            choice = input("\nИзберете номер или име (Enter за отказ): ").strip()
            if not choice:
                return None

            # Избор по номер
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(root_categories):
                    return root_categories[index].category_id

            # Избор по име
            for c in root_categories:
                if choice.lower() in c.name.lower():
                    return c.category_id

            print("Грешка: Невалиден избор. Опитайте отново.")

    # ============================================================
    # МЕНЮТА
    # ============================================================

    def show_menu(self, user):
        menu = Menu("Меню Продукти", [
            MenuItem("1", "Операции с продукти (CRUD)", self.menu_manage),
            MenuItem("2", "Списък и търсене", self.menu_search),
            MenuItem("3", "Критични наличности", self.low_stock),
            MenuItem("4", "Сортиране", lambda u: self.sort_view.show_menu()),
            MenuItem("0", "Назад", lambda u: "break")
        ])
        self._run_menu(menu, user)

    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice in ("0", None):
                break
            menu_obj.execute(choice, user)

    def menu_manage(self, user):
        submenu = Menu("Управление", [
            MenuItem("1", "Създаване на продукт", self.create_product),
            MenuItem("2", "Премахване на продукт", self.remove_product),
            MenuItem("0", "Назад", lambda u: "break")
        ])
        self._run_menu(submenu, user)

    def menu_search(self, user):
        submenu = Menu("Търсене и Филтри", [
            MenuItem("1", "Всички продукти", self.show_all),
            MenuItem("2", "Търсене по име", self.search),
            MenuItem("3", "Филтър по категория", self.filter_by_category),
            MenuItem("0", "Назад", lambda u: "break")
        ])
        self._run_menu(submenu, user)

    # ============================================================
    # CRUD ОПЕРАЦИИ
    # ============================================================

    def create_product(self, user):
        print("\n--- НОВ ПРОДУКТ ---")
        print("(Напишете 'отказ' по всяко време за изход)")

        # Валидация за Име
        while True:
            name = input("Име на продукт: ").strip()
            if name.lower() == "отказ": return
            if len(name) < 2:
                print("Грешка: Името трябва да е поне 2 символа!")
                continue
            break

        # Валидация за Цена
        while True:
            price_raw = input("Цена: ").strip()
            if price_raw.lower() == "отказ": return
            try:
                price = float(price_raw)
                if price <= 0:
                    print("Грешка: Цената трябва да е положително число!")
                    continue
                break
            except ValueError:
                print("Грешка: Моля, въведете валидно число за цена!")

        desc = input("Описание: ").strip()
        unit = input("Мерна единица (кг, бр, л) [бр.]: ").strip() or "бр."

        category_id = self._select_category()

        product_data = {
            "name": name,
            "description": desc,
            "price": price,
            "unit": unit,
            "category_ids": [category_id] if category_id else []
        }

        try:
            # Използваме user.user_id директно (стандартен достъп)
            new_product = self.product_controller.add(product_data, user.user_id)
            print(f"\n[OK] Продуктът '{new_product.name}' е добавен успешно.")
        except Exception as e:
            print(f"\nГрешка при запис: {e}")

    def remove_product(self, user):
        print("\n--- ИЗТРИВАНЕ НА ПРОДУКТ ---")

        while True:
            pid = input("ID на продукт (или 'отказ'): ").strip()
            if not pid or pid.lower() == "отказ": return

            product = self.product_controller.get_by_id(pid)
            if product:
                break
            print("Грешка: Продуктът не е намерен.")

        confirm = input(f"Сигурни ли сте, че триете '{product.name}'? (y/n): ").strip().lower()
        if confirm == "y":
            try:
                self.product_controller.delete_by_id(product.product_id, user.user_id)
                print("[OK] Продуктът е изтрит.")
            except Exception as e:
                print(f"Грешка при изтриване: {e}")

    # ============================================================
    # ТЪРСЕНЕ / ФИЛТРИ
    # ============================================================

    def show_all(self, _):
        self._print_products(self.product_controller.get_all(), "Всички налични продукти")

    def search(self, _):
        while True:
            keyword = input("\nТърсене (име/описание, Enter за отказ): ").strip()
            if not keyword: return
            results = self.product_controller.search(keyword)
            self._print_products(results, f"Резултати за '{keyword}'")
            break

    def filter_by_category(self, _):
        # 1. Избираме основната категория (напр. "Мебели")
        category_id = self._select_category()
        if not category_id:
            return

        # 2. Взимаме списък с ID-тата на всички нейни подкатегории (напр. "Столове", "Маси")
        # Използваме метода от CategoryController, който вече обсъждахме
        child_ids = self.category_controller.get_all_hierarchical_ids(category_id)

        # 3. Обединяваме избраното ID с тези на децата му
        # Подсигуряваме се, че child_ids не е None
        all_ids = [category_id] + (child_ids if child_ids else [])

        # 4. Търсим продукти, които съвпадат с който и да е от тези ID-та
        all_results = []
        for cid in all_ids:
            found = self.product_controller.filter_by_category(cid)
            all_results.extend(found)

        # 5. Премахваме дубликати (ако продукт е в повече от една подкатегория)
        unique_results = list({p.product_id: p for p in all_results}.values())

        # 6. Принтираме
        self._print_products(unique_results, "Продукти в категорията и нейните подкатегории")
    # ============================================================
    # КРИТИЧНИ НАЛИЧНОСТИ
    # ============================================================

    def low_stock(self, _):
        print("\n--- ПРОВЕРКА НА КРИТИЧНИ НАЛИЧНОСТИ ---")

        while True:
            raw = input("Минимална граница (Enter за 5.0, 'отказ' за изход): ").strip()
            if raw.lower() == "отказ": return
            if not raw:
                threshold = 5.0
                break
            try:
                threshold = float(raw)
                if threshold < 0:
                    print("Грешка: Границата не може да е отрицателна!")
                    continue
                break
            except ValueError:
                print("Грешка: Въведете валидно число!")

        low = [p for p in self.product_controller.get_all() if self._stock(p) < threshold]
        self._print_products(low, f"Продукти под границата от {threshold}")