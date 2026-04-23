from views.menu import Menu, MenuItem
from views.system_info_view import SystemInfoView
from views.product_menu_view import ProductView
from views.category_view import CategoryView


class AnonymousMenuView:
    def __init__(self, controllers):
        # Запазвам контролерите, за да ги подадем на под-менютата
        self.controllers = controllers
        # Инициализирам изгледите, които гостът може да достъпва
        self.product_view = ProductView(controllers["product"], controllers["category"], controllers["location"],
                                        controllers["activity_log"])

        self.category_view = CategoryView(controllers["category"])
        self.system_info_view = SystemInfoView()


    # Създавам на менюто
    def _build_menu(self):
        """ Изгражда менюто за анонимен потребител. """
        return Menu("Меню за анонимен потребител", [
            MenuItem("1", "Разглеждане на продукти", self.open_products),
            MenuItem("2", "Разглеждане на категории", self.open_categories),
            MenuItem("3", "Информация за системата", self.show_system_info),
            MenuItem("0", "Назад", lambda u: "break")])

    def show_menu(self, user=None):
        while True:
            # Превръщаме го в динамично меню, за да е в тон с професионалния стил на останалите
            menu = self._build_menu()
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # Гостът може да вижда продуктите;
    # ProductView автоматично крие админ бутоните за роли различни от Admin/Operator
    def open_products(self, user):
        self.product_view.show_menu(user)

    # Гостът може да вижда категориите
    def open_categories(self, user):
        self.category_view.show_menu(user)

    def show_system_info(self, _):
        # Подавам None или празния аргумент, тъй като SystemInfo обикновено не изисква потребител
        self.system_info_view.show_menu()