from views.menu import Menu, MenuItem
from views.product_menu_view import ProductView
from views.category_view import CategoryView
from views.movement_view import MovementView
from views.invoice_view import InvoiceView
from views.reports_menu_view import ReportsView
from views.system_info_view import SystemInfoView
from views.password_utils import require_password


class OperatorMenuView:
    def __init__(self, controllers):
        # Запазвам контролерите като отделни атрибути
        self.product_controller = controllers["product"]
        self.category_controller = controllers["category"]
        self.location_controller = controllers["location"]
        self.movement_controller = controllers["movement"]
        self.invoice_controller = controllers["invoice"]
        self.report_controller = controllers["report"]
        self.user_controller = controllers["user"]
        self.activity_log = controllers["activity_log"]
        self.supplier_controller = controllers.get("supplier")  # ако има доставчици

        # Създавам менюто като отделен метод
        self.menu = self._build_menu()

    # Създаваме менюто отделно
    def _build_menu(self):
        return Menu("Операторско меню", [
            MenuItem("1", "Управление на продукти", self.open_products),
            MenuItem("2", "Управление на категории", self.open_categories),
            MenuItem("3", "Доставки и продажби (IN/OUT движения)", self.open_movements),
            MenuItem("4", "Справки", self.open_reports),
            MenuItem("5", "Фактури", self.open_invoices),
            MenuItem("6", "Информация за системата", self.open_system_info),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    # Основно меню
    def show_menu(self, user):
        if user.role.lower() == "guest":
            print("Нямате достъп до операторското меню.")
            return

        while True:
            choice = self.menu.show()
            result = self.menu.execute(choice, user)
            if result == "break":
                break

    # Помощен метод за отваряне на View
    @staticmethod
    def _open_view(view_class, *args):
        return view_class(*args)

    # Продукти
    def open_products(self, user):
        view = self._open_view(ProductView,self.product_controller, self.category_controller,
                               self.location_controller, self.activity_log)
        view.show_menu(user)

    # Категории — защитено меню
    @require_password("parola123")
    def open_categories(self, user):
        view = self._open_view(CategoryView, self.category_controller)
        view.show_menu(user)

    # Движения — операторът има достъп
    def open_movements(self, user):
        view = self._open_view(MovementView, self.product_controller,
                               self.movement_controller, self.user_controller, self.location_controller,
                               self.supplier_controller)     #  доставчици, ако има
        view.show_menu(user)

    # Справки — защитено меню
    @require_password("parola123")
    def open_reports(self, user):
        view = self._open_view(ReportsView, self.report_controller)
        view.show_menu(user)

    # Фактури — защитено меню
    @require_password("parola123")
    def open_invoices(self, user):
        view = self._open_view(InvoiceView, self.invoice_controller, self.activity_log)
        view.show_menu(user)

    # Информация за системата — публично
    @staticmethod
    def open_system_info(_):
        SystemInfoView().show_menu()
