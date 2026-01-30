from storage.json_repository import JSONRepository
from controllers.category_controller import CategoryController
from controllers.product_controller import ProductController

from user_interface.product_menu import product_menu
from user_interface.category_menu import category_menu
from user_interface.system_info_menu import system_info_menu
from controllers.supplier_controller import SupplierController

def anonymous_menu(user):
    # --- Създаване на контролери ---
    category_repo = JSONRepository("data/categories.json")
    category_controller = CategoryController(category_repo)

    supplier_repo = JSONRepository("data/suppliers.json")
    supplier_controller = SupplierController(supplier_repo)

    product_repo = JSONRepository("data/products.json")
    product_controller = ProductController(product_repo, category_controller, supplier_controller)

    # --- Меню ---
    while True:
        print("\n=== Меню за гост (Анонимен потребител) ===")
        print("1. Преглед на продукти")
        print("2. Преглед на категории")
        print("7. Информация за системата")
        print("0. Назад")

        choice = input("Избор: ")

        if choice == "1":
            product_menu(product_controller, category_controller, readonly=True)

        elif choice == "2":
            category_menu(category_controller, readonly=True)

        elif choice == "7":
            system_info_menu()

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
