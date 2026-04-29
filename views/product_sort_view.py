from views.menu import Menu, MenuItem
from views.password_utils import format_table

from sorting.product_sorters import (sort_by_name_logic, sort_by_price_desc_logic,
                                     bubble_sort_logic, selection_sort_logic)


class ProductSortView:
    def __init__(self, product_controller, inventory_controller):
        self.product_controller = product_controller
        self.inventory_controller = inventory_controller

    def show_menu(self, _=None):
        menu = self._build_menu()
        while True:
            choice = menu.show()
            result = menu.execute(choice, None)
            if result == "break":
                break

    def _build_menu(self):
        return Menu("Сортиране на продукти", [
            MenuItem("1", "По име (A–Z) – вградено сортиране", self.sort_by_name),
            MenuItem("2", "По цена (висока -> ниска) – selection sort", self.sort_price_desc),
            MenuItem("3", "По цена (ниска -> висока) – bubble sort", self.sort_price_asc),
            MenuItem("4", "По количество (високо -> ниско) – bubble sort", self.sort_qty_desc),
            MenuItem("5", "По количество (ниско -> високо) – selection sort", self.sort_qty_asc),
            MenuItem("0", "Назад", lambda u: "break")])



    def sort_by_name(self, _):
        products = sort_by_name_logic(self.product_controller.get_all())
        self._print_sorted(products, "Име (A–Z) ↑", "Вградено сортиране")


    def sort_price_desc(self, _):
        products = selection_sort_logic(self.product_controller.get_all(), key=lambda p: p.price, reverse=True)
        self._print_sorted(products, "Цена (висока -> ниска)", "Selection Sort")


    def sort_price_asc(self, _):
        products = bubble_sort_logic(self.product_controller.get_all(), key=lambda p: p.price, reverse=False)
        self._print_sorted(products, "Цена (ниска -> висока)", "Bubble Sort")



    def sort_qty_desc(self, _):
        products = bubble_sort_logic(self.product_controller.get_all(),
                                     key=lambda p: self.inventory_controller.get_total_stock(p.product_id), reverse=True)
        self._print_sorted(products, "Количество (високо -> ниско)", "Bubble Sort")


    def sort_qty_asc(self, _):
        products = selection_sort_logic(self.product_controller.get_all(),
                                        key=lambda p: self.inventory_controller.get_total_stock(p.product_id), reverse=False)
        self._print_sorted(products, "Количество (ниско -> високо)", "Selection Sort")


    # Печат
    def _print_sorted(self, products, title, algorithm):
        if not products:
            print("\n[!] Няма продукти за показване.")
            return
        print(f"\nСортиране по: {title}")
        print(f"Алгоритъм: {algorithm}\n")

        rows = []
        for p in products:
            stock = self.inventory_controller.get_total_stock(p.product_id)
            rows.append([p.name, f"{p.price:.2f} лв.", f"{stock:.2f} {p.unit}"])

        print(format_table(["Име", "Цена", "Количество"], rows))
