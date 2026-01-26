from controllers.product_controller import ProductController
from controllers.movement_controller import MovementController


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

        # ---------------------------------------------------
        # 0. Назад
        # ---------------------------------------------------
        if choice == "0":
            break

        # ---------------------------------------------------
        # 1. Създаване на движение
        # ---------------------------------------------------
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

            try:
                movement_type_num = int(input("Въведете 0 за доставка или 1 за продажба: "))
            except ValueError:
                print("Невалиден избор.")
                continue

            quantity = input("Количество: ")
            description = input("Описание: ")
            price = input("Цена: ")

            try:
                movement_controller.add(
                    product_id=product_id,
                    user_id=user.id,
                    movement_type=movement_type_num,
                    quantity=quantity,
                    description=description,
                    price=price
                )
                print("Движението е добавено успешно!")
            except ValueError as e:
                print("Грешка:", e)

        # ---------------------------------------------------
        # 2. Търсене
        # ---------------------------------------------------
        elif choice == "2":
            keyword = input("Въведи дума за търсене в описанието: ").lower()
            results = movement_controller.search(keyword)

            if not results:
                print("Няма съвпадения.")
            else:
                print("\nНамерени движения:")
                for m in results:
                    print(f"- {m.movement_type.name} | "
                          f"Продукт ID: {m.product_id} | "
                          f"Количество: {m.quantity} | "
                          f"Цена: {m.price} | "
                          f"Дата: {m.date} | "
                          f"User ID: {m.user_id}")

        # ---------------------------------------------------
        # 3. Всички движения
        # ---------------------------------------------------
        elif choice == "3":
            movements = movement_controller.get_all()

            if not movements:
                print("Няма доставки или продажби.")
            else:
                print("\nСписък с движения:")
                for m in movements:
                    print(f"- {m.movement_type.name} | "
                          f"Продукт ID: {m.product_id} | "
                          f"Количество: {m.quantity} | "
                          f"Цена: {m.price} | "
                          f"Дата: {m.date} | "
                          f"User ID: {m.user_id}")

        else:
            print("Невалидна опция. Опитай пак!")
