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
        self._init_repositories()
        self._init_controllers()
        self._init_menus()

    #   ИНИЦИАЛИЗАЦИЯ НА ХРАНИЛИЩАТА
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

    #   ИНИЦИАЛИЗАЦИЯ НА КОНТРОЛЕРИТЕ
    def _init_controllers(self):
        # Логове на потребители
        self.activity_log_controller = UserActivityLogController("data/user_activity_log.json")

        # Основни контролери
        self.user_controller = UserController(self.user_repo)
        self.category_controller = CategoryController(self.category_repo)
        self.supplier_controller = SupplierController(self.supplier_repo)
        self.location_controller = LocationController(self.location_repo)
        self.invoice_controller = InvoiceController(self.invoice_repo)


        self.inventory_controller = InventoryController(self.inventory_repo)


        self.product_controller = ProductController(
            self.product_repo,
            self.category_controller,
            self.activity_log_controller
        )
        self.product_controller.supplier_controller = self.supplier_controller
        self.product_controller.inventory_controller = self.inventory_controller


        self.movement_controller = MovementController(
            self.movement_repo,
            self.product_controller,
            self.user_controller,
            self.location_controller,
            self.invoice_controller,
            self.activity_log_controller,
            self.inventory_controller,
            self.supplier_controller
        )

        # Закачам movement_controller към product_controller
        self.product_controller.movement_controller = self.movement_controller

        # ReportController
        self.report_controller = ReportController(
            self.report_repo,
            self.product_controller,
            self.movement_controller,
            self.invoice_controller,
            self.location_controller,
            self.inventory_controller
        )

        # Логистичен модул (Dijkstra)
        self.logistic_service = GraphView(
            self.inventory_controller,
            self.location_controller
        )

    #   ИНИЦИАЛИЗАЦИЯ НА МЕНЮТАТА
    def _init_menus(self):
        self.controllers = {
            "user": self.user_controller,
            "product": self.product_controller,
            "category": self.category_controller,
            "supplier": self.supplier_controller,
            "location": self.location_controller,
            "movement": self.movement_controller,
            "invoice": self.invoice_controller,
            "report": self.report_controller,
            "activity_log": self.activity_log_controller,
            "logistic": self.logistic_service
        }

        self.admin_menu = AdminMenuView(self.controllers)
        self.operator_menu = OperatorMenuView(self.controllers)
        self.anonymous_menu = AnonymousMenuView(self.controllers)

    #   ПРОЦЕС НА ВХОД
    def _login_flow(self):
        while True:
            try:
                username = input("Потребителско име: ").strip()
                password = input_password("Парола: ")
                user = self.user_controller.login(username, password)

                print(f"\nУспешен вход! Добре дошли, {user.first_name}.\n")
                self.activity_log_controller.add_log(
                    user.user_id, "LOGIN", f"Потребител {user.username} влезе."
                )

                if user.role == "Admin":
                    self.admin_menu.show_menu(user)
                elif user.role == "Operator":
                    self.operator_menu.show_menu(user)
                else:
                    print("[!] Невалидна роля на потребителя.")
                    return

                self.activity_log_controller.add_log(
                    user.user_id, "LOGOUT", f"Потребител {user.username} излезе."
                )
                return

            except ValueError as e:
                print(f"\n[!] {e}\nОпитайте отново.\n")

    #   АНОНИМЕН ДОСТЪП
    def _anonymous_flow(self):
        guest_user = self.user_controller.create_anonymous_user()
        self.activity_log_controller.add_log(guest_user.user_id, "ANONYMOUS_LOGIN", "Анонимен достъп.")

        self.anonymous_menu.show_menu(guest_user)

        self.activity_log_controller.add_log(guest_user.user_id, "ANONYMOUS_LOGOUT", "Анонимен изход.")


    def run(self):
        while True:
            print("\n" + "=" * 31)
            print(" СИСТЕМА ЗА УПРАВЛЕНИЕ НА СКЛАД ")
            print("=" * 31)
            print("1. Вход с потребител")
            print("2. Вход като анонимен потребител (разглеждане)")
            print("0. Изход")

            choice = input("\nИзбор: ").strip()
            if choice == "1":
                self._login_flow()
            elif choice == "2":
                self._anonymous_flow()
            elif choice == "0":
                print("Изход от системата. Довиждане!")
                break
            else:
                print("[!] Невалиден избор. Опитайте отново.")


if __name__ == "__main__":
    app = InventoryApplication()
    app.run()
