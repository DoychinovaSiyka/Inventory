def reports_menu(user, report_controller):
    while True:
        print("\n=== Справки ===")
        print("1. Справка за наличности")
        print("2. Справка за движения")
        print("3. Справка за продажби")
        print("0. Назад")

        choice = input("Избор: ")

        if choice == "1":
            report_controller.report_stock()

        elif choice == "2":
            report_controller.report_movements()

        elif choice == "3":
            report_controller.report_sales()

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
