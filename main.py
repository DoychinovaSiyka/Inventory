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

from views.admin_menu_view import AdminMenuView
from views.operator_menu_view import OperatorMenuView
from views.anonymous_menu_view import AnonymousMenuView
from views.graph_menu_view import GraphView

from storage.json_repository import JSONRepository
from datetime import datetime
from models.user import User


class Application:
    def __init__(self):
        #  Инициализация на хранилищата (Repositories)
        self._init_repositories()

        #  Инициализация на контролерите
        self._init_controllers()
        #  Инициализация на менютата
        self._init_menus()


    # Инициализация на хранилищата
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


    # Инициализация на контролерите
    def _init_controllers(self):
        self.activity_log_controller = UserActivityLogController("data/user_activity_log.json")
        self.user_controller = UserController(self.user_repo)
        self.category_controller = CategoryController(self.category_repo)
        self.supplier_controller = SupplierController(self.supplier_repo)
        self.location_controller = LocationController(self.location_repo)
        self.stocklog_controller = StockLogController(self.stocklog_repo)
        self.invoice_controller = InvoiceController(self.invoice_repo)

        # Регистрация на служебен оператор (ако липсва)
        try:
            self.user_controller.register("Ivan", "Petrov", "ivan@example.com",
                                          "ivan", "test123", "Operator")
        except ValueError:
            pass

        # ProductController се нуждае от категории и доставчици за филтриране
        self.product_controller = ProductController(self.product_repo, self.category_controller, self.supplier_controller,
                                                    self.activity_log_controller)

        self.movement_controller = MovementController( self.movement_repo, self.product_controller, self.user_controller, self.location_controller, self.stocklog_controller,
                                                       self.invoice_controller, self.activity_log_controller)

        self.report_controller = ReportController(self.report_repo, self.product_controller, self.movement_controller,
                                                  self.invoice_controller, self.location_controller)

        # Инициализация на логистичния модул (Dijkstra)
        self.logistic_service = GraphView(self.product_controller)


    # Инициализация на менютата
    def _init_menus(self):
        #  Речник с контролери (Dependency Injection за менютата)
        self.controllers = {
            "user": self.user_controller,
            "product": self.product_controller,
            "category": self.category_controller,
            "supplier": self.supplier_controller,
            "location": self.location_controller,  # нужно за избора на склад в ProductView
            "movement": self.movement_controller,
            "invoice": self.invoice_controller,
            "report": self.report_controller, "activity_log": self.activity_log_controller, "logistic": self.logistic_service }

        self.admin_menu = AdminMenuView(self.controllers)
        self.operator_menu = OperatorMenuView(self.controllers)
        self.anonymous_menu = AnonymousMenuView(self.controllers)


    # Процес на вход
    def _login_flow(self):
        username = input("Потребителско име: ")
        user = self.user_controller.login(username)

        if not user:
            print("[!] Грешно потребителско име или несъществуващ потребител.")
            return

        # Записваме лог за влизане
        self.activity_log_controller.add_log(user.user_id, "LOGIN",
                                             f"Потребител {user.username} влезе.")

        # Избор на меню според ролята
        if user.role == "Admin":
            self.admin_menu.show_menu(user)
        elif user.role == "Operator":
            self.operator_menu.show_menu(user)
        else:
            print("[!] Невалидна роля на потребителя.")
            return

        # Записваме лог за излизане
        self.activity_log_controller.add_log(user.user_id, "LOGOUT",
                                             f"Потребител {user.username} излезе.")


    # Анонимен достъп
    def _anonymous_flow(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        guest_user = User( user_id="guest-0000", first_name="Anonymous", last_name="", email="", username="guest",
                           password="", role="Anonymous", status="Active", created=now, modified=now )

        self.activity_log_controller.add_log(guest_user.user_id, "ANONYMOUS_LOGIN",
                                             "Анонимен достъп.")
        self.anonymous_menu.show_menu(guest_user)
        self.activity_log_controller.add_log(guest_user.user_id, "ANONYMOUS_LOGOUT",
                                             "Анонимен изход.")

    # Главен цикъл
    def run(self):
        while True:
            print("\n" + "=" * 30)
            print(" СИСТЕМА ЗА УПРАВЛЕНИЕ НА СКЛАД ")
            print("=" * 30)
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
    app = Application()
    app.run()
