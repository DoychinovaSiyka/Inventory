from controllers.user_controller import UserController
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from controllers.supplier_controller import SupplierController
from controllers.location_controller import LocationController
from controllers.stocklog_controller import StockLogController
from controllers.movement_controller import MovementController
from controllers.invoice_controller import InvoiceController
from controllers.report_controller import ReportController

from user_interface.admin_menu import admin_menu
import user_interface.operator_menu
from user_interface.anonymous_menu import anonymous_menu
from user_interface.product_sort_menu import sorting_menu
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

    # Главен цикъл
    while True:
        print("\nВход в системата")
        print("1. Вход с потребител")
        print("2. Вход като гост")
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
                admin_menu(
                    user,
                    user_controller,
                    product_controller,
                    category_controller,
                    supplier_controller,
                    movement_controller,
                    invoice_controller,
                    report_controller
                )

            elif user.role == "Operator":
                user_interface.operator_menu.operator_menu(
                    user,
                    product_controller,
                    category_controller,
                    supplier_controller,
                    movement_controller,
                    invoice_controller,
                    report_controller,
                    user_controller
                )

            else:
                print("Невалидна роля.")
                continue

        # Вход като гост
        elif choice == "2":
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            guest_user = User(
                user_id="guest-0000",
                first_name="Anonymous",
                last_name="",
                email="",
                username="guest",
                password="",
                role="guest",
                status="Active",
                created=now,
                modified=now
            )

            anonymous_menu(guest_user)

        # Изход
        elif choice == "0":
            print("Изход от системата.")
            break

        else:
            print("Невалиден избор.")


if __name__ == "__main__":
    main()
