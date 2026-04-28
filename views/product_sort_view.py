from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.product_controller import ProductController


class ProductSortView:
    def __init__(self, controller: ProductController):
        self.controller = controller


    def show_menu(self, _=None):
        menu = self._build_menu()
        while True:
            choice = menu.show()
            result = menu.execute(choice, None)
            if result == "break":
                break


    def _build_menu(self):
        """ Дефинира опциите за сортиране. """
        return Menu("Сортиране на продукти", [
            MenuItem("1", "По име (A–Z) – вградено сортиране", self.sort_by_name),
            MenuItem("2", "По цена (висока -> ниска) – selection sort", self.sort_price_desc),
            MenuItem("3", "По цена (ниска -> висока) – bubble sort", self.sort_price_asc),
            MenuItem("4", "По количество (високо -> ниско) – bubble sort", self.sort_qty_desc),
            MenuItem("5", "По количество (ниско -> високо) – selection sort", self.sort_qty_asc),
            MenuItem("0", "Назад", lambda u: "break")
        ])


    def sort_by_name(self, _):
        products = sorted(self.controller.get_all(), key=lambda p: p.name.lower())
        self._print_sorted(products, "Име (A–Z) ↑", "Вградено сортиране")

    # Цена висока - ниска
    def sort_price_desc(self, _):
        products = self.controller.selection_sort()
        self._print_sorted(products, "Цена (висока -> ниска)", "Selection Sort")


    def sort_price_asc(self, _):
        products = self.controller.bubble_sort()
        products.reverse()
        self._print_sorted(products, "Цена (ниска -> висока)", "Bubble Sort")

    # Количество високо - ниско
    def sort_qty_desc(self, _):
        products = sorted(
            self.controller.get_all(),
            key=lambda p: self.controller.get_total_stock(p.product_id),
            reverse=True
        )
        self._print_sorted(products, "Количество (високо -> ниско)", "Bubble Sort")

    # Количество ниско - високо
    def sort_qty_asc(self, _):
        products = sorted(
            self.controller.get_all(),
            key=lambda p: self.controller.get_total_stock(p.product_id)
        )
        self._print_sorted(products, "Количество (ниско -> високо)", "Selection Sort")


    # Общ метод за визуализация
    def _print_sorted(self, products, title, algorithm):
        if not products:
            print("\n[!] Няма продукти за показване.")
            return

        print(f"\nСортиране по: {title}")
        print(f"Алгоритъм: {algorithm}\n")

        rows = []

        for p in products:
            stock = self.controller.get_total_stock(p.product_id)
            rows.append([
                p.name,
                f"{p.price:.2f} лв.",
                f"{stock:.2f} {p.unit}"
            ])

        print(format_table(["Име", "Цена", "Количество"], rows))
