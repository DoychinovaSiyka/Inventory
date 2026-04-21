from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.product_controller import ProductController


class ProductSortView:
    def __init__(self, controller: ProductController):
        self.controller = controller
        self.menu = self._build_menu()

    # Меню за избор на метод за сортиране
    def _build_menu(self):
        return Menu("Сортиране на продукти", [MenuItem("1", "По име (A–Z) – вградено сортиране", self.sort_by_name),
                                              MenuItem("2", "По цена (висока -> ниска) – selection sort", self.sort_price_desc),
                                              MenuItem("3", "По цена (ниска -> висока) – bubble sort", self.sort_price_asc),
                                              MenuItem("4", "По количество (високо -> ниско) – bubble sort", self.sort_qty_desc),
                                              MenuItem("5", "По количество (ниско -> високо) – selection sort", self.sort_qty_asc),
                                              MenuItem("0", "Назад", lambda u: "break")])

    def show_menu(self, _=None):
        while True:
            choice = self.menu.show()
            result = self.menu.execute(choice, None)
            if result == "break":
                break

    def sort_by_name(self, _):
        products = sorted(self.controller.get_all(), key=lambda p: p.name.lower())
        self._print_sorted(products, "Име (A–Z) ↑", "Вградено сортиране")

    # Цена висока - ниска
    def sort_price_desc(self, _):
        products = self.controller.selection_sort()
        self._print_sorted(products, "Цена (висока → ниска)", "Selection Sort")


    def sort_price_asc(self, _):
        products = self.controller.bubble_sort()
        products.reverse()
        self._print_sorted(products, "Цена (ниска → висока)", "Bubble Sort")

    def sort_qty_desc(self, _):
        inv = self.controller.inventory_controller.data["products"]
        products = sorted(self.controller.get_all(),
                          key=lambda p: inv.get(p.product_id, {}).get("total_stock", 0),
                          reverse=True)
        self._print_sorted(products, "Количество (високо → ниско)", "Bubble Sort")

    # Количество ниско - високо
    def sort_qty_asc(self, _):
        inv = self.controller.inventory_controller.data["products"]
        products = sorted(self.controller.get_all(),
                          key=lambda p: inv.get(p.product_id, {}).get("total_stock", 0))
        self._print_sorted(products, "Количество (ниско → високо)", "Selection Sort")


    # Общ метод за визуализация
    def _print_sorted(self, products, title, algorithm):
        if not products:
            print("\n[!] Няма продукти за показване.")
            return

        print(f"\nСортиране по: {title}")
        print(f"Алгоритъм: {algorithm}\n")

        rows = []
        inv = self.controller.inventory_controller.data["products"]

        for p in products:
            stock = inv.get(p.product_id, {}).get("total_stock", 0)
            rows.append([p.name, p.location_id,
                         f"{p.price:.2f} лв.",
                         f"{stock:.2f} {p.unit}"])

        print(format_table(["Име", "Склад", "Цена", "Количество"], rows))
