

from menus.menu import Menu, MenuItem
from views.product_menu_view import ProductView
from views.category_view import CategoryView
from views.movement_view import MovementView
from views.invoice_view import InvoiceView
from views.reports_menu_view import ReportsView
from views.product_sort_view import ProductSortView
from views.system_info_view import SystemInfoView


class OperatorMenuView:
    def __init__(self, controllers):
        self.controllers = controllers

    def show_menu(self, user):
        if user.role.lower() == "guest":
            print("Нямате достъп до операторското меню.")
            return

        menu = Menu("Операторско меню", [
            MenuItem("1", "Управление на продукти", self.open_products),
            MenuItem("2", "Управление на категории", self.open_categories),
            MenuItem("3", "Доставки и продажби (IN/OUT движения)", self.open_movements),
            MenuItem("4", "Справки", self.open_reports),
            MenuItem("5", "Фактури", self.open_invoices),
            MenuItem("6", "Информация за системата", self.open_system_info),
            MenuItem("7", "Сортиране на продукти", self.open_sorting),
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
            self.controllers["category"]
        ).show_menu(user)

    # 2. Категории
    def open_categories(self, user):
        CategoryView(
            self.controllers["category"]
        ).show_menu(user)

    # 3. Движения
    def open_movements(self,_):
        MovementView(
            self.controllers["product"],
            self.controllers["movement"],
            self.controllers["user"]
        ).show_menu()

    # 4. Справки
    def open_reports(self, user):
        ReportsView(
            self.controllers["report"]
        ).show_menu(user)

    # 5. Фактури
    def open_invoices(self, user):
        InvoiceView(
            self.controllers["invoice"]
        ).show_menu(user)

    # 6. Информация за системата
    @staticmethod
    def open_system_info(_):
        SystemInfoView().show_menu()

    # 7. Сортиране
    def open_sorting(self,_ ):
        ProductSortView(
            self.controllers["product"]
        ).show_menu()
