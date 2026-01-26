from controllers.user_controller import UserController
from user_interface.product_menu import product_menu
from user_interface.category_menu import category_menu
from user_interface.movement_menu import movement_menu
from user_interface.user_menu import user_menu
from user_interface.reports_menu import reports_menu
from storage.json_repository import JSONRepository


def show_menu(user):
    role = user.role

    print("\nГлавно меню")

    if role == "anonymous":
        print("1. Преглед на продукти")
        print("2. Преглед на категории")
        print("0. Изход")
        return "anonymous"

    if role == "operator":
        print("1. Управление на продукти")
        print("2. Управление на категории")
        print("3. Доставки и продажби")
        print("0. Изход")
        return "operator"

    if role == "admin":
        print("1. Управление на продукти")
        print("2. Управление на категории")
        print("3. Доставки и продажби")
        print("4. Управление на потребители")
        print("5. Справки")
        print("0. Изход")
        return "admin"


def anonymous_menu(user):
    while True:
        choice = input("Избор: ")

        if choice == "1":
            product_menu(user, readonly=True)
        elif choice == "2":
            category_menu(user, readonly=True)
        elif choice == "0":
            break
        else:
            print("Невалиден избор.")


def operator_menu(user):
    while True:
        choice = input("Избор: ")

        if choice == "1":
            product_menu(user)
        elif choice == "2":
            category_menu(user)
        elif choice == "3":
            movement_menu(user)
        elif choice == "0":
            break
        else:
            print("Невалиден избор.")


def admin_menu(user):
    while True:
        choice = input("Избор: ")

        if choice == "1":
            product_menu(user)
        elif choice == "2":
            category_menu(user)
        elif choice == "3":
            movement_menu(user)
        elif choice == "4":
            user_menu(user)
        elif choice == "5":
            reports_menu(user)
        elif choice == "0":
            break
        else:
            print("Невалиден избор.")


def main():
    user_repo = JSONRepository("data/users.json")
    user_controller = UserController(user_repo)

    print("\nВход в системата")
    print("1. Вход с потребител")
    print("2. Вход като гост")
    print("0. Изход")

    option = input("Избор: ")

    if option == "1":
        username = input("Потребителско име: ")
        password = input("Парола: ")

        user = user_controller.authenticate(username, password)

        if not user:
            print("Грешно име или парола.")
            return

    elif option == "2":
        user = User(
            first_name="Guest",
            last_name="",
            email="",
            username="anonymous",
            password="",
            role="anonymous",
            status="active"
        )
    else:
        return

    role = show_menu(user)

    if role == "anonymous":
        anonymous_menu(user)
    elif role == "operator":
        operator_menu(user)
    elif role == "admin":
        admin_menu(user)


if __name__ == "__main__":
    main()
