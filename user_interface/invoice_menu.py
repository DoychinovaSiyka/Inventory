from password_utils import format_table   # използваме твоята таблица


def invoice_menu(user, invoice_controller):
    while True:
        print("\n=== Меню Фактури ===")
        print("1. Списък с всички фактури")
        print("2. Преглед на фактура по ID")
        print("3. Генериране на нова фактура (само при OUT движение)")
        print("0. Назад")

        choice = input("Избор: ")

        # --- 1. Списък с фактури ---
        if choice == "1":
            invoices = invoice_controller.get_all_invoices()

            if not invoices:
                print("Няма налични фактури.")
                continue

            columns = ["ID", "Продукт", "Количество", "Ед. Цена", "Общо", "Клиент", "Дата"]

            rows = []
            for inv in invoices:
                rows.append([
                    inv.invoice_id,
                    inv.product,
                    inv.quantity,
                    inv.unit_price,
                    inv.total_price,
                    inv.customer,
                    inv.date
                ])

            print("\n" + format_table(columns, rows))

        # --- 2. Преглед на фактура по ID ---
        elif choice == "2":
            invoice_id = input("Въведете ID на фактура: ")
            invoice = invoice_controller.get_invoice_by_id(invoice_id)

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

        # --- 3. Генериране на фактура ---
        elif choice == "3":
            print("\nФактурата се генерира автоматично при OUT движение.")
            print("Моля, използвайте менюто 'Доставки и продажби' за да регистрирате OUT операция.")

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
