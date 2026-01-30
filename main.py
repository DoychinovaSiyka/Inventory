from controllers.user_controller import UserController
from models.user import User
from storage.json_repository import JSONRepository

from user_interface.main_menu import show_menu
from user_interface.anonymous_menu import anonymous_menu
from user_interface.operator_menu import operator_menu
from user_interface.admin_menu import admin_menu


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

