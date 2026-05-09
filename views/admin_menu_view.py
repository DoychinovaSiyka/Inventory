from views.menu import Menu, MenuItem
from views.system_info_view import SystemInfoView
from views.product_menu_view import ProductMenuView
from views.category_view import CategoryView
from views.movement_view import MovementView
from views.user_view import UserView
from views.reports_menu_view import ReportsView
from views.invoice_view import InvoiceView
from views.supplier_view import SupplierView
from views.location_view import LocationView


class AdminMenuView:
    def __init__(self, controllers):
        self.controllers = controllers
        self.inventory_controller = controllers["inventory"]
        self.movement_controller = controllers["movement"]

        # Инициализация на под-изгледите (Views)
        # 1. Продукти
        self.product_view = ProductMenuView(
            controllers["product"],
            controllers["category"],
            controllers["inventory"],
            controllers["movement"]
        )

        # 2. Категории
        self.category_view = CategoryView(controllers["category"])

        # 3. Движения (Movement) - ТУК Е ВАЖНАТА КОРЕКЦИЯ (добавен е inventory_controller)
        self.movement_view = MovementView(
            controllers["product"],
            controllers["movement"],
            controllers["user"],
            controllers["location"],
            controllers["supplier"],
            controllers["inventory"]  # <--- Вече съвпада с дефиницията в MovementView
        )

        # 4. Останалите изгледи
        self.user_view = UserView(controllers["user"])
        self.reports_view = ReportsView(controllers["report"])
        self.invoice_view = InvoiceView(controllers["invoice"])
        self.supplier_view = SupplierView(controllers["supplier"])
        self.system_info_view = SystemInfoView()
        self.location_view = LocationView(controllers["location"])

        # 5. Логистичен модул (Graph)
        self.graph_view = controllers.get("graph")  # Сменено на "graph", за да съвпада с main.py

    def _build_menu(self):
        return Menu("Администраторско меню", [
            MenuItem("1", "Управление на продукти", lambda u: self.product_view.show_menu(u)),
            MenuItem("2", "Управление на категории", lambda u: self.category_view.show_menu(u)),
            MenuItem("3", "Доставки и продажби (Логистика)", lambda u: self.movement_view.show_menu(u)),
            MenuItem("4", "Управление на потребители", lambda u: self.user_view.show_menu(u)),
            MenuItem("5", "Справки и отчети", lambda u: self.reports_view.show_menu(u)),
            MenuItem("6", "Фактури", lambda u: self.invoice_view.show_menu(u)),
            MenuItem("7", "Информация за системата", lambda u: self.system_info_view.show_menu()),
            MenuItem("8", "Управление на доставчици", lambda u: self.supplier_view.show_menu(u)),
            MenuItem("9", "Управление на локации", lambda u: self.location_view.show_menu(u)),
            MenuItem("10", "Най-кратък път (Dijkstra)", lambda u: self.open_graph(u)),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    def show_menu(self, user):
        # Проверка за права (Admin)
        if user.role.lower() != "admin":
            print("\n[Грешка] Нямате достъп до административни функции.")
            return

        while True:
            current_menu = self._build_menu()
            choice = current_menu.show()

            if choice == "0" or choice is None:
                break

            result = current_menu.execute(choice, user)
            if result == "break":
                break

    def open_graph(self, user):
        """Отваря модула за оптимизация на пътищата."""
        if self.graph_view:
            self.graph_view.show_menu()  # GraphView обикновено не изисква user обекта
        else:
            print("\n[!] Логистичният модул не е наличен.")