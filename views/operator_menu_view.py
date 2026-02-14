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
        self.controllers = controllers

    def show_menu(self, user):
        if user.role.lower() == "guest":
            print("Нямате достъп до операторското меню.")
            return

        menu = Menu("Операторско меню", [
            MenuItem("1", "Управление на продукти", self.open_products),

            # Управление на категории е административна функция → защитаваме
            MenuItem("2", "Управление на категории", self.open_categories),

            MenuItem("3", "Доставки и продажби (IN/OUT движения)", self.open_movements),

            # Справките съдържат финансови данни → защитаваме
            MenuItem("4", "Справки", self.open_reports),

            # Фактурите съдържат чувствителни данни → защитаваме
            MenuItem("5", "Фактури", self.open_invoices),
            MenuItem("6", "Информация за системата", self.open_system_info),
            MenuItem("0", "Назад", lambda u: "break")
        ])

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # 1. Продукти
    def open_products(self, user):
        ProductView(
            self.controllers["product"],
            self.controllers["category"],
            self.controllers["activity_log"]
        ).show_menu(user)

    # 2. Категории — операторът може само да ги гледа → защитаваме менюто
    @require_password("parola123")
    def open_categories(self, user):
        CategoryView(self.controllers["category"]).show_menu(user)

    # 3. Движения — операторът трябва да има достъп → НЕ защитаваме
    def open_movements(self, _):
        MovementView(
            self.controllers["product"],
            self.controllers["movement"],
            self.controllers["user"],
            self.controllers["activity_log"]
        ).show_menu()

    # 4. Справки — съдържат финансови данни → защитаваме
    @require_password("parola123")
    def open_reports(self, user):
        ReportsView(self.controllers["report"]).show_menu(user)

    # 5. Фактури — съдържат чувствителни данни → защитаваме
    @require_password("parola123")
    def open_invoices(self, user):
        InvoiceView(
            self.controllers["invoice"],
            self.controllers["activity_log"]
        ).show_menu(user)

    # 6. Информация за системата — публична → НЕ защитаваме
    @staticmethod
    def open_system_info(_):
        SystemInfoView().show_menu()
