def reports_menu(user, report_controller):
    while True:
        print("\n=== Справки ===")
        print("1. Справка за наличности")
        print("2. Справка за движения")
        print("3. Справка за продажби")
        print("4. Справка за продажби по клиент")
        print("5. Справка за продажби по продукт")
        print("6. Справка за продажби по дата (ГГГГ-ММ-ДД)")
        print("0. Назад")

        choice = input("Избор: ")

        # --- 1. Наличности ---
        if choice == "1":
            report_controller.report_stock()

        # --- 2. Движения ---
        elif choice == "2":
            print("\n1. Всички движения")
            print("2. По продукт")
            print("3. По тип движение (IN/OUT/MOVE)")
            print("4. По дата (ГГГГ-ММ-ДД)")

            sub = input("Избор: ")

            if sub == "1":
                report_controller.report_movements()

            elif sub == "2":
                keyword = input("Име на продукт: ")
                report_controller.report_movements_by_product(keyword)

            elif sub == "3":
                mtype = input("Тип движение (IN/OUT/MOVE): ").upper()
                report_controller.report_movements_by_type(mtype)

            elif sub == "4":
                date_str = input("Дата (ГГГГ-ММ-ДД): ")
                report_controller.report_movements_by_date(date_str)

            else:
                print("Невалиден избор.")

        # --- 3. Продажби (общо) ---
        elif choice == "3":
            report_controller.report_sales()

        # --- 4. Продажби по клиент ---
        elif choice == "4":
            customer = input("Име на клиент: ")
            report_controller.report_sales_by_customer(customer)

        # --- 5. Продажби по продукт ---
        elif choice == "5":
            product = input("Име на продукт: ")
            report_controller.report_sales_by_product(product)

        # --- 6. Продажби по дата ---
        elif choice == "6":
            date_str = input("Дата (ГГГГ-ММ-ДД): ")
            report_controller.report_sales_by_date(date_str)

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
