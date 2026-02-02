from controllers.user_controller import UserController
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from controllers.supplier_controller import SupplierController
from controllers.location_controller import LocationController
from controllers.stocklog_controller import StockLogController
from controllers.movement_controller import MovementController
from controllers.invoice_controller import InvoiceController

from user_interface.admin_menu import admin_menu
from user_interface.operator_menu import operator_menu
from  user_interface.anonymous_menu import anonymous_menu

from storage.json_repository import JSONRepository


def main():
    # ---------------------------------------------------------
    # Репозитории
    # ---------------------------------------------------------
    user_repo = JSONRepository("data/users.json")
    product_repo = JSONRepository("data/products.json")
    category_repo = JSONRepository("data/categories.json")
    supplier_repo = JSONRepository("data/suppliers.json")
    location_repo = JSONRepository("data/locations.json")
    stocklog_repo = JSONRepository("data/stocklogs.json")
    movement_repo = JSONRepository("data/movements.json")
    invoice_repo = JSONRepository("data/invoices.json")

    # ---------------------------------------------------------
    # Контролери (в правилния ред!)
    # ---------------------------------------------------------
    user_controller = UserController(user_repo)
    category_controller = CategoryController(category_repo)
    supplier_controller = SupplierController(supplier_repo)
    location_controller = LocationController(location_repo)
    stocklog_controller = StockLogController(stocklog_repo)

    product_controller = ProductController(product_repo, category_controller, supplier_controller)

    invoice_controller = InvoiceController(invoice_repo)

    movement_controller = MovementController(
        movement_repo,
        product_controller,
        user_controller,
        location_controller,
        stocklog_controller,
        invoice_controller
    )

    # ---------------------------------------------------------
    # Главен цикъл
    # ---------------------------------------------------------
    while True:
        print("\nВход в системата")
        print("1. Вход с потребител")
        print("2. Вход като гост")
        print("0. Изход")

        choice = input("Избор: ")

        if choice == "1":
            username = input("Потребителско име: ")
            password = input("Парола: ")

            user = user_controller.login(username, password)

            if not user:
                print("Грешно потребителско име или парола.")
                continue

            # ЗАДЪЛЖИТЕЛНО!
            user_controller.logged_user = user

            if user.role == "Admin":
                admin_menu(user)

            elif user.role == "Operator":
                operator_menu(product_controller, category_controller,
                              supplier_controller, movement_controller, invoice_controller)

            else:
                print("Невалидна роля.")
                continue

        elif choice == "2":
            anonymous_menu(product_controller, category_controller)

        elif choice == "0":
            print("Изход от системата.")
            break

        else:
            print("Невалиден избор.")


if __name__ == "__main__":
    main()
