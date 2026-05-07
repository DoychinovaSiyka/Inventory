from views.menu import Menu, MenuItem
from views.product_menu_view import ProductMenuView
from views.category_view import CategoryView
from views.movement_view import MovementView
from views.invoice_view import InvoiceView
from views.reports_menu_view import ReportsView
from views.system_info_view import SystemInfoView
from views.password_utils import require_password
from views.location_view import LocationView


class OperatorMenuView:
    def __init__(self, controllers):
        self.controllers = controllers
        self.product_controller = controllers["product"]
        self.category_controller = controllers["category"]
        self.location_controller = controllers["location"]
        self.movement_controller = controllers["movement"]
        self.invoice_controller = controllers["invoice"]
        self.report_controller = controllers["report"]
        self.user_controller = controllers["user"]
        self.activity_log = controllers["activity_log"]
        self.supplier_controller = controllers["supplier"]
        self.inventory_controller = controllers["inventory"]

    def _build_menu(self):
        return Menu("Операторско меню", [
            MenuItem("1", "Управление на продукти", lambda u: self.open_products(u)),
            MenuItem("2", "Управление на категории", lambda u: self.open_categories(u)),
            MenuItem("3", "Доставки и продажби (IN/OUT)", lambda u: self.open_movements(u)),
            MenuItem("4", "Справки", lambda u: self.open_reports(u)),
            MenuItem("5", "Фактури", lambda u: self.open_invoices(u)),
            MenuItem("6", "Информация за системата", lambda u: self.open_system_info(u)),
            MenuItem("7", "Преглед на локации", lambda u: self.open_locations_readonly(u)),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    def show_menu(self, user):
        if user.role.lower() == "guest":
            print("\nНямате достъп до операторското меню.")
            return

        while True:
            menu = self._build_menu()
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    def open_products(self, user):
        view = ProductMenuView(self.product_controller, self.category_controller,
                               self.inventory_controller, self.movement_controller,
                               self.activity_log)
        view.show_menu(user)

    @require_password("parola123")
    def open_categories(self, user):
        view = CategoryView(self.category_controller)
        view.show_menu(user)

    def open_movements(self, user):
        view = MovementView(self.product_controller, self.movement_controller,
                            self.user_controller, self.location_controller, self.supplier_controller)
        view.show_menu(user)

    @require_password("parola123")
    def open_reports(self, user):
        view = ReportsView(self.report_controller)
        view.show_menu(user)

    @require_password("parola123")
    def open_invoices(self, user):
        view = InvoiceView(self.invoice_controller, self.activity_log)
        view.show_menu(user)

    @require_password("parola123")
    def open_locations_readonly(self, user):
        print("\nСписък на локациите:")
        view = LocationView(self.location_controller)
        view.show_all(user)
        input("\nНатиснете Enter за връщане...")

    def open_system_info(self, _):
        SystemInfoView().show_menu()
