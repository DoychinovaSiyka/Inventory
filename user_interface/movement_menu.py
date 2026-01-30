from controllers.product_controller import ProductController
from controllers.movement_controller import MovementController
from models.movement import MovementType


def movement_menu(product_controller: ProductController, movement_controller: MovementController, user_controller):
    user = user_controller.logged_user

    if not user:
        print("Трябва да сте логнат, за да правите доставки/продажби.")
        return

    while True:
        print("\nМеню за Доставки/Продажби")
        print("0.Назад")
        print("1.Създаване на доставка/продажба")
        print("2.Търсене на доставки/продажби")
        print("3.Покажи всички доставки/продажби")

        choice = input("Изберете опция: ")

        if choice == "0":
            break

        elif choice == "1":
            products = product_controller.get_all()

            if not products:
                print("Няма продукти.")
                continue

            for i, p in enumerate(products):
                print(f"{i}. {p.name}")

            try:
                product_idx = int(input("Изберете един от продуктите: "))
                product_id = products[product_idx].product_id
            except (ValueError, IndexError):
                print("Невалиден избор.")
                continue

            # -----------------------------
            # Избор на локация (по документацията)
            # -----------------------------
            locations = movement_controller.location_controller.get_all()

            if not locations:
                print("Няма налични локации.")
                continue

            print("\nИзберете локация:")
            for i, loc in enumerate(locations):
                print(f"{i}. {loc.name} (ID: {loc.location_id})")

            try:
                loc_idx = int(input("Локация: "))
                location_id = locations[loc_idx].location_id
            except (ValueError, IndexError):
                print("Невалиден избор за локация.")
                continue

            # -----------------------------
            # Тип движение
            # -----------------------------
            try:
                movement_type_num = int(input("Въведете 0 за доставка (IN) или 1 за продажба (OUT): "))
                if movement_type_num == 0:
                    movement_type = MovementType.IN
                elif movement_type_num == 1:
                    movement_type = MovementType.OUT
                else:
                    print("Невалиден тип движение.")
                    continue
            except ValueError:
                print("Невалиден избор.")
                continue

            # -----------------------------
            # Количество и цена
            # -----------------------------
            try:
                quantity = int(input("Количество: "))
                price = float(input("Цена: "))
            except ValueError:
                print("Количество и цена трябва да са числа.")
                continue

            description = input("Описание: ")

            # -----------------------------
            # Създаване на движение
            # -----------------------------
            try:
                movement_controller.add(
                    product_id=product_id,
                    user_id=user.id,
                    location_id=location_id,
                    movement_type=movement_type,
                    quantity=quantity,
                    description=description,
                    price=price
                )
                print("Движението е добавено успешно!")
            except ValueError as e:
                print("Грешка:", e)
