from user_interface.product_menu import product_menu
from user_interface.category_menu import category_menu
from user_interface.system_info_menu import system_info_menu


def anonymous_menu(
    product_controller,
    category_controller,
    supplier_controller,
    movement_controller,
    invoice_controller,
    report_controller
):
    while True:
        print("\n=== Меню за гост (Анонимен потребител) ===")
        print("1. Преглед на продукти")
        print("2. Преглед на категории")
        print("3. Справки")
        print("7. Информация за системата")
        print("0. Назад")

        choice = input("Избор: ")

        if choice == "1":
            # readonly режим за гост
            product_menu(product_controller, category_controller, readonly=True)

        elif choice == "2":
            # readonly режим за гост
            category_menu(None, category_controller, readonly=True)

        elif choice == "3":
            # пример: справка за наличности
            report = report_controller.report_stock()
            print("\n=== Справка за наличности ===")
            for item in report.data:
                print(item)

        elif choice == "7":
            system_info_menu()

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
