from controllers.product_controller import ProductController
from controllers.movement_controller import MovementController
from models.movement import MovementType


def movement_menu(product_controller: ProductController, movement_controller: MovementController, user_controller):
    # ВЗИМАМЕ ЛОГНАТИЯ ПОТРЕБИТЕЛ
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
            # Избор на локация
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
            quantity = input("Количество: ")
            price = input("Цена: ")
            description = input("Описание: ")

            # -----------------------------
            # Клиент (само при OUT)
            # -----------------------------
            customer = None
            if movement_type == MovementType.OUT:
                customer = input("Въведете име на клиент: ").strip()
                if not customer:
                    print("Не е въведено име на клиент. Ще се използва потребителското име.")
                    customer = None  # fallback към username

            # -----------------------------
            # Създаване на движение
            # -----------------------------
            try:
                movement_controller.add(
                    product_id=product_id,
                    user_id=user.user_id,
                    location_id=location_id,
                    movement_type=movement_type,
                    quantity=quantity,
                    description=description,
                    price=price,
                    customer=customer
                )
                print("Движението е добавено успешно!")
                print("Ако е OUT → фактурата е генерирана автоматично.")
            except ValueError as e:
                print("Грешка:", e)

        elif choice == "2":
            keyword = input("Търси по описание: ")
            results = movement_controller.search(keyword)

            if not results:
                print("Няма намерени движения.")
                continue

            for m in results:
                print(m)

        elif choice == "3":
            all_movements = movement_controller.get_all()

            if not all_movements:
                print("Няма движения.")
                continue

            for m in all_movements:
                print(m)

        else:
            print("Невалиден избор.")
