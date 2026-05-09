from views.menu import Menu, MenuItem
from views.password_utils import format_table


class ProductSortView:
    def __init__(self, product_controller, inventory_controller):
        self.product_controller = product_controller
        self.inventory_controller = inventory_controller

    def show_menu(self, _=None):
        menu = self._build_menu()
        while True:
            choice = menu.show()
            if choice == "0" or choice is None:
                break
            menu.execute(choice, None)

    def _build_menu(self):
        return Menu("Сортиране на продукти", [
            MenuItem("1", "По име (A–Z)", self.sort_by_name),
            MenuItem("2", "По цена (висока -> ниска)", self.sort_price_desc),
            MenuItem("3", "По цена (ниска -> висока)", self.sort_price_asc),
            MenuItem("4", "По количество (високо -> ниско)", self.sort_qty_desc),
            MenuItem("5", "По количество (ниско -> високо)", self.sort_qty_asc),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    def sort_by_name(self, _):
        products = self.product_controller.get_sorted_by_name()
        self._print_sorted(products, "Име (A–Z)", "Вградено сортиране")

    def sort_price_desc(self, _):
        products = self.product_controller.get_custom_sort(
            sort_type="price",
            algorithm="selection",
            reverse=True
        )
        self._print_sorted(products, "Цена (висока -> ниска)", "Selection Sort")

    def sort_price_asc(self, _):
        products = self.product_controller.get_custom_sort(
            sort_type="price",
            algorithm="bubble",
            reverse=False
        )
        self._print_sorted(products, "Цена (ниска -> висока)", "Bubble Sort")

    def sort_qty_desc(self, _):
        products = self.product_controller.get_sorted_by_quantity(
            self.inventory_controller,
            algorithm="bubble",
            reverse=True
        )
        self._print_sorted(products, "Количество (високо -> ниско)", "Bubble Sort")

    def sort_qty_asc(self, _):
        products = self.product_controller.get_sorted_by_quantity(
            self.inventory_controller,
            algorithm="selection",
            reverse=False
        )
        self._print_sorted(products, "Количество (ниско -> високо)", "Selection Sort")

    def _print_sorted(self, products, title, algorithm_name):
        if not products:
            print("\nНяма продукти за показване.")
            return

        print(f"\nСортиране по: {title}")
        print(f"Метод: {algorithm_name}\n")

        rows = []
        for p in products:
            stock = self.inventory_controller.get_total_stock(p.product_id)
            short_id = str(p.product_id)[:8]

            try:
                price_val = float(p.price)
            except (ValueError, TypeError):
                price_val = 0.0

            rows.append([
                short_id,
                p.name[:25],
                f"{stock:.2f} {p.unit}",
                f"{price_val:.2f} лв."
            ])

        print(format_table(["ID", "Име", "Наличност", "Цена"], rows))
        input("\nEnter за връщане...")
