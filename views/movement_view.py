from views.menu import Menu, MenuItem


class MovementView:
    def __init__(self, product_controller, movement_controller, user_controller, location_controller,
                 supplier_controller=None):
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller
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

    # Помощен метод за избор (преместен от контролера тук)
    def _select_item(self, items, label):
        if not items:
            print(f"Няма налични {label}.")
            return None
        print(f"\nИзберете {label}:")
        for i, item in enumerate(items, start=1):
            name = getattr(item, 'name', 'N/A')
            id_val = getattr(item, f'{label}_id', 'ID')
            print(f"{i}. {name} (ID: {id_val})")

        choice = input("Номер: ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(items)):
            print("Невалиден избор.")
            return None
        return items[int(choice) - 1]

    def show_menu(self):
        user = self.user_controller.logged_user
        if not user:
            print("Трябва да сте логнат, за да правите доставки/продажби.")
            return

        while True:
            choice = self.menu.show()
            if self.menu.execute(choice, user) == "break":
                break

    # IN/OUT движение
    def create_movement(self, user):
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return

        location = self._select_item(self.location_controller.get_all(), "локация")
        if not location:
            return

        print("\n0 - Доставка (IN)")
        print("1 - Продажба (OUT)")
        movement_type_choice = input("Избор: ").strip()
        movement_type = "IN" if movement_type_choice == "0" else "OUT"

        try:
            self.movement_controller.check_movement_allowed(
                product_id=product.product_id,
                location_id=location.location_id,
                movement_type=movement_type
            )
        except ValueError as e:
            print("Грешка:", e)
            return

        quantity = input("Количество: ")
        price = input("Цена: ")
        description = input("Описание: ")

        supplier_id = None
        customer = None

        if movement_type == "IN":
            if self.supplier_controller:
                supplier = self._select_item(self.supplier_controller.get_all(), "доставчик")
                if supplier:
                    supplier_id = supplier.supplier_id
            else:
                print("Грешка: Липсва контролер за доставчици.")
                return

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

        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return

        from_loc = self._select_item(self.location_controller.get_all(), "ИЗХОДНА локация")
        if not from_loc:
            return

        to_loc = self._select_item(self.location_controller.get_all(), "ЦЕЛЕВА локация")
        if not to_loc:
            return

        quantity = input("Количество за преместване: ")
        description = input("Описание (по избор): ")

        try:
            movement = self.movement_controller.move_product(
                product_id=product.product_id,
                user_id=user.user_id,
                from_loc=from_loc.location_id,
                to_loc=to_loc.location_id,
                quantity=quantity,
                description=description
            )
            print("\nПреместването е извършено успешно!")
            print(f"ID: {movement.movement_id}")

        except ValueError as e:
            print("Грешка:", e)

    # Търсене
    def search_movements(self, _):
        keyword = input("Търси по описание (мин. 3 символа): ").strip()

        # ✔ Проверка за минимум 3 символа
        if len(keyword) < 3:
            print("Моля, въведете поне 3 символа за търсене.")
            return

        results = self.movement_controller.search_by_description(keyword)
        if not results:
            print("Няма намерени движения.")
            return

        for m in results:
            print(f"[{m.date}] {m.movement_type.name} - {m.quantity} {m.unit}")
            print("Описание:")
            print(m.description)
            print("-" * 45)

    # Всички движения
    def show_all(self, _):
        movements = self.movement_controller.get_all()
        if not movements:
            print("Няма движения.")
            return

        for m in movements:
            print(f"ID: {m.movement_id} | {m.date} | {m.movement_type.name} | {m.quantity} {m.unit}")

    # Разширено филтриране
    def advanced_filter(self, _):
        print("\n   Разширено филтриране на движения   ")

        print("0=IN, 1=OUT, 2=MOVE")
        m_type_input = input("Тип движение или Enter: ").strip() or None

        movement_type = None
        if m_type_input == "0":
            movement_type = "IN"
        elif m_type_input == "1":
            movement_type = "OUT"
        elif m_type_input == "2":
            movement_type = "MOVE"

        start_date = input("Начална дата (YYYY-MM-DD) или Enter: ").strip() or None
        end_date = input("Крайна дата (YYYY-MM-DD) или Enter: ").strip() or None
        product_id = input("ID на продукт или Enter: ").strip() or None
        location_id = input("ID на локация или Enter: ").strip() or None
        user_id = input("ID на потребител или Enter: ").strip() or None

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
            print(f"[{m.date}] {m.movement_type.name} | Продукт: {m.product_id} | Сума: {m.price}")
