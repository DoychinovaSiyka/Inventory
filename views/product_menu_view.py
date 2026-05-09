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

    def _stock(self, product):
        # Връща общата наличност на продукта
        return self.inventory_controller.get_total_stock(product.product_id)


    def _print_products(self, products, title=""):
        if not products:
            print("\nНяма продукти.\n")
            return

        rows = []
        for p in products:
            qty = self._stock(p)
            rows.append([str(p.product_id)[:8], p.name[:30], f"{qty:.2f} {p.unit}", f"{p.price:.2f} лв."])

        if title:
            print(f"\n{title}")

        print(format_table(["ID", "Име", "Наличност", "Цена"], rows))
        input("\nEnter за продължение...")

    def _select_category(self):
        categories = self.category_controller.get_all()
        if not categories:
            return None

        print("\nКатегории:")
        for i, c in enumerate(categories, start=1):
            print(f"{i}. {c.name}")

        choice = input("\nНомер или Enter за отказ: ").strip()
        if not choice:
            return None

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(categories):
                return categories[idx].category_id


        for c in categories:
            if choice.lower() in c.name.lower():
                return c.category_id

        print("Невалиден избор.")
        return None


    def create_product(self, user):
        print("\nНов продукт (напишете 'отказ' за изход)")
        name = input("Име: ").strip()
        if name.lower() == "отказ":
            return

        price_raw = input("Цена: ").strip()
        if price_raw.lower() == "отказ":
            return

        desc = input("Описание: ").strip()
        unit = input("Мерна единица [бр.]: ").strip() or "бр."
        cat_id = self._select_category()

        data = {"name": name, "price": price_raw, "description": desc,
                "unit": unit, "category_ids": [cat_id] if cat_id else []}

        try:
            new_p = self.product_controller.add(data, user.user_id)
            print(f"\nПродуктът '{new_p.name}' е добавен.")
        except Exception as e:
            print(f"\nГрешка: {e}")

    def remove_product(self, user):
        pid = input("\nID на продукт за изтриване (или 'отказ'): ").strip()
        if pid.lower() == "отказ":
            return

        product = self.product_controller.get_by_id(pid)
        if not product:
            print("Няма такъв продукт.")
            return

        confirm = input(f"Изтриване на '{product.name}'? (y/n): ").lower()
        if confirm == "y":
            self.product_controller.delete_by_id(product.product_id, user.user_id)
            print("Изтрито.")

    def show_all(self, _):
        self._print_products(self.product_controller.get_all(), "Всички продукти")

    def search(self, _):
        keyword = input("\nТърсене (име/описание): ").strip()
        if keyword:
            results = self.product_controller.search(keyword)
            self._print_products(results, f"Резултати за '{keyword}'")

    def filter_by_category(self, _):
        cat_id = self._select_category()
        if not cat_id:
            return

        # всички под-категории
        all_ids = [cat_id] + self.category_controller.get_all_hierarchical_ids(cat_id)

        results = []
        for cid in all_ids:
            results.extend(self.product_controller.filter_by_category(cid))

        # Премахваме дубликати, ако продукт е в повече от една под-категория
        unique_results = list({p.product_id: p for p in results}.values())
        self._print_products(unique_results, "Продукти в категорията и нейните под-нива")



    def low_stock(self, _):
        raw = input("\nМинимална граница (Enter за 5.0): ").strip()
        threshold = float(raw) if raw else 5.0

        low = [p for p in self.product_controller.get_all() if self._stock(p) < threshold]
        self._print_products(low, f"Под {threshold}")

    def sort_products(self, _):
        print("\nСортиране:")
        print("1. По име")
        print("2. По цена")
        print("3. По наличност")

        choice = input("\nИзбор: ").strip()

        if choice == "1":
            sorted_list = self.product_controller.get_sorted_by_name()
            self._print_products(sorted_list, "Сортиране по име")

        elif choice == "2":
            sorted_list = self.product_controller.get_sorted_by_price()
            self._print_products(sorted_list, "Сортиране по цена")

        elif choice == "3":
            sorted_list = self.product_controller.get_sorted_by_quantity(self.inventory_controller)
            self._print_products(sorted_list, "Сортиране по наличност")

    def show_menu(self, user):
        menu = Menu("Меню продукти", [
            MenuItem("1", "Създаване на продукт", self.create_product),
            MenuItem("2", "Премахване на продукт", self.remove_product),
            MenuItem("3", "Всички продукти", self.show_all),
            MenuItem("4", "Търсене", self.search),
            MenuItem("5", "Филтър по категория", self.filter_by_category),
            MenuItem("6", "Критични наличности", self.low_stock),
            MenuItem("7", "Сортиране", self.sort_products),
            MenuItem("0", "Назад", lambda u: "break")])


        while True:
            choice = menu.show()
            if choice in ("0", None):
                break
            menu.execute(choice, user)
