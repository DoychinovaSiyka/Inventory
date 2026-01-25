def reports_menu(user):
    print("\nМеню справки")
    print("1. Справка за продукти")
    print("2. Справка за категории")
    print("3. Справка за движения")
    print("0. Назад")

    while True:
        choice = input("Избор: ")

        if choice == "1":
            print("Тук ще бъде справка за продукти.")
        elif choice == "2":
            print("Тук ще бъде справка за категории.")
        elif choice == "3":
            print("Тук ще бъде справка за движения.")
        elif choice == "0":
            break
        else:
            print("Невалиден избор.")
