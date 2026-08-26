from views.menu import Menu, MenuItem
from views.system_info_view import SystemInfoView
from views.product_menu_view import ProductMenuView
from views.category_view import CategoryView
from views.movement_view import MovementView
from views.user_view import UserView
from views.reports_menu_view import ReportsView
from views.invoice_view import InvoiceView
from views.supplier_view import SupplierView
from views.location_view import LocationView




class AdminMenuView:
    def __init__(self, controllers):
        self.controllers = controllers

        self.product_view = ProductMenuView(controllers["product"], controllers["category"])
        self.category_view = CategoryView(controllers["category"], controllers["product"])

        self.movement_view = MovementView(controllers["product"], controllers["movement"],
                                          controllers["user"], controllers["location"],
                                          controllers["supplier"], controllers["inventory"])

        self.user_view = UserView(controllers["user"])
        self.reports_view = ReportsView(controllers["report"])
        self.invoice_view = InvoiceView(controllers["invoice"])
        self.supplier_view = SupplierView(controllers["supplier"])
        self.system_info_view = SystemInfoView()
        self.location_view = LocationView(controllers["location"])

        self.graph_view = controllers.get("graph")




    def _build_menu(self):
        return Menu("Администраторско меню", [
            MenuItem("1", "Управление на продукти", self.product_view.show_menu),
            MenuItem("2", "Управление на категории", self.category_view.show_menu),
            MenuItem("3", "Доставки, продажби и преместване", self.movement_view.show_menu),
            MenuItem("4", "Управление на потребители", self.user_view.show_menu),
            MenuItem("5", "Отчети", self.reports_view.show_menu),
            MenuItem("6", "Фактури", self.invoice_view.show_menu),
            MenuItem("7", "Информация за системата", lambda u: self.system_info_view.show_menu()),
            MenuItem("8", "Управление на доставчици", self.supplier_view.show_menu),
            MenuItem("9", "Управление на локации", self.location_view.show_menu),
            MenuItem("10", "Логистичен модул (Dijkstra)", self.open_graph),
            MenuItem("0", "Назад", lambda u: "break")])



    def show_menu(self, user):
        if user.role.lower() != "admin":
            print("\nНямате достъп до административните функции.")
            return

        while True:
            menu = self._build_menu()
            choice = menu.show()

            if choice == "0" or choice is None:
                return

            result = menu.execute(choice, user)
            if result == "break":
                return



    def open_graph(self, user):
        if self.graph_view:
            self.graph_view.show_menu(user)
        else:
            print("\nЛогистичният модул не е наличен.")

