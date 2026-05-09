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

        from views.product_sort_view import ProductSortView
        self.sort_view = ProductSortView(product_controller, inventory_controller)

    # ПОМОЩНИ МЕТОДИ

    def _stock(self, product):
        return self.inventory_controller.get_total_stock(product.product_id)

    def _print_products(self, products, title=""):
        if not products:
            print("\nНяма продукти.\n")
            return

        rows = []
        for p in products:
            qty = self._stock(p)
            short_id = str(p.product_id)[:8]
            price_text = f"{float(p.price):.2f} лв."
            rows.append([short_id, p.name[:30], f"{qty:.2f} {p.unit}", price_text])

        if title:
            print(f"\n{title}")
        print(format_table(["ID", "Име", "Наличност", "Цена"], rows))
        input("\nEnter за продължение...")

    def _select_category(self):
        categories = self.category_controller.get_all()
        if not categories:
            print("\nНяма категории.")
            return None

        root_categories = [c for c in categories if not c.parent_id]

        while True:
            print("\nИзбор на категория:")
            for i, c in enumerate(root_categories, start=1):
                print(f"{i}. {c.name}")

            choice = input("\nНомер или име (Enter за отказ): ").strip()
            if not choice:
                return None

            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(root_categories):
                    return root_categories[index].category_id

            for c in root_categories:
                if choice.lower() in c.name.lower():
                    return c.category_id

            print("Невалиден избор. Опитайте пак.")

    # МЕНЮ

    def show_menu(self, user):
        menu = Menu("Меню продукти", [
            MenuItem("1", "Създаване на продукт", self.create_product),
            MenuItem("2", "Премахване на продукт", self.remove_product),
            MenuItem("3", "Всички продукти", self.show_all),
            MenuItem("4", "Търсене по име", self.search),
            MenuItem("5", "Филтър по категория", self.filter_by_category),
            MenuItem("6", "Критични наличности", self.low_stock),
            MenuItem("7", "Сортиране", lambda u: self.sort_view.show_menu()),
            MenuItem("0", "Назад", lambda u: "break")
        ])
        self._run_menu(menu, user)

    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice in ("0", None):
                break
            menu_obj.execute(choice, user)

    # CRUD

    def create_product(self, user):
        print("\nНов продукт")
        print("(Напишете 'отказ' за изход)")

        while True:
            name = input("Име: ").strip()
            if name.lower() == "отказ":
                return
            if len(name) < 2:
                print("Името е твърде кратко.")
                continue
            break

        while True:
            price_raw = input("Цена: ").strip()
            if price_raw.lower() == "отказ":
                return
            try:
                price = float(price_raw)
                if price <= 0:
                    print("Цената трябва да е положителна.")
                    continue
                break
            except ValueError:
                print("Невалидно число.")
                continue

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
            new_product = self.product_controller.add(product_data, user.user_id)
            print(f"\nПродуктът '{new_product.name}' е добавен.")
        except Exception as e:
            print(f"\nПроблем при запис: {e}")

    def remove_product(self, user):
        print("\nИзтриване на продукт")

        while True:
            pid = input("ID (или 'отказ'): ").strip()
            if not pid or pid.lower() == "отказ":
                return

            product = self.product_controller.get_by_id(pid)
            if product:
                break
            print("Няма такъв продукт.")

        confirm = input(f"Искате ли да изтрием '{product.name}'? (y/n): ").strip().lower()
        if confirm == "y":
            try:
                self.product_controller.delete_by_id(product.product_id, user.user_id)
                print("Продуктът е изтрит.")
            except Exception as e:
                print(f"Проблем при изтриване: {e}")

    # ТЪРСЕНЕ / ФИЛТРИ

    def show_all(self, _):
        self._print_products(self.product_controller.get_all(), "Всички продукти")

    def search(self, _):
        while True:
            keyword = input("\nТърсене (име/описание, Enter за отказ): ").strip()
            if not keyword:
                return
            results = self.product_controller.search(keyword)
            self._print_products(results, f"Резултати за '{keyword}'")
            break

    def filter_by_category(self, _):
        category_id = self._select_category()
        if not category_id:
            return

        child_ids = self.category_controller.get_all_hierarchical_ids(category_id)
        all_ids = [category_id] + (child_ids if child_ids else [])

        all_results = []
        for cid in all_ids:
            found = self.product_controller.filter_by_category(cid)
            all_results.extend(found)

        unique_results = list({p.product_id: p for p in all_results}.values())
        self._print_products(unique_results, "Продукти в категорията")


    def low_stock(self, _):
        print("\nКритични наличности")

        while True:
            raw = input("Минимална граница (Enter за 5.0): ").strip()
            if raw.lower() == "отказ":
                return
            if not raw:
                threshold = 5.0
                break
            try:
                threshold = float(raw)
                if threshold < 0:
                    print("Границата не може да е отрицателна.")
                    continue
                break
            except ValueError:
                print("Невалидно число.")
                continue

        low = [p for p in self.product_controller.get_all() if self._stock(p) < threshold]
        self._print_products(low, f"Под {threshold}")
