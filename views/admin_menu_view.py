from views.menu import Menu, MenuItem
from views.product_menu_view import ProductView
from views.category_view import CategoryView
from views.movement_view import MovementView
from views.user_view import UserView
from views.reports_menu_view import ReportsView
from views.invoice_view import InvoiceView
from views.supplier_view import SupplierView
from views.system_info_view import SystemInfoView


# Вече няма нужда да импортираме класа GraphView тук,
# защото ще ползваме готовия обект от контролерите.

class AdminMenuView:
    def __init__(self, controllers):
        self.controllers = controllers

    def show_menu(self, user):
        if user.role.lower() != "admin":
            print("Само администратор има достъп до това меню.")
            return

        menu = Menu("Администраторско меню", [
            MenuItem("1", "Управление на продукти", self.open_products),
            MenuItem("2", "Управление на категории", self.open_categories),
            MenuItem("3", "Доставки и продажби (IN/OUT движения)", self.open_movements),
            MenuItem("4", "Управление на потребители", self.open_users),
            MenuItem("5", "Справки", self.open_reports),
            MenuItem("6", "Фактури", self.open_invoices),
            MenuItem("7", "Информация за системата", self.open_system_info),
            MenuItem("8", "Управление на доставчици", self.open_suppliers),
            MenuItem("9", "Най-кратък път между складове (Dijkstra)", self.open_graph),
            MenuItem("0", "Назад", lambda u: "break")
        ])

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # Продукти - КРИТИЧНА КОРЕКЦИЯ: добавен location controller за работа със складове
    def open_products(self, user):
        ProductView(
            self.controllers["product"],
            self.controllers["category"],
            self.controllers["location"], # ТАЗИ ДОБАВКА Е ВАЖНА ЗА СКЛАДОВЕТЕ
            self.controllers["activity_log"]
        ).show_menu(user)

    # Категории
    def open_categories(self, user):
        CategoryView(self.controllers["category"]).show_menu(user)

    # Движения
    def open_movements(self, user):
        MovementView(
            self.controllers["product"],
            self.controllers["movement"],
            self.controllers["user"],
            self.controllers["activity_log"]
        ).show_menu()

    # Потребители
    def open_users(self, user):
        UserView(self.controllers["user"]).show_menu(user)

    # Справки
    def open_reports(self, user):
        ReportsView(self.controllers["report"]).show_menu(user)

    # Фактури
    def open_invoices(self, user):
        InvoiceView(
            self.controllers["invoice"],
            self.controllers["activity_log"]
        ).show_menu(user)

    # Информация за системата
    def open_system_info(self, _):
        SystemInfoView().show_menu()

    # Доставчици
    def open_suppliers(self, user):
        SupplierView(self.controllers["supplier"]).show_menu(user)

    # Dijkstra – най-кратък път (КОРИГИРАН)
    def open_graph(self, user):
        # Вземаме инстанцията на GraphView, която създадохме в main.py
        logistic_module = self.controllers.get("logistic")

        if logistic_module:
            logistic_module.show_menu(user)
        else:
            print("\nГрешка: Логистичният модул (Dijkstra) не е инициализиран.")

# Бележка: Чрез речника 'controllers' постигаме Dependency Injection.
# В метода open_graph вече не създаваме нов обект, а използваме
# съществуващия, който вече има достъп до всички данни.