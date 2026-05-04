from controllers.user_controller import UserController
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from controllers.supplier_controller import SupplierController
from controllers.location_controller import LocationController
from controllers.movement_controller import MovementController
from controllers.invoice_controller import InvoiceController
from controllers.report_controller import ReportController
from controllers.user_activity_log_controller import UserActivityLogController
from controllers.inventory_controller import InventoryController

from views.admin_menu_view import AdminMenuView
from views.operator_menu_view import OperatorMenuView
from views.anonymous_menu_view import AnonymousMenuView
from views.graph_menu_view import GraphView
from views.password_utils import input_password
from storage.json_repository import JSONRepository


class InventoryApplication:
    def __init__(self):
        # Създавам всички хранилища (Model слой)
        self._init_repositories()

        # Създавам всички контролери (Controller слой)
        self._init_controllers()

        # Създавам менюта (View слой)
        self._init_menus()


    # ХРАНИЛИЩА
    def _init_repositories(self):
        self.user_repo = JSONRepository("data/users.json")
        self.product_repo = JSONRepository("data/products.json")
        self.category_repo = JSONRepository("data/categories.json")
        self.supplier_repo = JSONRepository("data/suppliers.json")
        self.location_repo = JSONRepository("data/locations.json")
        self.movement_repo = JSONRepository("data/movements.json")
        self.invoice_repo = JSONRepository("data/invoices.json")
        self.report_repo = JSONRepository("data/reports.json")
        self.inventory_repo = JSONRepository("data/inventory.json")


    # КОНТРОЛЕРИ (Controller)
    def _init_controllers(self):
        # Логове на действията
        self.activity_log_controller = UserActivityLogController(JSONRepository("data/user_activity_log.json"))

        self.user_controller = UserController(self.user_repo)
        self.category_controller = CategoryController(self.category_repo)
        self.supplier_controller = SupplierController(self.supplier_repo)
        self.location_controller = LocationController(self.location_repo)
        self.invoice_controller = InvoiceController(self.invoice_repo)

        # Контролер за продукти – получава нужните зависимости
        self.product_controller = ProductController(self.product_repo, self.category_controller, self.activity_log_controller,
                                                    self.supplier_controller, self.inventory_repo)

        # Контролер за инвентар
        self.inventory_controller = InventoryController(self.inventory_repo, self.product_controller, self.location_controller)

        # Контролер за движения – най-сложният
        self.movement_controller = MovementController(self.movement_repo, self.product_controller, self.user_controller, self.location_controller,
                                                      self.invoice_controller, self.activity_log_controller, self.inventory_controller, self.supplier_controller)

        # Контролер за справки
        self.report_controller = ReportController(self.report_repo, self.product_controller, self.movement_controller,
                                                  self.invoice_controller, self.location_controller,
                                                  self.inventory_controller, self.supplier_controller)

        # Графи (логистика)
        self.logistic_service = GraphView(self.inventory_controller, self.location_controller)

        # Зареждане на инвентара според наличните движения
        if not self.movement_controller.movements:
            print("Няма движения – зареждам началните количества.")
            all_locations = self.location_controller.get_all()
            default_location = all_locations[0].location_id
            self.inventory_controller.auto_seed_initial_stock(default_location)
        else:
            print("Има движения – възстановявам инвентара.")
            self.inventory_controller.rebuild_inventory_from_movements(self.movement_controller.movements)


    # МЕНЮТА (View)
    def _init_menus(self):
        self.controllers = {"user": self.user_controller, "product": self.product_controller,
                            "category": self.category_controller, "supplier": self.supplier_controller,
                            "location": self.location_controller, "movement": self.movement_controller,
                            "invoice": self.invoice_controller, "report": self.report_controller,
                            "activity_log": self.activity_log_controller, "logistic": self.logistic_service,
                            "inventory": self.inventory_controller}


        self.admin_menu = AdminMenuView(self.controllers)
        self.operator_menu = OperatorMenuView(self.controllers)
        self.anonymous_menu = AnonymousMenuView(self.controllers)


    # ПРОЦЕС НА ВХОД
    def _login_flow(self):
        while True:
            try:
                username = input("Потребителско име: ").strip()
                password = input_password("Парола: ")
                user = self.user_controller.login(username, password)
                print(f"\nУспешен вход! Добре дошли, {user.first_name}.\n")

                # Показвам меню според ролята
                if user.role == "Admin":
                    self.admin_menu.show_menu(user)
                elif user.role == "Operator":
                    self.operator_menu.show_menu(user)
                else:
                    print("[!] Невалидна роля.")
                return

            except ValueError as e:
                print(f"[Грешка] {e}\nОпитайте отново.\n")

    # Анонимен достъп (само разглеждане)
    def _anonymous_flow(self):
        guest = self.user_controller.create_anonymous_user()
        self.anonymous_menu.show_menu(guest)



    def run(self):
        while True:
            print("\n=== СИСТЕМА ЗА УПРАВЛЕНИЕ НА СКЛАД ===")
            print("1. Вход")
            print("2. Анонимен достъп")
            print("0. Изход")

            choice = input("Избор: ").strip()

            if choice == "1":
                self._login_flow()
            elif choice == "2":
                self._anonymous_flow()
            elif choice == "0":
                print("Изход от системата.")
                break
            else:
                print("[!] Невалиден избор.")


if __name__ == "__main__":
    app = InventoryApplication()
    app.run()
