# views/product_sort_view.py

from menus.menu import Menu, MenuItem
from storage.password_utils import format_table
from controllers.product_controller import ProductController


class ProductSortView:
    def __init__(self, controller: ProductController):
        self.controller = controller

    # Няма нужда от user – не се използва
    def show_menu(self):
        menu = Menu("Сортиране на продукти", [
            MenuItem("1", "По име (A–Z) – вградено сортиране", self.sort_by_name),
            MenuItem("2", "По цена (висока → ниска) – selection sort", self.sort_price_desc),
            MenuItem("3", "По цена (ниска → висока) – bubble sort", self.sort_price_asc),
            MenuItem("4", "По количество (високо → ниско) – bubble sort", self.sort_qty_desc),
            MenuItem("5", "По количество (ниско → високо) – selection sort", self.sort_qty_asc),
            MenuItem("0", "Назад", lambda u: "break")
        ])

        while True:
            choice = menu.show()
            result = menu.execute(choice, None)
            if result == "break":
                break

    # 1. По име
    def sort_by_name(self, _):
        products = self.controller.sort_by_name()
        self._print_sorted(products, "Име (A–Z) ↑", "Вградено сортиране")

    # 2. Цена
    def sort_price_desc(self, _):
        products = self.controller.selection_sort()
        self._print_sorted(products, "Цена (висока → ниска)", "Selection Sort")

    # 3. Цена
    def sort_price_asc(self, _):
        products = self.controller.bubble_sort()
        self._print_sorted(products, "Цена (ниска → висока)", "Bubble Sort")

    # 4. Количество
    def sort_qty_desc(self,_):
        products = self.controller.bubble_sort()
        products.sort(key=lambda p: p.quantity, reverse=True)
        self._print_sorted(products, "Количество (високо → ниско)", "Bubble Sort")

    # 5. Количество
    def sort_qty_asc(self,_):
        products = self.controller.selection_sort()
        products.sort(key=lambda p: p.quantity)
        self._print_sorted(products, "Количество (ниско → високо)", "Selection Sort")

    # Общ метод за печат
    @staticmethod
    def _print_sorted( products, title, algorithm):
        print(f"\n=== Сортиране по: {title} ===")
        print(f"Алгоритъм: {algorithm}\n")

        rows = [
            [p.name.ljust(20), f"{p.price:.2f} лв.", f"{p.quantity} {p.unit}"]
            for p in products
        ]

        print(format_table(["Име", "Цена", "Количество"], rows))
