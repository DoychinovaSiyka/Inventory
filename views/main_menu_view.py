from views.menu import Menu, MenuItem
from views.product_menu_view import ProductView
from views.category_view import CategoryView
from views.supplier_view import SupplierView
from views.movement_view import MovementView
from views.invoice_view import InvoiceView
from views.user_view import UserView
from views.reports_view import ReportsView
from views.graph_view import GraphView


class MainMenuView:
    def __init__(self, controllers):
        self.product_controller = controllers["product"]
        self.category_controller = controllers["category"]
        self.supplier_controller = controllers["supplier"]
        self.movement_controller = controllers["movement"]
        self.invoice_controller = controllers["invoice"]
        self.user_controller = controllers["user"]
        self.report_controller = controllers["report"]
        self.graph_controller = controllers["graph"]
        self.menu = self._build_menu()


    def _build_menu(self):
        return Menu("Главно меню", [MenuItem("1", "Продукти", self.open_products),
                                    MenuItem("2", "Категории", self.open_categories),
                                    MenuItem("3", "Доставчици", self.open_suppliers),
                                    MenuItem("4", "Движения", self.open_movements),
                                    MenuItem("5", "Фактури", self.open_invoices),
                                    MenuItem("6", "Справки", self.open_reports),
                                    MenuItem("7", "Потребители", self.open_users),
                                    MenuItem("8", "Най-кратък път между складове (Dijkstra)", self.open_graph),
                                    MenuItem("0", "Изход", lambda u: "break")])


    def show_menu(self, user):
        while True:
            choice = self.menu.show()
            result = self.menu.execute(choice, user)
            if result == "break":
                break


    # Действия - всяко е отделен метод
    def open_products(self, user):
        ProductView(self.product_controller, self.category_controller).show_menu(user)

    def open_categories(self, user):
        CategoryView(self.category_controller).show_menu(user)

    def open_suppliers(self, user):
        SupplierView(self.supplier_controller).show_menu(user)

    def open_movements(self, _):
        MovementView( self.product_controller, self.movement_controller, self.user_controller).show_menu()

    def open_invoices(self, user):
        InvoiceView(self.invoice_controller).show_menu(user)

    def open_reports(self, user):
        ReportsView(self.report_controller).show_menu(user)

    def open_users(self, user):
        UserView(self.user_controller).show_menu(user)

    def open_graph(self, _):
        GraphView(self.graph_controller).show_menu()
