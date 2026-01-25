from controllers.product_controller import ProductController
from controllers.movement_controller import MovementController
from controllers.category_controller import CategoryController
from models.movement import MovementType
from models.product import Product
from models.category import Category
from storage.json_repository import JSONRepository
from password import require_password
from password import show_products_menu

from user_interface.product_menu import product_menu
from user_interface.category_menu import category_menu
from user_interface.movement_menu import movement_menu



def show_menu():
    print("\nНачално меню")
    print("0.Назад")
    print("1.Управление на продукт")
    print("2.Управление на категория")
    print("3.Управление на доставки/продажби")


def main():
    category_repo = JSONRepository("data/categories.json")
    product_repo = JSONRepository("data/products.json")
    movement_repo = JSONRepository("data/movements.json")

    category_controller = CategoryController(category_repo)
    product_controller = ProductController(product_repo)
    movement_controller = MovementController(movement_repo)
    while True:
        show_menu()
        choice = input("Изберете опция: ")
        if choice == "0":
            break
        elif choice == "1":
            product_menu(product_controller,category_controller)
        elif choice == "2":
            category_menu(category_controller)
        elif choice == "3":
            movement_menu(product_controller,movement_controller)
        else:
            print("Невалидна опция. Опитай пак!")



if __name__  == "__main__":
    main()



