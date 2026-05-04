from views.menu import Menu, MenuItem
from views.system_info_view import SystemInfoView
from views.product_menu_view import ProductMenuView
from views.category_view import CategoryView


class AnonymousMenuView:
    def __init__(self, controllers):
        # Запазвам контролерите, за да ги подадем на под-менютата
        self.controllers = controllers

        self.product_view = ProductMenuView(controllers["product"], controllers["category"], controllers["location"],
                                            controllers["inventory"], controllers["supplier"], controllers["activity_log"])

        self.category_view = CategoryView(controllers["category"])
        self.system_info_view = SystemInfoView()

    def _build_menu(self):
        """Изгражда менюто за анонимен потребител. """
        return Menu("Меню за анонимен потребител", [MenuItem("1", "Разглеждане на продукти", self.open_products),
                                                    MenuItem("2", "Разглеждане на категории", self.open_categories),
                                                    MenuItem("3", "Информация за системата", self.show_system_info),
                                                    MenuItem("0", "Назад", lambda u: "break")])


    def show_menu(self, user=None):
        while True:
            menu = self._build_menu()
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break


    # Гостът може да вижда само списъка, без меню
    def open_products(self, user):
        self.product_view.show_all(user)

    # Гостът може да вижда категориите
    def open_categories(self, user):
        self.category_view.show_menu(user)

    def show_system_info(self, _):
        self.system_info_view.show_menu()
