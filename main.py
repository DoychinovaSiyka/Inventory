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

from storage.json_repository import JSONRepository
from datetime import datetime
from models.user import User


def main():

    user_repo = JSONRepository("data/users.json")
    product_repo = JSONRepository("data/products.json")
    category_repo = JSONRepository("data/categories.json")
    supplier_repo = JSONRepository("data/suppliers.json")
    location_repo = JSONRepository("data/locations.json")
    stocklog_repo = JSONRepository("data/stocklogs.json")
    movement_repo = JSONRepository("data/movements.json")
    invoice_repo = JSONRepository("data/invoices.json")
    report_repo = JSONRepository("data/reports.json")

    # логове
    activity_log_controller = UserActivityLogController("data/user_activity_log.json")

    # контролери
    user_controller = UserController(user_repo)

    # добавяме тестов потребител (ако вече го има → игнорираме)
    try:
        user_controller.register("Ivan", "Petrov", "ivan@example.com", "ivan",
                                 "test123", "Operator")
    except ValueError:
        pass

    category_controller = CategoryController(category_repo)
    supplier_controller = SupplierController(supplier_repo)
    location_controller = LocationController(location_repo)
    stocklog_controller = StockLogController(stocklog_repo)

    product_controller = ProductController(product_repo, category_controller,
                                           supplier_controller, activity_log_controller)

    invoice_controller = InvoiceController(invoice_repo)

    movement_controller = MovementController(
        movement_repo, product_controller, user_controller,
        location_controller, stocklog_controller, invoice_controller,activity_log_controller)

    report_controller = ReportController(report_repo, product_controller, movement_controller,
        invoice_controller, location_controller)

    controllers = {
        "user": user_controller, "product": product_controller,
        "category": category_controller, "supplier": supplier_controller,
        "movement": movement_controller, "invoice": invoice_controller,
        "report": report_controller, "activity_log": activity_log_controller
    }

    # главен цикъл
    while True:
        print("\nВход в системата")
        print("1. Вход с потребител")
        print("2. Вход като анонимен потребител")
        print("0. Изход")

        choice = input("Избор: ")

        if choice == "1":
            username = input("Потребителско име: ")
            user = user_controller.login(username)

            if not user:
                print("Грешно потребителско име или парола.")
                continue

            user_controller.logged_user = user
            activity_log_controller.add_log(user.user_id, "LOGIN",
                                            f"{user.username} logged in")

            if user.role == "Admin":
                AdminMenuView(controllers).show_menu(user)
            elif user.role == "Operator":
                OperatorMenuView(controllers).show_menu(user)
            else:
                print("Невалидна роля.")
                continue

            activity_log_controller.add_log(user.user_id, "LOGOUT",
                                            f"{user.username} logged out")

        elif choice == "2":
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            guest_user = User(user_id="guest-0000", first_name="Anonymous", last_name="",
                email="", username="guest", password="",
                role="Anonymous", status="Active", created=now, modified=now)

            activity_log_controller.add_log(guest_user.user_id, "ANONYMOUS_LOGIN",
                                            "Anonymous entered")

            AnonymousMenuView().show_menu(guest_user)

            activity_log_controller.add_log(guest_user.user_id, "ANONYMOUS_LOGOUT",
                                            "Anonymous exited")

        elif choice == "0":
            print("Изход от системата.")
            break

        else:
            print("Невалиден избор.")


if __name__ == "__main__":
    main()
