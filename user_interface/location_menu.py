from storage.password_utils import format_table


def location_menu(user, location_controller):
    is_admin = user.role == "Admin"

    while True:
        print("\n=== Меню Локации ===")
        print("1. Списък с локации")
        if is_admin:
            print("2. Добавяне на локация")
            print("3. Редактиране на локация")
            print("4. Изтриване на локация")
        print("0. Назад")

        choice = input("Избор: ")


        # 1. Списък с локации (Admin + Operator)

        if choice == "1":
            locations = location_controller.get_all()

            if not locations:
                print("Няма налични локации.")
                continue

            columns = ["ID", "Име", "Зона", "Капацитет"]
            rows = [
                [loc.location_id, loc.name, loc.zone, loc.capacity]
                for loc in locations
            ]

            print("\n" + format_table(columns, rows))


        # 2. Добавяне на локация (Admin only)

        elif choice == "2" and is_admin:
            name = input("Име на локация: ").strip()
            zone = input("Зона/Сектор: ").strip()
            try:
                capacity = int(input("Капацитет: "))
            except ValueError:
                print("Капацитетът трябва да е число.")
                continue

            try:
                location_controller.add(name=name, zone=zone, capacity=capacity)
                print("Локацията е добавена успешно!")
            except ValueError as e:
                print("Грешка:", e)


        # 3. Редактиране на локация (Admin only)

        elif choice == "3" and is_admin:
            loc_id = input("Въведете ID на локация: ").strip()
            location = location_controller.get_by_id(loc_id)

            if not location:
                print("Локацията не е намерена.")
                continue

            print("\nОставете празно, ако не искате да променяте полето.")
            new_name = input(f"Ново име ({location.name}): ").strip()
            new_zone = input(f"Нова зона ({location.zone}): ").strip()

            try:
                new_capacity_input = input(f"Нов капацитет ({location.capacity}): ").strip()
                new_capacity = int(new_capacity_input) if new_capacity_input else location.capacity
            except ValueError:
                print("Капацитетът трябва да е число.")
                continue

            try:
                location_controller.update(
                    loc_id,
                    name=new_name if new_name else location.name,
                    zone=new_zone if new_zone else location.zone,
                    capacity=new_capacity
                )
                print("Локацията е обновена успешно!")
            except ValueError as e:
                print("Грешка:", e)


        # 4. Изтриване на локация (Admin only)

        elif choice == "4" and is_admin:
            loc_id = input("Въведете ID на локация: ").strip()

            try:
                if location_controller.remove(loc_id):
                    print("Локацията е изтрита успешно!")
                else:
                    print("Локацията не е намерена.")
            except ValueError as e:
                print("Грешка:", e)

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
