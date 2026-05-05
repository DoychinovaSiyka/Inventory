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
        self.controllers = controllers

    def _build_menu(self):
        """ Изгражда структурата на менюто при всяко извикване. """
        return Menu("Главно меню", [
            MenuItem("1", "Продукти", self.open_products),
            MenuItem("2", "Категории", self.open_categories),
            MenuItem("3", "Доставчици", self.open_suppliers),
            MenuItem("4", "Движения", self.open_movements),
            MenuItem("5", "Фактури", self.open_invoices),
            MenuItem("6", "Справки", self.open_reports),
            MenuItem("7", "Потребители", self.open_users),
            MenuItem("8", "Най-кратък път между складове (Dijkstra)", self.open_graph),
            MenuItem("0", "Изход", lambda u: "break")
        ])

    def show_menu(self, user):
        while True:
            current_menu = self._build_menu()
            choice = current_menu.show()
            result = current_menu.execute(choice, user)
            if result == "break":
                break

    # Действия - методи, които отварят съответните под-изгледи (Views)
    def open_products(self, user):
        ProductView(self.controllers["product"], self.controllers["category"],
                    self.controllers["location"], self.controllers["activity_log"]).show_menu(user)

    def open_categories(self, user):
        CategoryView(self.controllers["category"]).show_menu(user)

    def open_suppliers(self, user):
        SupplierView(self.controllers["supplier"]).show_menu(user)

    def open_movements(self, _):
        MovementView(self.controllers["product"], self.controllers["movement"], self.controllers["user"],
                     self.controllers["location"], self.controllers["supplier"]).show_menu()

    def open_invoices(self, user):
        InvoiceView(self.controllers["invoice"]).show_menu(user)

    def open_reports(self, user):
        ReportsView(self.controllers["report"]).show_menu(user)

    def open_users(self, user):
        UserView(self.controllers["user"]).show_menu(user)

    def open_graph(self, _):
        GraphView(self.controllers["graph"]).show_menu()
