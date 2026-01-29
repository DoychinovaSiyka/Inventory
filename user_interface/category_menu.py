from password_utils import format_table

def category_menu(category_controller):
    while True:
        print("\n=== МЕНЮ КАТЕГОРИИ ===")
        print("0. Назад")
        print("1. Създаване на категория")
        print("2. Премахване на категория")
        print("3. Промяна на категория")
        print("4. Покажи всички категории")

        choice = input("Изберете опция: ")

        if choice == "0":
            break

        elif choice == "1":
            name = input("Име: ").strip()
            if not name:
                print("Името не може да е празно.")
                continue

            try:
                category_controller.add(name)
                print(f"Категорията '{name}' е създадена.")
            except ValueError as e:
                print("Грешка:", e)

        elif choice == "2":
            category_id = input("Въведи ID на категорията за изтриване: ")
            removed = category_controller.remove(category_id)
            if removed:
                print("Категорията е премахната.")
            else:
                print("Категорията не е намерена.")

        elif choice == "3":
            category_id = input("Въведи ID на категорията за промяна: ")
            new_name = input("Ново име: ").strip()
            updated = category_controller.update_name(category_id, new_name)
            if updated:
                print("Категорията е обновена.")
            else:
                print("Категорията не е намерена.")

        elif choice == "4":
            categories = category_controller.get_all()
            if not categories:
                print("Няма налични категории.")
            else:
                columns = ["ID", "Име"]
                rows = [[c.category_id, c.name] for c in categories]
                print("\n" + format_table(columns, rows))

        else:
            print("Невалидна опция. Опитай пак!")
