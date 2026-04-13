from views.menu import Menu, MenuItem
from validators.movement_validator import MovementValidator


class MovementView:
    def __init__(self, product_controller, movement_controller, user_controller, activity_log_controller=None):

        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller
        self.activity_log = activity_log_controller
        self.menu = self._build_menu()

    # Меню
    def _build_menu(self):
        return Menu("Меню за Доставки/Продажби/Премествания", [
            MenuItem("1", "Създаване на доставка/продажба (IN/OUT)", self.create_movement),
            MenuItem("2", "Преместване между локации (MOVE)", self.move_between_locations),
            MenuItem("3", "Търсене на движения", self.search_movements),
            MenuItem("4", "Покажи всички движения", self.show_all),
            MenuItem("5", "Разширено филтриране", self.advanced_filter),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    def show_menu(self):
        user = self.user_controller.logged_user
        if not user:
            print("Трябва да сте логнат, за да правите доставки/продажби.")
            return
        while True:
            if self.menu.execute(self.menu.show(), user) == "break":
                break

    # IN/OUT движение
    def create_movement(self, user):
        # Изборът на продукт е в контролера
        product = self.movement_controller.select_product()
        if not product:
            return

        # Изборът на локация е в контролера
        location = self.movement_controller.select_location("локация")
        if not location:
            return

        raw_type = input("0  Доставка (IN), 1  Продажба (OUT): ").strip()
        try:
            movement_type = MovementValidator.parse_movement_type(raw_type)
        except ValueError as e:
            print(e)
            return

        quantity_raw = input("Количество: ")
        price_raw = input("Цена: ")
        description = input("Описание: ")

        try:
            quantity = MovementValidator.parse_quantity(quantity_raw)
            price = MovementValidator.parse_price(price_raw, movement_type)
            MovementValidator.validate_description(description, movement_type)
        except ValueError as e:
            print(e)
            return

        supplier_id = None
        if movement_type == "IN":
            supplier_id = self.movement_controller.select_supplier()
            if supplier_id is None:
                return

        customer = None
        if movement_type == "OUT":
            customer = input("Име на клиент: ").strip() or None

        try:
            movement = self.movement_controller.add(
                product_id=product.product_id,
                user_id=user.user_id,
                location_id=location.location_id,
                movement_type=movement_type,
                quantity=quantity,
                description=description,
                price=price,
                customer=customer,
                supplier_id=supplier_id
            )
            print("\nДвижението е добавено успешно!")
            print(f"ID: {movement.movement_id}")

        except ValueError as e:
            print("Грешка:", e)

    # MOVE
    def move_between_locations(self, user):
        print("\n   Преместване между локации (MOVE)   ")

        product = self.movement_controller.select_product()
        if not product:
            return

        from_loc = self.movement_controller.select_location("ИЗХОДНА локация")
        if not from_loc:
            return

        to_loc = self.movement_controller.select_location("ЦЕЛЕВА локация")
        if not to_loc:
            return

        quantity_raw = input("Количество за преместване: ")
        description = input("Описание (по избор): ")

        try:
            quantity = MovementValidator.parse_quantity(quantity_raw)
            MovementValidator.validate_locations(from_loc.location_id, to_loc.location_id, "MOVE")
        except ValueError as e:
            print(e)
            return

        try:
            movement = self.movement_controller.move_product(
                product_id=product.product_id,
                user_id=user.user_id,
                from_location_id=from_loc.location_id,
                to_location_id=to_loc.location_id,
                quantity=quantity,
                description=description
            )
            print("\nПреместването е извършено успешно!")
            print(f"ID: {movement.movement_id}")

        except ValueError as e:
            print("Грешка:", e)

    # Търсене
    def search_movements(self, _):
        keyword = input("Търси по описание: ").strip().lower()
        results = self.movement_controller.search_by_description(keyword)
        if not results:
            print("Няма намерени движения.")
            return
        for m in results:
            print(self.movement_controller.format_movement(m))

    # Всички движения
    def show_all(self, _):
        movements = self.movement_controller.get_all()
        if not movements:
            print("Няма движения.")
            return
        for m in movements:
            print(self.movement_controller.format_movement(m))

    # Разширено филтриране
    def advanced_filter(self, _):
        print("\n   Разширено филтриране на движения   ")

        raw_type = input("Тип движение (0=IN, 1=OUT, 2=MOVE) или Enter: ").strip()
        movement_type = None
        if raw_type:
            try:
                movement_type = MovementValidator.parse_movement_type(raw_type)
            except ValueError as e:
                print(e)
                return

        start_date_raw = input("Начална дата (YYYY-MM-DD) или Enter: ").strip()
        end_date_raw = input("Крайна дата (YYYY-MM-DD) или Enter: ").strip()
        try:
            start_date = MovementValidator.validate_date(start_date_raw)
            end_date = MovementValidator.validate_date(end_date_raw)
        except ValueError as e:
            print(e)
            return

        product_id = input("ID на продукт или Enter: ").strip() or None

        raw_loc = input("ID на локация или Enter: ").strip()
        try:
            location_id = MovementValidator.parse_optional_int(raw_loc, "ID на локация")
        except ValueError as e:
            print(e)
            return

        raw_uid = input("ID на потребител или Enter: ").strip()
        try:
            user_id = MovementValidator.parse_optional_int(raw_uid, "ID на потребител")
        except ValueError as e:
            print(e)
            return

        results = self.movement_controller.advanced_filter(
            movement_type=movement_type,
            start_date=start_date,
            end_date=end_date,
            product_id=product_id,
            location_id=location_id,
            user_id=user_id
        )

        if not results:
            print("\nНяма движения, които отговарят на критериите.")
            return

        for m in results:
            print(self.movement_controller.format_movement(m))
