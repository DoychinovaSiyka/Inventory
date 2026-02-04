from storage.password_utils import format_table


def supplier_menu(user, supplier_controller):
    is_admin = user.role == "Admin"

    while True:
        print("\n=== Меню Доставчици ===")
        print("1. Списък с доставчици")
        if is_admin:
            print("2. Добавяне на доставчик")
            print("3. Редактиране на доставчик")
            print("4. Изтриване на доставчик")
        print("0. Назад")

        choice = input("Избор: ")


        # 1. Списък с доставчици (Admin + Operator)
        if choice == "1":
            suppliers = supplier_controller.get_all()

            if not suppliers:
                print("Няма налични доставчици.")
                continue

            columns = ["ID", "Име", "Контакт", "Адрес"]
            rows = [
                [s.supplier_id, s.name, s.contact, s.address]
                for s in suppliers
            ]

            print("\n" + format_table(columns, rows))


        # 2. Добавяне на доставчик (Admin only)
        elif choice == "2" and is_admin:
            name = input("Име на доставчик: ").strip()
            contact = input("Контакт (телефон/имейл): ").strip()
            address = input("Адрес: ").strip()

            try:
                supplier_controller.add(name=name,contact=contact,address=address)
                print("Доставчикът е добавен успешно!")
            except ValueError as e:
                print("Грешка:", e)


        # 3. Редактиране на доставчик (Admin only)

        elif choice == "3" and is_admin:
            supplier_id = input("Въведете ID на доставчик: ").strip()
            supplier = supplier_controller.get_by_id(supplier_id)

            if not supplier:
                print("Доставчикът не е намерен.")
                continue

            print("\nОставете празно, ако не искате да променяте полето.")
            new_name = input(f"Ново име ({supplier.name}): ").strip()
            new_contact = input(f"Нов контакт ({supplier.contact}): ").strip()
            new_address = input(f"Нов адрес ({supplier.address}): ").strip()

            try:
                supplier_controller.update(
                    supplier_id,
                    name=new_name if new_name else supplier.name,
                    contact=new_contact if new_contact else supplier.contact,
                    address=new_address if new_address else supplier.address
                )
                print("Доставчикът е обновен успешно!")
            except ValueError as e:
                print("Грешка:", e)


        # 4. Изтриване на доставчик (Admin only)

        elif choice == "4" and is_admin:
            supplier_id = input("Въведете ID на доставчик: ").strip()

            try:
                if supplier_controller.remove(supplier_id):
                    print("Доставчикът е изтрит успешно!")
                else:
                    print("Доставчикът не е намерен.")
            except ValueError as e:
                print("Грешка:", e)

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
