from views.menu import Menu, MenuItem
from views.system_info_view import SystemInfoView
from views.product_menu_view import ProductMenuView
from views.category_view import CategoryView


class AnonymousMenuView:
    def __init__(self, controllers):
        self.controllers = controllers

        self.product_view = ProductMenuView(controllers["product"], controllers["category"])
        self.category_view = CategoryView(controllers["category"], controllers["product"])
        self.system_info_view = SystemInfoView()




    def _build_menu(self):
        return Menu("Меню за анонимен потребител", [
            MenuItem("1", "Разглеждане на продукти", self.open_products),
            MenuItem("2", "Разглеждане на категории", self.open_categories),
            MenuItem("3", "Информация за системата", self.show_system_info),
            MenuItem("0", "Назад", lambda u: "break")])


    def show_menu(self, user=None):
        while True:
            menu = self._build_menu()
            choice = menu.show()

            if choice == "0" or choice is None:
                return

            result = menu.execute(choice, user)
            if result == "break":
                return



    def open_products(self, _):
        self.product_view.show_all(None)



    def open_categories(self, _):
        self.category_view.show_menu(None)



    def show_system_info(self, _):
        self.system_info_view.show_menu()
