from controllers.user_controller import UserController
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from controllers.supplier_controller import SupplierController
from controllers.location_controller import LocationController
from controllers.stocklog_controller import StockLogController
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
from datetime import datetime


class InventoryApplication:
    def __init__(self):
        self._init_repositories()   # Инициализация на хранилищата (Repositories)
        self._init_controllers()     #  Инициализация на контролерите
        self._init_menus()           #  Инициализация на менютата

    #  Инициализация на хранилищата
    def _init_repositories(self):
        self.user_repo = JSONRepository("data/users.json")
        self.product_repo = JSONRepository("data/products.json")
        self.category_repo = JSONRepository("data/categories.json")
        self.supplier_repo = JSONRepository("data/suppliers.json")
        self.location_repo = JSONRepository("data/locations.json")
        self.stocklog_repo = JSONRepository("data/stocklogs.json")
        self.movement_repo = JSONRepository("data/movements.json")
        self.invoice_repo = JSONRepository("data/invoices.json")
        self.report_repo = JSONRepository("data/reports.json")
        self.inventory_repo = JSONRepository("data/inventory.json")

    #  Инициализация на контролерите
    def _init_controllers(self):
        self.activity_log_controller = UserActivityLogController("data/user_activity_log.json")
        self.user_controller = UserController(self.user_repo)
        self.category_controller = CategoryController(self.category_repo)
        self.supplier_controller = SupplierController(self.supplier_repo)
        self.location_controller = LocationController(self.location_repo)
        self.stocklog_controller = StockLogController(self.stocklog_repo)
        self.invoice_controller = InvoiceController(self.invoice_repo)
        self.product_controller = ProductController(self.product_repo, self.category_controller,
                                                    self.supplier_controller, self.activity_log_controller)

        # Създаваме InventoryController
        self.inventory_controller = InventoryController(self.inventory_repo)
        #  Ако inventory.json е празен – инициализираме го от продуктите - чрез контролера
        if not self.inventory_controller.stock:
            products = self.product_controller.get_all()
            self.inventory_controller.initialize_from_products(products)

        # MovementController получава inventory_controller
        self.movement_controller = MovementController(self.movement_repo, self.product_controller,
                                                      self.user_controller, self.location_controller,
                                                      self.stocklog_controller, self.invoice_controller,
                                                      self.activity_log_controller, self.inventory_controller)

        # MovementController  получава supplier_controller
        self.movement_controller.attach_supplier_controller(self.supplier_controller)
        self.report_controller = ReportController(self.report_repo, self.product_controller,
                                                  self.movement_controller, self.invoice_controller, self.location_controller)
        #  Автоматично генериране и записване на отчети само веднъж
        initial_reports = self.report_controller.generate_all_reports()
        self.report_controller.save_reports_once(initial_reports)
        # Инициализация на логистичния модул (Dijkstra)
        self.logistic_service = GraphView(self.inventory_controller)

    #  Инициализация на менютата
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

    #  Процес на вход
    def _login_flow(self):
        username = input("Потребителско име: ")
        password = input_password("Парола: ")
        user = self.user_controller.login(username, password)
        if not user:
            print("[!] Грешно потребителско име или парола.")
            return

        self.activity_log_controller.add_log(user.user_id,"LOGIN",f"Потребител {user.username} влезе.")
        if user.role == "Admin":
            self.admin_menu.show_menu(user)
        elif user.role == "Operator":
            self.operator_menu.show_menu(user)
        else:
            print("[!] Невалидна роля на потребителя.")
            return

        self.activity_log_controller.add_log(user.user_id,
                                             "LOGOUT",f"Потребител {user.username} излезе.")

    #  Анонимен достъп
    def _anonymous_flow(self):
        guest_user = self.user_controller.create_anonymous_user()
        self.activity_log_controller.add_log(
            guest_user.user_id,"ANONYMOUS_LOGIN","Анонимен достъп.")

        self.anonymous_menu.show_menu(guest_user)
        self.activity_log_controller.add_log(guest_user.user_id,
                                             "ANONYMOUS_LOGOUT","Анонимен изход.")


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