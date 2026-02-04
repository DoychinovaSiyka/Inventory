from user_interface.product_menu import product_menu
from user_interface.category_menu import category_menu
from user_interface.movement_menu import movement_menu
from user_interface.user_menu import user_menu
from user_interface.reports_menu import reports_menu
from user_interface.invoice_menu import invoice_menu
from user_interface.system_info_menu import system_info_menu

# правилно добавено меню за доставчици
from user_interface.supplier_menu import supplier_menu


def admin_menu(
    user,
    user_controller,
    product_controller,
    category_controller,
    supplier_controller,
    movement_controller,
    invoice_controller,
    report_controller
):

    if user.role.lower() != "admin":
        print("Само администратор има достъп до това меню.")
        return

    while True:
        print("\n=== Администраторско меню ===")
        print("1. Управление на продукти")
        print("2. Управление на категории")
        print("3. Доставки и продажби (IN/OUT движения)")
        print("4. Управление на потребители")
        print("5. Справки")
        print("6. Фактури")
        print("7. Информация за системата")
        print("8. Управление на доставчици")   # ← добавено
        print("0. Назад")

        choice = input("Избор: ")

        if choice == "1":
            product_menu(product_controller, category_controller, readonly=False)

        elif choice == "2":
            category_menu(user, category_controller, readonly=False)

        elif choice == "3":
            movement_menu(product_controller, movement_controller, user_controller)

        elif choice == "4":
            user_menu(user, user_controller)

        elif choice == "5":
            reports_menu(user, report_controller)

        elif choice == "6":
            invoice_menu(user, invoice_controller)

        elif choice == "7":
            system_info_menu()

        elif choice == "8":
            supplier_menu(user, supplier_controller)   # ← поправено извикване

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
