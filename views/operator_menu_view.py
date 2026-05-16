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
        self.supplier_controller = controllers["supplier"]
        self.inventory_controller = controllers["inventory"]


    def _build_menu(self):
        return Menu("Операторско меню", [
            MenuItem("1", "Управление на продукти (защитено)", self.open_products),
            MenuItem("2", "Управление на категории (защитено)", self.open_categories),
            MenuItem("3", "Доставки и продажби (IN/OUT)", self.open_movements),
            MenuItem("4", "Справки и анализи (защитено)", self.open_reports),
            MenuItem("5", "Архив фактури (защитено)", self.open_invoices),
            MenuItem("6", "Информация за системата", self.open_system_info),
            MenuItem("7", "Преглед на складови локации", self.open_locations_readonly),
            MenuItem("0", "Изход", lambda u: "break")])


    def show_menu(self, user):
        if user is None or not user.role:
            print("\nНеуспешно разпознаване на потребител.")
            return

        if user.role.lower() == "guest":
            print("\nНямате достъп до операторския модул.")
            return

        while True:
            menu = self._build_menu()
            choice = menu.show()

            if choice == "0" or choice is None:
                break

            result = menu.execute(choice, user)
            if result == "break":
                break

    @require_password("parola123")
    def open_products(self, user):
        view = ProductMenuView(self.product_controller, self.category_controller)
        view.show_menu(user)


    @require_password("parola123")
    def open_categories(self, user):
        view = CategoryView(self.category_controller, self.product_controller)
        view.show_menu(user)


    @require_password("parola123")
    def open_reports(self, user):
        view = ReportsView(self.report_controller)
        view.show_menu(user)

    @require_password("parola123")
    def open_invoices(self, user):
        view = InvoiceView(self.invoice_controller)
        view.show_menu(user)

    # СВОБОДЕН ДОСТЪП
    def open_movements(self, user):
        view = MovementView(self.product_controller, self.movement_controller,
                            self.user_controller, self.location_controller, self.supplier_controller, self.inventory_controller)
        view.show_menu(user)

    def open_locations_readonly(self, user):
        print("\nСкладови локации:")
        view = LocationView(self.location_controller)
        view.show_all(user)


    def open_system_info(self, _):
        SystemInfoView().show_menu()