from controllers.report_controller import ReportController
from storage.json_repository import JSONRepository
from controllers.product_controller import ProductController
from controllers.movement_controller import MovementController



# Меню за Справки
def reports_menu(user):
    print("\nСправки")

    # Създаваме нужните контролери
    product_repo = JSONRepository("data/products.json")
    movement_repo = JSONRepository("data/movements.json")

    product_controller = ProductController(product_repo)
    movement_controller = MovementController(movement_repo)

    report_controller = ReportController(product_controller,movement_controller)
    while True:
        print("\n--- Меню Справки ---")
        print("1. Ниски наличности")
        print("2. Изчерпани продукти")
        print("3. Стойност на склада")
        print("4. Движения по период")
        print("0. Назад")

        choice = input("Избор: ")

        if choice == "1":
            report = report_controller.low_stock()
            print("\n--- Справка: Ниски наличности ---")
            for item in report.result:
                print(item)

        elif choice == "2":
            report = report_controller.out_of_stock()
            print("\n--- Справка: Изчерпани продукти ---")
            for item in report.result:
                print(item)

        elif choice == "3":
            report = report_controller.inventory_value()
            print("\n--- Справка: Стойност на склада ---")
            print(f"Обща стойност: {report.result} лв.")

        elif choice == "4":
            start = input("Начална дата (YYYY-MM-DD): ")
            end = input("Начална дата (YYYY-MM-DD): ")

            report = report_controller.movements_by_period(start,end)

            print("\n---Справка: Движения по период ---")
            for item in report.result:
                print(item)

        elif choice == "0":
            break
        else:
            print("Невалиден избор.")




