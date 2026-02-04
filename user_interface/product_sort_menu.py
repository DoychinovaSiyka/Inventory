from controllers.product_controller import ProductController
from storage.password_utils import format_table


def sorting_menu(product_controller: ProductController):
    while True:
        print("\nСортиране на продукти:")
        print("1. По име (A–Z) – вградено сортиране")
        print("2. По цена (висока → ниска) – selection sort")
        print("3. По цена (ниска → висока) – bubble sort")
        print("4. По количество (високо → ниско) – bubble sort")
        print("5. По количество (ниско → високо) – selection sort")
        print("0. Назад")

        choice = input("Избор: ")

        if choice == "0":
            break

        #   Сортиране
        if choice == "1":
            products = product_controller.sort_by_name()
            title = "Име (A–Z) ↑"
            algorithm = "Вградено сортиране"

        elif choice == "2":
            products = product_controller.selection_sort()
            products.sort(key=lambda p: p.price, reverse=True)
            title = "Цена (висока → ниска) "
            algorithm = "Selection Sort"

        elif choice == "3":
            products = product_controller.bubble_sort()
            products.sort(key=lambda p: p.price)
            title = "Цена (ниска → висока) "
            algorithm = "Bubble Sort"

        elif choice == "4":
            products = product_controller.bubble_sort()
            products.sort(key=lambda p: p.quantity, reverse=True)
            title = "Количество (високо → ниско) ↓"
            algorithm = "Bubble Sort"

        elif choice == "5":
            products = product_controller.selection_sort()
            products.sort(key=lambda p: p.quantity)
            title = "Количество (ниско → високо) ↑"
            algorithm = "Selection Sort"

        else:
            print("Невалиден избор.")
            continue

        #   Таблично показване
        print(f"\n=== Сортиране по: {title} ===")
        print(f"Алгоритъм: {algorithm}\n")

        rows = [
            [p.name.ljust(20), f"{p.price:.2f} лв.", str(p.quantity)]
            for p in products
        ]

        print(format_table(["Име", "Цена", "Количество"], rows))
