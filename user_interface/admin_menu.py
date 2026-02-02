from storage.json_repository import JSONRepository

from controllers.category_controller import CategoryController
from controllers.product_controller import ProductController
from controllers.user_controller import UserController
from controllers.invoice_controller import InvoiceController
from controllers.report_controller import ReportController
from controllers.movement_controller import MovementController
from controllers.supplier_controller import SupplierController
from controllers.location_controller import LocationController
from controllers.stocklog_controller import StockLogController

from user_interface.product_menu import product_menu
from user_interface.category_menu import category_menu
from user_interface.movement_menu import movement_menu
from user_interface.user_menu import user_menu
from user_interface.reports_menu import reports_menu
from user_interface.invoice_menu import invoice_menu
from user_interface.system_info_menu import system_info_menu


def admin_menu(user):
    # --- Репота ---
    category_repo = JSONRepository("data/categories.json")
    supplier_repo = JSONRepository("data/suppliers.json")
    product_repo = JSONRepository("data/products.json")
    user_repo = JSONRepository("data/users.json")
    invoice_repo = JSONRepository("data/invoices.json")
    movement_repo = JSONRepository("data/movements.json")
    location_repo = JSONRepository("data/locations.json")
    stocklog_repo = JSONRepository("data/stocklogs.json")
    report_repo = JSONRepository("data/reports.json")

    # --- Контролери ---
    category_controller = CategoryController(category_repo)
    supplier_controller = SupplierController(supplier_repo)

    product_controller = ProductController(
        product_repo,
        category_controller,
        supplier_controller
    )

    user_controller = UserController(user_repo)
    invoice_controller = InvoiceController(invoice_repo)
    location_controller = LocationController(location_repo)
    stocklog_controller = StockLogController(stocklog_repo)

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
        movement_controller,
        invoice_controller
    )

    # --- Меню ---
    while True:
        print("\n=== Администраторско меню ===")
        print("1. Управление на продукти")
        print("2. Управление на категории")
        print("3. Доставки и продажби (IN/OUT движения)")
        print("4. Управление на потребители")
        print("5. Справки")
        print("6. Фактури")
        print("7. Информация за системата")
        print("0. Назад")

        choice = input("Избор: ")

        if choice == "1":
            product_menu(product_controller, category_controller, readonly=False)

        elif choice == "2":
            category_menu(category_controller, readonly=False)

        elif choice == "3":
            # movement_menu изисква (user, movement_controller, user_controller)
            movement_menu(user, movement_controller, user_controller)

        elif choice == "4":

            user_menu(user, user_controller)


        elif choice == "5":
            reports_menu(report_controller)

        elif choice == "6":
            invoice_menu(invoice_controller)

        elif choice == "7":
            system_info_menu()

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
