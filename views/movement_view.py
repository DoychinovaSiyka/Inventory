from views.menu import Menu, MenuItem
from controllers.product_controller import ProductController
from controllers.movement_controller import MovementController
from controllers.user_controller import UserController
from models.movement import MovementType


class MovementView:
    def __init__(self, product_controller: ProductController,
                 movement_controller: MovementController,
                 user_controller: UserController,
                 activity_log_controller=None):
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller
        self.activity_log = activity_log_controller

    def show_menu(self):
        user = self.user_controller.logged_user

        if not user:
            print("Трябва да сте логнат, за да правите доставки/продажби.")
            return

        # Добавена е опция за вътрешно преместване (MOVE)
        menu = Menu("Меню за Доставки/Продажби/Премествания", [
            MenuItem("1", "Създаване на доставка/продажба (IN/OUT)", self.create_movement),
            MenuItem("2", "Преместване между локации (MOVE)", self.move_between_locations),
            MenuItem("3", "Търсене на движения", self.search_movements),
            MenuItem("4", "Покажи всички движения", self.show_all),
            MenuItem("5", "Разширено филтриране", self.advanced_filter),
            MenuItem("0", "Назад", lambda u: "break")
        ])

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # Създаване на IN/OUT движение
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

        # Избор на локация
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
        quantity = input("Количество: ")
        price = input("Цена: ")
        description = input("Описание: ")

        # Доставчик при IN
        supplier_id = None
        if movement_type == MovementType.IN:
            suppliers = self.product_controller.supplier_controller.get_all()

            if not suppliers:
                print("Няма доставчици. Добавете доставчик първо.")
                return

            print("\nИзберете доставчик:")
            for i, s in enumerate(suppliers):
                print(f"{i}. {s.name} (ID: {s.supplier_id})")

            try:
                sup_idx = int(input("Доставчик: "))
                supplier_id = suppliers[sup_idx].supplier_id
            except (ValueError, IndexError):
                print("Невалиден избор за доставчик.")
                return

        # Клиент при OUT
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
                customer=customer,
                supplier_id=supplier_id
            )
            print("Движението е добавено успешно!")
            print("Ако е OUT → фактурата е генерирана автоматично.")

        except ValueError as e:
            print("Грешка:", e)

    # MOVE – вътрешно преместване между локации
    def move_between_locations(self, user):
        print("\n=== Преместване между локации (MOVE) ===")

        # Избор на продукт
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
        except (ValueError, IndexError):
            print("Невалиден избор.")
            return

        # Избор на изходна локация
        locations = self.movement_controller.location_controller.get_all()
        if not locations:
            print("Няма налични локации.")
            return

        print("\nИзберете ИЗХОДНА локация:")
        for i, loc in enumerate(locations):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")

        try:
            from_idx = int(input("Избор: "))
            from_location_id = locations[from_idx].location_id
        except (ValueError, IndexError):
            print("Невалиден избор.")
            return

        # Избор на целева локация
        print("\nИзберете ЦЕЛЕВА локация:")
        for i, loc in enumerate(locations):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")

        try:
            to_idx = int(input("Избор: "))
            to_location_id = locations[to_idx].location_id
        except (ValueError, IndexError):
            print("Невалиден избор.")
            return

        # Количество
        quantity = input("Количество за преместване: ")

        # Описание
        description = input("Описание (по избор): ")

        # Извършване на преместването
        try:
            self.movement_controller.move_product(
                product_id=product.product_id,
                user_id=user.user_id,
                from_location_id=from_location_id,
                to_location_id=to_location_id,
                quantity=float(quantity),
                description=description
            )
            print("\nПреместването е извършено успешно!")

        except ValueError as e:
            print("Грешка:", e)

    # Търсене по описание
    def search_movements(self, _):
        keyword = input("Търси по описание: ")
        results = self.movement_controller.search(keyword)

        if not results:
            print("Няма намерени движения.")
            return

        for m in results:
            self._print_movement(m)

    # Показване на всички движения
    def show_all(self, _):
        all_movements = self.movement_controller.get_all()

        if not all_movements:
            print("Няма движения.")
            return

        for m in all_movements:
            self._print_movement(m)

    # Принтиране на движение
    def _print_movement(self, m):
        product = self.product_controller.get_by_id(m.product_id)
        product_name = product.name if product else f"ID: {m.product_id}"
        print(f"Продукт: {product_name}")

        user = self.user_controller.get_by_id(m.user_id)
        user_name = user.username if user else f"ID: {m.user_id}"
        print(f"Потребител: {user_name}")

        location = self.movement_controller.location_controller.get_by_id(m.location_id)
        location_name = location.name if location else "—"
        print(f"Локация: {location_name}")

        print(f"Тип: {m.movement_type.name}")
        print(f"Количество: {m.quantity} {m.unit}")

        # MOVE не е финансова операция → няма цена
        if m.movement_type == MovementType.MOVE:
            print("Цена: няма (вътрешно преместване)")
        else:
            print(f"Цена: {m.price}")

        print(f"Описание: {m.description}")

        if m.movement_type == MovementType.IN:
            supplier_name = "—"
            if m.supplier_id:
                supplier = self.product_controller.supplier_controller.get_by_id(m.supplier_id)
                if supplier:
                    supplier_name = supplier.name
            print(f"Доставчик: {supplier_name}")

        elif m.movement_type == MovementType.OUT:
            print(f"Клиент: {m.customer}")

        print(f"Дата: {m.date}")
        print(f"ID: {m.movement_id}")
        print("----------------------------------------")

    # Разширено филтриране
    def advanced_filter(self, _):
        print("\n=== Разширено филтриране на движения ===")

        print("Тип движение:")
        print("0 = IN (доставка)")
        print("1 = OUT (продажба)")
        print("2 = MOVE (преместване)")
        raw_type = input("Изберете тип или Enter за пропуск: ").strip()
        movement_type = None
        if raw_type.isdigit():
            raw_type = int(raw_type)
            if raw_type == 0:
                movement_type = MovementType.IN
            elif raw_type == 1:
                movement_type = MovementType.OUT
            elif raw_type == 2:
                movement_type = MovementType.MOVE

        start_date = input("Начална дата (YYYY-MM-DD) или Enter: ").strip()
        end_date = input("Крайна дата (YYYY-MM-DD) или Enter: ").strip()
        start_date = start_date if start_date else None
        end_date = end_date if end_date else None

        raw_pid = input("ID на продукт или Enter: ").strip()
        product_id = raw_pid if raw_pid else None

        raw_loc = input("ID на локация или Enter: ").strip()
        location_id = int(raw_loc) if raw_loc.isdigit() else None

        raw_uid = input("ID на потребител или Enter: ").strip()
        user_id = int(raw_uid) if raw_uid.isdigit() else None

        results = self.movement_controller.movements

        if movement_type:
            results = self.movement_controller.filter_by_type(movement_type)

        if start_date or end_date:
            results = self.movement_controller.filter_by_date_range(start_date, end_date)

        if product_id:
            results = [m for m in results if m.product_id == product_id]

        if location_id is not None:
            results = [m for m in results if m.location_id == location_id]

        if user_id is not None:
            results = [m for m in results if m.user_id == user_id]

        if not results:
            print("\nНяма движения, които отговарят на критериите.")
            return

        print("\n=== Резултати ===")
        for m in results:
            self._print_movement(m)
