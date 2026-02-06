
from menus.menu import Menu, MenuItem
from controllers.product_controller import ProductController
from controllers.movement_controller import MovementController
from controllers.user_controller import UserController
from models.movement import MovementType


class MovementView:
    def __init__(self, product_controller: ProductController,
                 movement_controller: MovementController,
                 user_controller: UserController):
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller

    def show_menu(self):
        user = self.user_controller.logged_user

        if not user:
            print("Трябва да сте логнат, за да правите доставки/продажби.")
            return

        menu = Menu("Меню за Доставки/Продажби", [
            MenuItem("1", "Създаване на доставка/продажба", self.create_movement),
            MenuItem("2", "Търсене на доставки/продажби", self.search_movements),
            MenuItem("3", "Покажи всички доставки/продажби", self.show_all),
            MenuItem("0", "Назад", lambda u: "break")
        ])

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # 1. Създаване на движение
    def create_movement(self, user):
        products = self.product_controller.get_all()

        if not products:
            print("Няма продукти.")
            return

        print("\nИзберете продукт:")
        for i, p in enumerate(products):
            print(f"{i}. {p.name} ({p.quantity} {p.unit})")

        try:
            product_idx = int(input("Избор: "))
            product = products[product_idx]
            product_id = product.product_id
        except (ValueError, IndexError):
            print("Невалиден избор.")
            return

        # Локации
        locations = self.movement_controller.location_controller.get_all()

        if not locations:
            print("Няма налични локации.")
            return

        print("\nИзберете локация:")
        for i, loc in enumerate(locations):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")

        try:
            loc_idx = int(input("Локация: "))
            location_id = locations[loc_idx].location_id
        except (ValueError, IndexError):
            print("Невалиден избор за локация.")
            return

        # Тип движение
        try:
            movement_type_num = int(input("0 = Доставка (IN), 1 = Продажба (OUT): "))
            if movement_type_num == 0:
                movement_type = MovementType.IN
            elif movement_type_num == 1:
                movement_type = MovementType.OUT
            else:
                print("Невалиден тип движение.")
                return
        except ValueError:
            print("Невалиден избор.")
            return

        # Количество, цена, описание
        print(f"Мерна единица на продукта: {product.unit}")
        quantity = input("Количество: ")  # ← остава string, валидира се в контролера
        price = input("Цена: ")
        description = input("Описание: ")

        # Клиент (само при OUT)
        customer = None
        if movement_type == MovementType.OUT:
            customer = input("Име на клиент: ").strip()
            if not customer:
                print("Не е въведено име на клиент. Ще се използва потребителското име.")
                customer = None

        # Създаване на движение
        try:
            self.movement_controller.add(
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

    # 2. Търсене
    def search_movements(self, _):
        keyword = input("Търси по описание: ")
        results = self.movement_controller.search(keyword)

        if not results:
            print("Няма намерени движения.")
            return

        for m in results:
            print(m)

    # 3. Всички движения
    def show_all(self, _):
        all_movements = self.movement_controller.get_all()

        if not all_movements:
            print("Няма движения.")
            return

        for m in all_movements:
            print(m)
