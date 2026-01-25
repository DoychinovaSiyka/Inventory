from controllers.product_controller import ProductController
from controllers.movement_controller import MovementController
from controllers.category_controller import CategoryController
from controllers.user_controller import UserController

from storage.json_repository import JSONRepository

from user_interface.product_menu import product_menu
from user_interface.category_menu import category_menu
from user_interface.movement_menu import movement_menu


def login(user_controller):
    print("\n   Вход в системата   ")
    username = input("Потребителско име: ")
    password = input("Парола: ")

    user = user_controller.authenticate(username, password)
    if not user:
        print("Грешно име или парола.")
        return None

    print(f"Добре дошъл, {user.username}! Роля: {user.role}")
    return user


def main():
    # Зареждане на репозиторита
    category_repo = JSONRepository("data/categories.json")
    product_repo = JSONRepository("data/products.json")
    user_repo = JSONRepository("data/users.json")
    movement_repo = JSONRepository("data/movements.json")

    # Контролери
    category_controller = CategoryController(category_repo)
    product_controller = ProductController(product_repo, category_controller)
    user_controller = UserController(user_repo)
    movement_controller = MovementController(movement_repo, product_controller, user_controller)

    # Логин
    user = None
    while not user:
        user = login(user_controller)

    # Главно меню според роля
    while True:
        print("\n Главно меню ")
        print("0. Изход")

        # Оператор + Администратор
        if user.role in ("operator", "admin"):
            print("1. Управление на продукт")
            print("2. Управление на категория")
            print("3. Управление на доставки/продажби")
            print("4. Справки (по-късно)")

        # Само Администратор
        if user.role == "admin":
            print("5. Управление на потребители (по-късно)")
            print("6. Управление на доставчици (по-късно)")
            print("7. Управление на локации (по-късно)")

        choice = input("Изберете опция: ")

        if choice == "0":
            break

        # Оператор + Администратор
        if choice == "1" and user.role in ("operator", "admin"):
            product_menu(product_controller, category_controller)

        elif choice == "2" and user.role in ("operator", "admin"):
            category_menu(category_controller)

        elif choice == "3" and user.role in ("operator", "admin"):
            movement_menu(product_controller, movement_controller)

        # Администратор
        elif choice in ("5", "6", "7") and user.role != "admin":
            print("Нямате права за тази операция.")

        else:
            print("Невалидна опция или нямате достъп.")


if __name__ == "__main__":
    main()
