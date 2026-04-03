from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.product_controller import ProductController


class ProductSortView:
    def __init__(self, controller: ProductController):
        self.controller = controller

    # паролата се контролира само от productview.sort_menu_protected
    def show_menu(self, _=None):
        menu = Menu("Сортиране на продукти", [
            MenuItem("1", "По име (A–Z) – вградено сортиране", self.sort_by_name),
            MenuItem("2", "По цена (висока → ниска) – selection sort", self.sort_price_desc),
            MenuItem("3", "По цена (ниска → висока) – bubble sort", self.sort_price_asc),
            MenuItem("4", "По количество (високо → ниско) – bubble sort", self.sort_qty_desc),
            MenuItem("5", "По количество (ниско → високо) – selection sort", self.sort_qty_asc),
            MenuItem("0", "Назад", lambda u: "break")])

        while True:
            choice = menu.show()
            result = menu.execute(choice, None)
            if result == "break":
                break

    # 1. по име
    def sort_by_name(self, _):
        products = self.controller.sort_by_name()
        self._print_sorted(products, "Име (A–Z) ↑", "Вградено сортиране")

    # 2. цена (DESC)
    def sort_price_desc(self, _):
        # Използваме selection_sort от контролера с параметри
        products = self.controller.selection_sort(criteria="price", reverse=True)
        self._print_sorted(products, "Цена (висока → ниска)", "Selection Sort")

    # 3. цена (ASC)
    def sort_price_asc(self, _):
        # Използваме bubble_sort от контролера с параметри
        products = self.controller.bubble_sort(criteria="price", reverse=False)
        self._print_sorted(products, "Цена (ниска → висока)", "Bubble Sort")

    # 4. количество (DESC)
    def sort_qty_desc(self, _):
        # Вече не ползваме .sort() тук, а директно алгоритъма от контролера
        products = self.controller.bubble_sort(criteria="quantity", reverse=True)
        self._print_sorted(products, "Количество (високо → ниско)", "Bubble Sort")

    # 5. количество (ASC)
    def sort_qty_asc(self, _):
        # Вече не ползваме .sort() тук, а директно алгоритъма от контролера
        products = self.controller.selection_sort(criteria="quantity", reverse=False)
        self._print_sorted(products, "Количество (ниско → високо)", "Selection Sort")

    # общ метод за печат - ДОБАВЕНА КОЛОНА "СКЛАД"
    @staticmethod
    def _print_sorted(products, title, algorithm):
        if not products:
            print("\n[!] Няма продукти за показване.")
            return

        print(f"\n=== Сортиране по: {title} ===")
        print(f"Алгоритъм: {algorithm}\n")

        # Добавяме p.location_id в редовете, за да виждаме в кой склад е стоката
        rows = []
        for p in products:
            rows.append([p.name.ljust(20), p.location_id, f"{p.price:.2f} лв.",f"{p.quantity} {p.unit}"])

        # Обновяваме заглавията на колоните
        print(format_table(["Име", "Склад", "Цена", "Количество"], rows))