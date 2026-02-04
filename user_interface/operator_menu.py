from user_interface.product_menu import product_menu
from user_interface.category_menu import category_menu
from user_interface.movement_menu import movement_menu
from user_interface.reports_menu import reports_menu
from user_interface.invoice_menu import invoice_menu
from user_interface.system_info_menu import system_info_menu
from user_interface.product_sort_menu import sorting_menu


def operator_menu(
    user,
    product_controller,
    category_controller,
    supplier_controller,
    movement_controller,
    invoice_controller,
    report_controller,
    user_controller
):

    if user.role.lower() == "guest":
        print("Нямате достъп до операторското меню.")
        return

    while True:
        print("\n=== Операторско меню ===")
        print("1. Управление на продукти")
        print("2. Управление на категории")
        print("3. Доставки и продажби (IN/OUT движения)")
        print("4. Справки")
        print("5. Фактури")
        print("6. Информация за системата")
        print("7. Сортиране на продукти")
        print("0. Назад")

        choice = input("Избор: ")

        if choice == "1":
            product_menu(product_controller, category_controller, readonly=False)

        elif choice == "2":
            category_menu(user, category_controller, readonly=False)

        elif choice == "3":
            movement_menu(product_controller, movement_controller, user_controller)

        elif choice == "4":
            reports_menu(user, report_controller)

        elif choice == "5":
            invoice_menu(user, invoice_controller)

        elif choice == "6":
            system_info_menu()

        elif choice == "7":
            sorting_menu(product_controller)

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
