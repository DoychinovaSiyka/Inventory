from views.menu import Menu, MenuItem
from views.password_utils import format_table


class MovementView:
    def __init__(self, product_controller, movement_controller, user_controller, location_controller,
                 supplier_controller=None):
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller
        self.menu = self._build_menu()


    def _build_menu(self):
        return Menu("Меню за Доставки/Продажби/Премествания", [
            MenuItem("1", "Създаване на доставка/продажба (IN/OUT)", self.create_movement),
            MenuItem("2", "Преместване между локации (MOVE)", self.move_between_locations),
            MenuItem("3", "Търсене на движения", self.search_movements),
            MenuItem("4", "Покажи всички движения", self.show_all),
            MenuItem("5", "Разширено филтриране", self.advanced_filter),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    # Помощен метод за избор - само по номер
    def _select_item(self, items, label):
        if not items:
            print(f"Няма налични {label}.")
            return None
        print(f"\nИзберете {label}:")
        for i, item in enumerate(items, start=1):
            # Продукт – разпознаваме по типа
            if isinstance(item, type(self.product_controller.get_all()[0])):
                item_id = item.product_id
            elif isinstance(item, type(self.location_controller.get_all()[0])):
                item_id = item.location_id
            # Доставчик – разпознаваме по типа
            elif self.supplier_controller and isinstance(item, type(self.supplier_controller.get_all()[0])):
                item_id = item.supplier_id
            else:
                item_id = "N/A"

            name = getattr(item, "name", "N/A")
            print(f"{i}. {name} (ID: {item_id})")

        choice = input("Номер (Enter = отказ): ").strip()
        if choice == "":
            return None
        if not choice.isdigit():
            print("Моля, въведете валиден номер.")
            return None
        idx = int(choice) - 1
        if 0 <= idx < len(items):
            return items[idx]
        print("Невалиден номер.")
        return None


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
        # Текущ склад на продукта
        current_location = self.location_controller.get_by_id(product.location_id)
        print("\n0 - Доставка (IN)")
        print("1 - Продажба (OUT)")
        movement_type_choice = input("Избор: ").strip()
        movement_type = "IN" if movement_type_choice == "0" else "OUT"

        # Продажба: винаги от текущия склад
        if movement_type == "OUT":
            location = current_location
            print(f"\nПродажбата ще бъде извършена от склада, в който е продуктът: {location.name}")

        # Доставка: избор на склад
        else:
            location = self._select_item(self.location_controller.get_all(), "локация")
            if not location:
                return

        # Проверка от контролера - бизнес логика
        try:
            self.movement_controller.check_movement_allowed(product_id=product.product_id,
                                                            location_id=location.location_id, movement_type=movement_type)
        except ValueError as e:
            print("Грешка:", e)
            return

        quantity = input("Количество: ")
        price = input("Цена: ")
        description = input("Описание: ")
        supplier_id = None
        customer = None
        # Доставка (IN) изисква доставчик
        if movement_type == "IN":
            if self.supplier_controller:
                supplier = self._select_item(self.supplier_controller.get_all(), "доставчик")
                if not supplier:
                    print("Грешка: При IN движение трябва да има доставчик.")
                    return
                supplier_id = supplier.supplier_id
            else:
                print("Грешка: Липсва контролер за доставчици.")
                return

        # Продажба (OUT) изисква клиент
        if movement_type == "OUT":
            customer = input("Име на клиент: ").strip() or None

        try:
            movement = self.movement_controller.add(product_id=product.product_id, user_id=user.user_id,
                                                    location_id=location.location_id, movement_type=movement_type,
                                                    quantity=quantity, description=description,
                                                    price=price, customer=customer, supplier_id=supplier_id)
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
        if from_loc.location_id == to_loc.location_id:
            print("\nГрешка: Не може да преместите продукта в същия склад!")
            return

        quantity = input("Количество за преместване: ")
        description = input("Описание (по избор): ")

        try:
            movement = self.movement_controller.move_product(product_id=product.product_id, user_id=user.user_id,
                                                             from_loc=from_loc.location_id, to_loc=to_loc.location_id,
                                                             quantity=quantity, description=description)
            print("\nПреместването е извършено успешно!")
            print(f"ID: {movement.movement_id}")

        except ValueError as e:
            print("Грешка:", e)

    # Търсене
    def search_movements(self, _):
        keyword = input("Търси по описание (мин. 3 символа): ").strip()
        if len(keyword) < 3:
            print("Моля, въведете поне 3 символа за търсене.")
            return

        results = self.movement_controller.search_by_description(keyword)
        if not results:
            print("Няма намерени движения.")
            return

        columns = ["Дата", "Тип", "Количество", "Единица", "Описание"]
        rows = [[m.date, m.movement_type.name, m.quantity, m.unit, m.description] for m in results]
        print(format_table(columns, rows))
        print()

    # Всички движения
    def show_all(self, _):
        movements = self.movement_controller.get_all()
        if not movements:
            print("Няма движения.")
            return

        columns = ["ID", "Дата", "Тип", "Количество", "Единица"]
        rows = [[m.movement_id, m.date, m.movement_type.name, m.quantity, m.unit] for m in movements]
        print(format_table(columns, rows))

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

        results = self.movement_controller.advanced_filter(movement_type=movement_type, start_date=start_date,
                                                           end_date=end_date, product_id=product_id, location_id=location_id,
                                                           user_id=user_id)

        if not results:
            print("\nНяма движения, които отговарят на критериите.")
            return

        has_price = any(m.movement_type.name in ("IN", "OUT") for m in results)
        if has_price:
            columns = ["Дата", "Тип", "Продукт", "Количество", "Единица", "Сума"]
            rows = []
            for m in results:
                if m.movement_type.name == "MOVE":
                    rows.append([m.date, "MOVE", m.product_id, m.quantity, m.unit, ""])
                else:
                    rows.append([m.date, m.movement_type.name, m.product_id, m.quantity, m.unit, m.price])
        else:
            columns = ["Дата", "Тип", "Продукт", "Количество", "Единица"]
            rows = [[m.date, m.movement_type.name, m.product_id, m.quantity, m.unit] for m in results]

        print(format_table(columns, rows))
