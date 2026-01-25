def movement_menu(product_controller: ProductController, movement_controller: MovementController):
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
            for i, c in enumerate(products):
                print(f"{i}. {c.name}")

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
                movement_controller.add(product_id, movement_type_num, quantity, description, price)
                print("Движението е добавено успешно!")
            except ValueError as e:
                print("Грешка:", e)

        elif choice == "2":
            keyword = input("Въведи дума за търсене в описанието: ").lower()
            results = [m for m in movement_controller.get_all() if keyword in m.description.lower()]
            if not results:
                print("Няма съвпадения.")
            else:
                print("\nНамерени движения:")
                for m in results:
                    print(f"-{m.movement_type.name} | Продукт ID: {m.product_id} | Количество: {m.quantity} | Цена: {m.price} | Дата: {m.created}")

        elif choice == "3":
            movements = movement_controller.get_all()
            if not movements:
                print("Няма доставки или продажби.")
            else:
                print("\nСписък с движения:")
                for m in movements:
                    print(f"-{m.movement_type.name} | Продукт ID: {m.product_id} | Количество: {m.quantity} | Цена: {m.price} | Дата: {m.created}")

        else:
            print("Невалидна опция. Опитай пак!")
