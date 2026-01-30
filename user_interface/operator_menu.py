from storage.json_repository import JSONRepository
from controllers.category_controller import CategoryController
from controllers.product_controller import ProductController
from controllers.invoice_controller import InvoiceController
from controllers.report_controller import ReportController

from user_interface.product_menu import product_menu
from user_interface.category_menu import category_menu
from user_interface.movement_menu import movement_menu
from user_interface.reports_menu import reports_menu
from user_interface.invoice_menu import invoice_menu
from user_interface.system_info_menu import system_info_menu
from  controllers.supplier_controller import SupplierController

def operator_menu(user):
    # --- Създаване на контролери ---
    category_repo = JSONRepository("data/categories.json")
    category_controller = CategoryController(category_repo)

    supplier_repo = JSONRepository("data/suppliers.json")
    supplier_controller = SupplierController(supplier_repo)

    product_repo = JSONRepository("data/products.json")
    product_controller = ProductController(product_repo, category_controller, supplier_controller)

    invoice_repo = JSONRepository("data/invoices.json")
    invoice_controller = InvoiceController(invoice_repo)

    report_repo = JSONRepository("data/reports.json")
    report_controller = ReportController(report_repo)

    # --- Меню ---
    while True:
        print("\n=== Операторско меню ===")
        print("1. Управление на продукти")
        print("2. Управление на категории")
        print("3. Доставки и продажби (IN/OUT движения)")
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
            movement_menu(user)

        elif choice == "5":
            reports_menu(user, report_controller)

        elif choice == "6":
            invoice_menu(user, invoice_controller)

        elif choice == "7":
            system_info_menu()

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
