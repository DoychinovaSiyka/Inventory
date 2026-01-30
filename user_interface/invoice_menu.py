from password_utils import format_table


def invoice_menu(user, invoice_controller):
    while True:
        print("\n=== Меню Фактури ===")
        print("1. Списък с всички фактури")
        print("2. Преглед на фактура по ID")
        print("3. Търсене по клиент")
        print("4. Търсене по продукт")
        print("5. Търсене по дата (ГГГГ-ММ-ДД)")
        print("0. Назад")

        choice = input("Избор: ")

        # --- 1. Списък с фактури ---
        if choice == "1":
            invoices = invoice_controller.get_all()

            if not invoices:
                print("Няма налични фактури.")
                continue

            columns = ["ID", "Продукт", "Количество", "Ед. Цена", "Общо", "Клиент", "Дата"]

            rows = [
                [
                    inv.invoice_id,
                    inv.product,
                    inv.quantity,
                    inv.unit_price,
                    inv.total_price,
                    inv.customer,
                    inv.date
                ]
                for inv in invoices
            ]

            print("\n" + format_table(columns, rows))

        # --- 2. Преглед на фактура по ID ---
        elif choice == "2":
            invoice_id = input("Въведете ID на фактура: ")
            invoice = invoice_controller.get_by_id(invoice_id)

            if not invoice:
                print("Фактурата не е намерена.")
                continue

            columns = ["Поле", "Стойност"]
            rows = [
                ["ID", invoice.invoice_id],
                ["Movement ID", invoice.movement_id],
                ["Продукт", invoice.product],
                ["Количество", invoice.quantity],
                ["Единична цена", invoice.unit_price],
                ["Обща цена", invoice.total_price],
                ["Клиент", invoice.customer],
                ["Дата", invoice.date]
            ]

            print("\n" + format_table(columns, rows))

        # --- 3. Търсене по клиент ---
        elif choice == "3":
            keyword = input("Въведете име на клиент: ")
            results = invoice_controller.search_by_customer(keyword)

            if not results:
                print("Няма фактури за този клиент.")
                continue

            columns = ["ID", "Продукт", "Количество", "Общо", "Дата"]
            rows = [
                [inv.invoice_id, inv.product, inv.quantity, inv.total_price, inv.date]
                for inv in results
            ]

            print("\n" + format_table(columns, rows))

        # --- 4. Търсене по продукт ---
        elif choice == "4":
            keyword = input("Въведете име на продукт: ")
            results = invoice_controller.search_by_product(keyword)

            if not results:
                print("Няма фактури за този продукт.")
                continue

            columns = ["ID", "Клиент", "Количество", "Общо", "Дата"]
            rows = [
                [inv.invoice_id, inv.customer, inv.quantity, inv.total_price, inv.date]
                for inv in results
            ]

            print("\n" + format_table(columns, rows))

        # --- 5. Търсене по дата ---
        elif choice == "5":
            date_str = input("Въведете дата (ГГГГ-ММ-ДД): ")
            results = invoice_controller.search_by_date(date_str)

            if not results:
                print("Няма фактури за тази дата.")
                continue

            columns = ["ID", "Продукт", "Клиент", "Общо"]
            rows = [
                [inv.invoice_id, inv.product, inv.customer, inv.total_price]
                for inv in results
            ]

            print("\n" + format_table(columns, rows))

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
