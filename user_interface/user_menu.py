def user_menu(user_controller: UserController):
    user = user_controller.logged_user

    if user.role != "admin":
        print("Само администратор може да управлява потребители.")
        return

    while True:
        print("\n=== МЕНЮ ПОТРЕБИТЕЛИ ===")
        print("1. Списък на потребители")
        print("2. Добавяне на потребител")
        print("3. Промяна на роля")
        print("4. Деактивиране на потребител")
        print("0. Назад")

        choice = input("Избор: ")

        if choice == "1":
            users = user_controller.get_all()
            for u in users:
                print(f"{u.username} | {u.role} | {u.status}")

        elif choice == "2":
            fn = input("Име: ")
            ln = input("Фамилия: ")
            email = input("Email: ")
            username = input("Потребителско име: ")
            password = input("Парола: ")
            role = input("Роля (admin/operator): ")

            try:
                user_controller.register(fn, ln, email, username, password, role)
                print("Потребителят е добавен!")
            except ValueError as e:
                print("Грешка:", e)

        elif choice == "3":
            username = input("Потребителско име: ")
            new_role = input("Нова роля (admin/operator): ")

            if user_controller.change_role(username, new_role):
                print("Ролята е променена.")
            else:
                print("Потребителят не е намерен.")

        elif choice == "4":
            username = input("Потребителско име: ")
            if user_controller.deactivate_user(username):
                print("Потребителят е деактивиран.")
            else:
                print("Потребителят не е намерен.")

        elif choice == "0":
            break

        else:
            print("Невалидна опция.")


