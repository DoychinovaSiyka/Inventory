from views.menu import Menu, MenuItem
from views.system_info_view import SystemInfoView
from views.product_menu_view import ProductMenuView
from views.category_view import CategoryView
from views.movement_view import MovementView
from views.user_view import UserView
from views.invoice_view import InvoiceView
from views.supplier_view import SupplierView
from views.location_view import LocationView
from views.reports_menu_view import ReportsView


class AdminMenuView:
    def __init__(self, user_controller, product_controller, category_controller, supplier_controller, location_controller,
                 movement_controller, invoice_controller, report_controller, inventory_controller, graph_view, movement_view):

        self.user_controller = user_controller
        self.product_controller = product_controller
        self.category_controller = category_controller
        self.supplier_controller = supplier_controller
        self.location_controller = location_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.report_controller = report_controller
        self.inventory_controller = inventory_controller
        self.graph_view = graph_view
        self.movement_view = movement_view

        self.product_view = ProductMenuView(product_controller, category_controller)
        self.category_view = CategoryView(category_controller, product_controller)
        self.user_view = UserView(user_controller)
        self.reports_view = ReportsView(report_controller)
        self.invoice_view = InvoiceView(invoice_controller)
        self.supplier_view = SupplierView(supplier_controller)
        self.system_info_view = SystemInfoView()
        self.location_view = LocationView(location_controller)

    def _build_menu(self):
        return Menu("Администраторско меню", [
            MenuItem("1", "Управление на продукти", lambda u: self.product_view.show_menu(u)),
            MenuItem("2", "Управление на категории", lambda u: self.category_view.show_menu(u)),
            MenuItem("3", "Доставки, продажби и преместване", lambda u: self.movement_view.show_menu(u)),
            MenuItem("4", "Управление на потребители", lambda u: self.user_view.show_menu(u)),
            MenuItem("5", "Отчети", lambda u: self.reports_view.show_menu(u)),
            MenuItem("6", "Фактури", lambda u: self.invoice_view.show_menu(u)),
            MenuItem("7", "Информация за системата", lambda u: self.system_info_view.show_menu()),
            MenuItem("8", "Управление на доставчици", lambda u: self.supplier_view.show_menu(u)),
            MenuItem("9", "Управление на локации", lambda u: self.location_view.show_menu(u)),
            MenuItem("10", "Логистичен модул (Dijkstra)", lambda u: self.graph_view.show_menu(u)),
            MenuItem("0", "Назад", lambda u: "break")])



    def show_menu(self, user):
        if user.role.lower() != "admin":
            print("\nНямате достъп до административните функции.")
            return

        while True:
            menu = self._build_menu()
            choice = menu.show()
            if choice == "0" or choice is None:
                break
            result = menu.execute(choice, user)
            if result == "break":
                break
