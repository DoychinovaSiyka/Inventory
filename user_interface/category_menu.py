from storage.password_utils import format_table


def category_menu(user, category_controller):
    is_admin = user.role == "Admin"

    while True:
        print("\n=== Меню Категории ===")
        print("1. Списък с категории")
        if is_admin:
            print("2. Добавяне на категория")
            print("3. Редактиране на категория")
            print("4. Изтриване на категория")
        print("0. Назад")

        choice = input("Избор: ")

        # ---------------------------------------------------------
        # 1. Списък с категории (Admin + Operator)
        # ---------------------------------------------------------
        if choice == "1":
            categories = category_controller.get_all()

            if not categories:
                print("Няма категории.")
                continue

            columns = ["ID", "Име", "Описание"]
            rows = [
                [c.category_id, c.name, c.description]
                for c in categories
            ]

            print("\n" + format_table(columns, rows))

        # ---------------------------------------------------------
        # 2. Добавяне на категория (Admin only)
        # ---------------------------------------------------------
        elif choice == "2" and is_admin:
            name = input("Име на категория: ").strip()
            description = input("Описание: ").strip()

            try:
                category_controller.add(name=name, description=description)
                print("Категорията е добавена успешно!")
            except ValueError as e:
                print("Грешка:", e)

        # ---------------------------------------------------------
        # 3. Редактиране на категория (Admin only)
        # ---------------------------------------------------------
        elif choice == "3" and is_admin:
            category_id = input("Въведете ID на категория: ").strip()
            category = category_controller.get_by_id(category_id)

            if not category:
                print("Категорията не е намерена.")
                continue

            print("\nОставете празно, ако не искате да променяте полето.")
            new_name = input(f"Ново име ({category.name}): ").strip()
            new_desc = input(f"Ново описание ({category.description}): ").strip()

            try:
                category_controller.update(
                    category_id,
                    name=new_name if new_name else category.name,
                    description=new_desc if new_desc else category.description
                )
                print("Категорията е обновена успешно!")
            except ValueError as e:
                print("Грешка:", e)

        # ---------------------------------------------------------
        # 4. Изтриване на категория (Admin only)
        # ---------------------------------------------------------
        elif choice == "4" and is_admin:
            category_id = input("Въведете ID на категория: ").strip()

            try:
                if category_controller.remove(category_id):
                    print("Категорията е изтрита успешно!")
                else:
                    print("Категорията не е намерена.")
            except ValueError as e:
                print("Грешка:", e)

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
