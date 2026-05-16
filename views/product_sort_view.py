from views.menu import Menu, MenuItem

class ProductSortView:
    def __init__(self, product_controller, parent_view):
        self.product_controller = product_controller
        self.parent_view = parent_view



    def show_menu(self, _=None):
        menu = self._build_menu()
        while True:
            choice = menu.show()
            if choice in ("0", None):
                break
            if menu.execute(choice, None) == "break":
                break

    def _build_menu(self):
        return Menu("Сортиране на продукти", [
            MenuItem("1", "По име (A–Z)", self.sort_by_name),
            MenuItem("2", "По цена (висока -> ниска)", self.sort_price_desc),
            MenuItem("3", "По цена (ниска -> висока)", self.sort_price_asc),
            MenuItem("0", "Назад", lambda u: "break")])




    def sort_by_name(self, _):
        products = self.product_controller.get_custom_sort(sort_type="name", algorithm="selection", reverse=False)
        self.parent_view._print_products(products, "Име (A–Z)")


    def sort_price_desc(self, _):
        products = self.product_controller.get_custom_sort(sort_type="price", algorithm="selection", reverse=True)
        self.parent_view._print_products(products, "Цена (висока -> ниска)")



    def sort_price_asc(self, _):
        products = self.product_controller.get_custom_sort(sort_type="price", algorithm="bubble", reverse=False)
        self.parent_view._print_products(products, "Цена (ниска -> висока)")

