from controllers.user_controller import UserController
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from controllers.supplier_controller import SupplierController
from controllers.location_controller import LocationController
from controllers.stocklog_controller import StockLogController
from controllers.movement_controller import MovementController
from controllers.invoice_controller import InvoiceController
from controllers.report_controller import ReportController

from views.admin_menu_view import AdminMenuView
from views.operator_menu_view import OperatorMenuView
from views.anonymous_menu_view import AnonymousMenuView

from storage.json_repository import JSONRepository
from datetime import datetime
from models.user import User


def main():

    # Репозитории
    user_repo = JSONRepository("data/users.json")
    product_repo = JSONRepository("data/products.json")
    category_repo = JSONRepository("data/categories.json")
    supplier_repo = JSONRepository("data/suppliers.json")
    location_repo = JSONRepository("data/locations.json")
    stocklog_repo = JSONRepository("data/stocklogs.json")
    movement_repo = JSONRepository("data/movements.json")
    invoice_repo = JSONRepository("data/invoices.json")
    report_repo = JSONRepository("data/reports.json")

    # Контролери
    user_controller = UserController(user_repo)
    category_controller = CategoryController(category_repo)
    supplier_controller = SupplierController(supplier_repo)
    location_controller = LocationController(location_repo)
    stocklog_controller = StockLogController(stocklog_repo)

    product_controller = ProductController(
        product_repo,
        category_controller,
        supplier_controller
    )

    invoice_controller = InvoiceController(invoice_repo)

    movement_controller = MovementController(
        movement_repo,
        product_controller,
        user_controller,
        location_controller,
        stocklog_controller,
        invoice_controller
    )

    report_controller = ReportController(
        report_repo,
        product_controller,
        movement_controller,
        invoice_controller
    )

    # Пакет от контролери за менюта
    controllers = {
        "user": user_controller,
        "product": product_controller,
        "category": category_controller,
        "supplier": supplier_controller,
        "movement": movement_controller,
        "invoice": invoice_controller,
        "report": report_controller
    }

    # Главен цикъл
    while True:
        print("\nВход в системата")
        print("1. Вход с потребител")
        print("2. Вход като анонимен потребител")
        print("0. Изход")

        choice = input("Избор: ")

        # Вход с потребител
        if choice == "1":
            username = input("Потребителско име: ")
            password = input("Парола: ")

            user = user_controller.login(username, password)

            if not user:
                print("Грешно потребителско име или парола.")
                continue

            user_controller.logged_user = user

            if user.role == "Admin":
                AdminMenuView(controllers).show_menu(user)

            elif user.role == "Operator":
                OperatorMenuView(controllers).show_menu(user)

            else:
                print("Невалидна роля.")
                continue

        # Вход като анонимен потребител
        elif choice == "2":
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            guest_user = User(
                user_id="guest-0000",
                first_name="Anonymous",
                last_name="",
                email="",
                username="guest",
                password="",
                role="Anonymous",
                status="Active",
                created=now,
                modified=now
            )

            AnonymousMenuView().show_menu(guest_user)



        # Изход
        elif choice == "0":
            print("Изход от системата.")
            break

        else:
            print("Невалиден избор.")


if __name__ == "__main__":
    main()
