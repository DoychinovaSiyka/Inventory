import sys

from controllers.user_controller import UserController
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from controllers.supplier_controller import SupplierController
from controllers.location_controller import LocationController
from controllers.movement_controller import MovementController
from controllers.invoice_controller import InvoiceController
from controllers.report_controller import ReportController
from controllers.inventory_controller import InventoryController

from views.admin_menu_view import AdminMenuView
from views.operator_menu_view import OperatorMenuView
from views.anonymous_menu_view import AnonymousMenuView
from views.graph_menu_view import GraphView
from views.movement_view import MovementView
from views.password_utils import input_password

from storage.json_repository import JSONStorage







class InventoryApplication:
    def __init__(self):
        self._init_model()
        self._init_controllers()
        self._init_views()


    # MODEL LAYER
    def _init_model(self):
        self.user_repo = JSONStorage("data/users.json")
        self.product_repo = JSONStorage("data/products.json")
        self.category_repo = JSONStorage("data/categories.json")
        self.supplier_repo = JSONStorage("data/suppliers.json")
        self.location_repo = JSONStorage("data/locations.json")
        self.movement_repo = JSONStorage("data/movements.json")
        self.invoice_repo = JSONStorage("data/invoices.json")
        self.inventory_repo = JSONStorage("data/inventory.json")


    # CONTROLLER LAYER
    def _init_controllers(self):
        self.user_controller = UserController(self.user_repo)
        self.category_controller = CategoryController(self.category_repo)
        self.supplier_controller = SupplierController(self.supplier_repo)
        self.location_controller = LocationController(self.location_repo)

        self.product_controller = ProductController(self.product_repo, self.category_controller)

        self.movement_controller = MovementController(self.movement_repo, self.product_controller,
                                                      self.user_controller, self.location_controller, self.supplier_controller)


        self.inventory_controller = InventoryController(self.inventory_repo, self.product_controller, self.location_controller)


        self.movement_controller.set_inventory_controller(self.inventory_controller)

        self.invoice_controller = InvoiceController(self.invoice_repo)

        self.report_controller = ReportController(self.category_controller, self.product_controller,
                                                  self.inventory_controller, self.movement_controller, self.supplier_controller,
                                                  self.location_controller, self.invoice_controller)

        self.movement_controller.set_report_controller(self.report_controller)


    # VIEW LAYER
    def _init_views(self):
        self.graph_view = GraphView(self.inventory_controller, self.location_controller, self.product_controller)

        self.movement_view = MovementView(self.product_controller, self.movement_controller, self.user_controller,
                                          self.location_controller, self.supplier_controller, self.inventory_controller)


        self.admin_menu = AdminMenuView(user_controller=self.user_controller, product_controller=self.product_controller,
                                        category_controller=self.category_controller, supplier_controller=self.supplier_controller,
                                        location_controller=self.location_controller, movement_controller=self.movement_controller,
                                        invoice_controller=self.invoice_controller, report_controller=self.report_controller,
                                        inventory_controller=self.inventory_controller, graph_view=self.graph_view,
                                        movement_view=self.movement_view)



        self.operator_menu = OperatorMenuView(user_controller=self.user_controller, product_controller=self.product_controller,
                                              category_controller=self.category_controller,
                                              supplier_controller=self.supplier_controller, location_controller=self.location_controller,
                                              movement_controller=self.movement_controller, invoice_controller=self.invoice_controller,
                                              report_controller=self.report_controller, inventory_controller=self.inventory_controller,
                                              graph_view=self.graph_view, movement_view=self.movement_view)



        self.anonymous_menu = AnonymousMenuView(report_controller=self.report_controller, inventory_controller=self.inventory_controller,
                                                movement_controller=self.movement_controller)





    def _login_flow(self):
        while True:
            print("\n-----------------------------------------------------------")
            print("\nВХОД В СИСТЕМАТА")
            username = input("Потребителско име (Enter за връщане): ").strip()
            if not username:
                break

            password = input_password("Парола: ")
            try:
                user = self.user_controller.login(username, password)
                print(f"\nДобре дошли, {user.first_name}. Роля: {user.role}")

                if user.role == "Admin":
                    self.admin_menu.show_menu(user)
                elif user.role == "Operator":
                    self.operator_menu.show_menu(user)
                else:
                    print("Непозната роля.")
                break

            except ValueError as e:
                print(f"\nГрешка при вход: {e}")
                print("Опитайте отново.\n")




    def _anonymous_flow(self):
        guest = self.user_controller.create_anonymous_user()
        print("\nВлизане като Гост (Само за преглед)...")
        self.anonymous_menu.show_menu(guest)




    def run(self):
        while True:
            print("\n-----------------------------------------------------------\n")
            print("\n   СКЛАДОВА СИСТЕМА   ")
            print("1. Вход")
            print("2. Анонимен достъп (само преглед)")
            print("0. Изход")

            choice = input("\nВашият избор: ").strip()
            if choice == "1":
                self._login_flow()
            elif choice == "2":
                self._anonymous_flow()
            elif choice == "0":
                print("\nДовиждане!")
                sys.exit()
            else:
                print("\nНевалиден избор. Опитайте пак.")


if __name__ == "__main__":
    try:
        app = InventoryApplication()
        app.run()
    except KeyboardInterrupt:
        print("\n\nПрограмата е прекъсната ръчно.")
        sys.exit()
    except Exception as e:
        print(f"\nГрешка при стартиране: {e}")
        sys.exit(1)
