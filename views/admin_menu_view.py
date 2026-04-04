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

        # Създаваме view обектите
        self.product_view = ProductView(controllers["product"],controllers["category"],controllers["location"],controllers["activity_log"])
        self.category_view = CategoryView(controllers["category"])
        self.movement_view = MovementView(controllers["product"],controllers["movement"],controllers["user"],controllers["activity_log"])
        self.user_view = UserView(controllers["user"])
        self.reports_view = ReportsView(controllers["report"])
        self.invoice_view = InvoiceView(controllers["invoice"], controllers["activity_log"])
        self.supplier_view = SupplierView(controllers["supplier"])
        self.system_info_view = SystemInfoView()

        # Вземаме инстанцията на GraphView, която е в main.py
        self.graph_view = controllers.get("logistic")

    def show_menu(self, user):
        if user.role.lower() != "admin":
            print("Само администратор има достъп до това меню.")
            return

        menu = Menu("Администраторско меню", [MenuItem("1", "Управление на продукти", lambda u: self.product_view.show_menu(u)),
                                              MenuItem("2", "Управление на категории", lambda u: self.category_view.show_menu(u)),
                                              MenuItem("3", "Доставки и продажби (IN/OUT движения)", lambda u: self.movement_view.show_menu()),
                                              MenuItem("4", "Управление на потребители", lambda u: self.user_view.show_menu(u)),
                                              MenuItem("5", "Справки", lambda u: self.reports_view.show_menu(u)),
                                              MenuItem("6", "Фактури", lambda u: self.invoice_view.show_menu(u)),
                                              MenuItem("7", "Информация за системата", lambda u: self.system_info_view.show_menu()),
                                              MenuItem("8", "Управление на доставчици", lambda u: self.supplier_view.show_menu(u)),
                                              MenuItem("9", "Най-кратък път между складове (Dijkstra)", lambda u: self.open_graph(u)),
                                              MenuItem("0", "Назад", lambda u: "break")])

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # Dijkstra – най-кратък път
    def open_graph(self, user):
        # Вземаме инстанцията на GraphView, която създадохме в main.py
        if self.graph_view:
            self.graph_view.show_menu(user)
        else:
            print("\nГрешка: Логистичният модул (Dijkstra) не е инициализиран.")

#  Чрез речника 'controllers' постигаме Dependency Injection.
# В метода open_graph вече не създаваме нов обект, а използваме
# съществуващия, който вече има достъп до всички данни.