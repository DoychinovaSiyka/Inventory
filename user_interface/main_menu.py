def show_menu(user):
    role = user.role

    print("\n=== Главно меню ===")

    if role == "anonymous":
        print("1. Преглед на продукти")
        print("2. Преглед на категории")
        print("7. Информация за системата")
        print("0. Изход")
        return "anonymous"

    if role == "operator":
        print("1. Управление на продукти")
        print("2. Управление на категории")
        print("3. Доставки и продажби (IN/OUT движения)")
        print("5. Справки")
        print("6. Фактури")
        print("7. Информация за системата")
        print("0. Изход")
        return "operator"

    if role == "admin":
        print("1. Управление на продукти")
        print("2. Управление на категории")
        print("3. Доставки и продажби (IN/OUT движения)")
        print("4. Управление на потребители")
        print("5. Справки")
        print("6. Фактури")
        print("7. Информация за системата")
        print("0. Изход")
        return "admin"
