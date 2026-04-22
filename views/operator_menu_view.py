from views.menu import Menu, MenuItem
from views.product_menu_view import ProductView
from views.category_view import CategoryView
from views.movement_view import MovementView
from views.invoice_view import InvoiceView
from views.reports_menu_view import ReportsView
from views.system_info_view import SystemInfoView
from views.password_utils import require_password
from views.location_view import LocationView


class OperatorMenuView:
    def __init__(self, controllers):
        # пазим контролерите, за да може менюто да отваря нужните екрани
        self.product_controller = controllers["product"]
        self.category_controller = controllers["category"]
        self.location_controller = controllers["location"]
        self.movement_controller = controllers["movement"]
        self.invoice_controller = controllers["invoice"]
        self.report_controller = controllers["report"]
        self.user_controller = controllers["user"]
        self.activity_log = controllers["activity_log"]
        self.supplier_controller = controllers.get("supplier")  # може и да няма доставчици


    # структурата на менюто
    def _build_menu(self):
        """ Изгражда структурата на менюто при всяко извикване. """
        return Menu("Операторско меню", [
            MenuItem("1", "Управление на продукти", self.open_products),
            MenuItem("2", "Управление на категории", self.open_categories),
            MenuItem("3", "Доставки и продажби (IN/OUT движения)", self.open_movements),
            MenuItem("4", "Справки", self.open_reports),
            MenuItem("5", "Фактури", self.open_invoices),
            MenuItem("6", "Информация за системата", self.open_system_info),

            # операторът може само да гледа локациите
            MenuItem("7", "Преглед на локации (само за четене)", self.open_locations_readonly),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    # основен цикъл
    def show_menu(self, user):
        if user.role.lower() == "guest":  # гост - няма достъп
            print("Нямате достъп до операторското меню.")
            return

        # Генерираме менюто локално
        menu = self._build_menu()
        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # помощен метод за създаване на view класове
    @staticmethod
    def _open_view(view_class, *args):
        return view_class(*args)

    def open_products(self, user):
        view = self._open_view(ProductView, self.product_controller,
                               self.category_controller, self.location_controller,
                               self.activity_log)
        view.show_menu(user)

    # категории – защитено с парола
    @require_password("parola123")
    def open_categories(self, user):
        view = self._open_view(CategoryView, self.category_controller)
        view.show_menu(user)

    # движения (IN/OUT/MOVE)
    def open_movements(self, user):
        view = self._open_view(MovementView, self.product_controller,
                               self.movement_controller, self.user_controller,
                               self.location_controller, self.supplier_controller)
        view.show_menu(user)

    # справки – също защитено
    @require_password("parola123")
    def open_reports(self, user):
        view = self._open_view(ReportsView, self.report_controller)
        view.show_menu(user)

    # фактури
    @require_password("parola123")
    def open_invoices(self, user):
        view = self._open_view(InvoiceView, self.invoice_controller, self.activity_log)
        view.show_menu(user)

    # локации – само за гледане
    @require_password("parola123")
    def open_locations_readonly(self, user):
        print("\n--- СПИСЪК НА ЛОКАЦИИТЕ (READ-ONLY) ---")

        view = LocationView(self.location_controller)
        view.show_all(user)

        input("\nНатиснете Enter за връщане към менюто...")

    @staticmethod
    def open_system_info(_):
        SystemInfoView().show_menu()