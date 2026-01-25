def user_menu(user):
    if user.role != "admin":
        print("Само администратор може да управлява потребители.")
        return

    while True:
        print("\nМеню потребители")
        print("1. Списък на потребители")
        print("2. Добавяне на потребител")
        print("3. Промяна на роля")
        print("4. Деактивиране на потребител")
        print("0. Назад")

        choice = input("Избор: ")

        if choice == "1":
            list_users()
        elif choice == "2":
            add_user()
        elif choice == "3":
            change_role()
        elif choice == "4":
            deactivate_user()
        elif choice == "0":
            break
        else:
            print("Невалиден избор.")
