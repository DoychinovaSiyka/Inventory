from storage.password_utils import format_table

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
            report = report_controller.report_stock()
            rows = [
                [item["product"], item["quantity"], item["price"], item["location"]]
                for item in report.data
            ]
            print(format_table(["Продукт", "Количество", "Цена", "Локация"], rows))

        # --- 2. Движения ---
        elif choice == "2":
            print("\n1. Всички движения")
            print("2. По продукт")
            print("3. По тип движение (IN/OUT/MOVE)")
            print("4. По дата (ГГГГ-ММ-ДД)")

            sub = input("Избор: ")

            if sub == "1":
                report = report_controller.report_movements()
                rows = [
                    [item["date"], item["type"], item["product_id"], item["quantity"], item["price"], item["location"]]
                    for item in report.data
                ]
                print(format_table(["Дата", "Тип", "Продукт ID", "Количество", "Цена", "Локация"], rows))

            elif sub == "2":
                keyword = input("Име на продукт: ")
                report = report_controller.report_movements_by_product(keyword)
                rows = [
                    [item["date"], item["type"], item["quantity"], item["price"]]
                    for item in report.data
                ]
                print(format_table(["Дата", "Тип", "Количество", "Цена"], rows))

            elif sub == "3":
                mtype = input("Тип движение (IN/OUT/MOVE): ").upper()
                report = report_controller.report_movements_by_type(mtype)
                rows = [
                    [item["date"], item["product_id"], item["quantity"]]
                    for item in report.data
                ]
                print(format_table(["Дата", "Продукт ID", "Количество"], rows))

            elif sub == "4":
                date_str = input("Дата (ГГГГ-ММ-ДД): ")
                report = report_controller.report_movements_by_date(date_str)
                rows = [
                    [item["date"], item["type"], item["quantity"]]
                    for item in report.data
                ]
                print(format_table(["Дата", "Тип", "Количество"], rows))

            else:
                print("Невалиден избор.")

        # --- 3. Продажби (общо) ---
        elif choice == "3":
            report = report_controller.report_sales()
            rows = [
                [item["date"], item["product"], item["quantity"], item["total_price"], item["customer"]]
                for item in report.data
            ]
            print(format_table(["Дата", "Продукт", "Количество", "Общо", "Клиент"], rows))

        # --- 4. Продажби по клиент ---
        elif choice == "4":
            customer = input("Име на клиент: ")
            report = report_controller.report_sales_by_customer(customer)
            rows = [
                [item["date"], item["product"], item["quantity"], item["total_price"]]
                for item in report.data
            ]
            print(format_table(["Дата", "Продукт", "Количество", "Общо"], rows))

        # --- 5. Продажби по продукт ---
        elif choice == "5":
            product = input("Име на продукт: ")
            report = report_controller.report_sales_by_product(product)
            rows = [
                [item["date"], item["customer"], item["quantity"], item["total_price"]]
                for item in report.data
            ]
            print(format_table(["Дата", "Клиент", "Количество", "Общо"], rows))

        # --- 6. Продажби по дата ---
        elif choice == "6":
            date_str = input("Дата (ГГГГ-ММ-ДД): ")
            report = report_controller.report_sales_by_date(date_str)
            rows = [
                [item["product"], item["customer"], item["quantity"], item["total_price"]]
                for item in report.data
            ]
            print(format_table(["Продукт", "Клиент", "Количество", "Общо"], rows))

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
