from views.menu import Menu, MenuItem
from views.system_info_view import SystemInfoView
from views.product_menu_view import ProductView
from views.category_view import CategoryView

class AnonymousMenuView:
    def __init__(self, controllers):
        # Запазваме контролерите, за да ги подадем на под-менютата
        self.controllers = controllers

    def show_menu(self, user=None):
        menu = Menu("Меню за анонимен потребител", [
            MenuItem("1", "Разглеждане на продукти", self.open_products),
            MenuItem("2", "Разглеждане на категории", self.open_categories),
            MenuItem("3", "Информация за системата", self.show_system_info),
            MenuItem("0", "Назад", lambda u: "break")
        ])

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # Гостът може да вижда продуктите (ProductView автоматично крие админ бутоните за роли различни от Admin/Operator)
    def open_products(self, user):
        ProductView(self.controllers["product"],self.controllers["category"],self.controllers["location"],
                    self.controllers["activity_log"]).show_menu(user)

    # Гостът може да вижда категориите
    def open_categories(self, user):
        CategoryView(self.controllers["category"]).show_menu(user)

    @staticmethod
    def show_system_info(_):
        SystemInfoView().show_menu()