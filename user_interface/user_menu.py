from controllers.user_controller import UserController
from models.user import User   # ако нямаш този импорт, махни го


def user_menu(user: User, user_controller: UserController):
    # Само Admin има достъп (SRS + Summary)
    if user.role != "Admin":
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

        # ---------------------------------------------------------
        # 1. Списък
        # ---------------------------------------------------------
        if choice == "1":
            users = user_controller.get_all()
            for u in users:
                print(f"{u.username} | {u.role} | {u.status}")

        # ---------------------------------------------------------
        # 2. Добавяне (Admin only)
        # ---------------------------------------------------------
        elif choice == "2":
            fn = input("Име: ")
            ln = input("Фамилия: ")
            email = input("Email: ")
            username = input("Потребителско име: ")
            password = input("Парола: ")
            role = input("Роля (Admin/Operator): ")

            try:
                user_controller.register(fn, ln, email, username, password, role)
                print("Потребителят е добавен!")
            except ValueError as e:
                print("Грешка:", e)

        # ---------------------------------------------------------
        # 3. Промяна на роля (Admin only)
        # ---------------------------------------------------------
        elif choice == "3":
            username = input("Потребителско име: ")
            new_role = input("Нова роля (Admin/Operator): ")

            try:
                if user_controller.change_role(user, username, new_role):
                    print("Ролята е променена.")
                else:
                    print("Потребителят не е намерен.")
            except Exception as e:
                print("Грешка:", e)

        # ---------------------------------------------------------
        # 4. Деактивиране (Admin only)
        # ---------------------------------------------------------
        elif choice == "4":
            username = input("Потребителско име: ")

            try:
                if user_controller.deactivate_user(user, username):
                    print("Потребителят е деактивиран.")
                else:
                    print("Потребителят не е намерен.")
            except Exception as e:
                print("Грешка:", e)

        elif choice == "0":
            break

        else:
            print("Невалидна опция.")
