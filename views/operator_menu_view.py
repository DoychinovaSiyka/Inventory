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
        # Запазваме контролерите като отделни атрибути
        self.product_controller = controllers["product"]
        self.category_controller = controllers["category"]
        self.location_controller = controllers["location"]
        self.movement_controller = controllers["movement"]
        self.invoice_controller = controllers["invoice"]
        self.report_controller = controllers["report"]
        self.user_controller = controllers["user"]
        self.activity_log = controllers["activity_log"]
        # Създаваме менюто като отделен метод
        self.menu = self._build_menu()

    # Създаваме менюто отделно
    def _build_menu(self):
        return Menu("Операторско меню", [
            MenuItem("1", "Управление на продукти", self.open_products),
            # Управление на категории е административна функция → защитаваме
            MenuItem("2", "Управление на категории", self.open_categories),
            MenuItem("3", "Доставки и продажби (IN/OUT движения)", self.open_movements),
            # Справките съдържат финансови данни - защитаваме
            MenuItem("4", "Справки", self.open_reports),
            # Фактурите съдържат чувствителни данни - защитаваме
            MenuItem("5", "Фактури", self.open_invoices),
            MenuItem("6", "Информация за системата", self.open_system_info),
            MenuItem("0", "Назад", lambda u: "break") ])

    # Основно меню
    def show_menu(self, user):
        # Проверка за достъп (по твоя оригинал)
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

    #  Продукти: Добавен location контролер
    def open_products(self, user):
        view = self._open_view( ProductView,self.product_controller, self.category_controller,
                                self.location_controller, self.activity_log)
        view.show_menu(user)

    #  Категории — операторът може само да ги гледа - защитаваме менюто
    @require_password("parola123")
    def open_categories(self, user):
        view = self._open_view(CategoryView, self.category_controller)
        view.show_menu(user)

    #  Движения — операторът трябва да има достъп - НЕ защитаваме
    def open_movements(self, _):
        view = self._open_view(MovementView,self.product_controller,
                               self.movement_controller, self.user_controller,
                                self.activity_log)
        view.show_menu()

    #  Справки — съдържат финансови данни - защитаваме
    @require_password("parola123")
    def open_reports(self, user):
        view = self._open_view(ReportsView, self.report_controller)
        view.show_menu(user)

    #  Фактури — съдържат чувствителни данни - защитаваме
    @require_password("parola123")
    def open_invoices(self, user):
        view = self._open_view(InvoiceView, self.invoice_controller, self.activity_log)
        view.show_menu(user)

    #  Информация за системата — публична - НЕ защитаваме
    @staticmethod
    def open_system_info(_):
        SystemInfoView().show_menu()
