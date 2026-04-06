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

    # Помощни методи
    def _select_product(self):
        products = self.product_controller.get_all()
        if not products:
            print("Няма продукти.")
            return None
        print("\nИзберете продукт:")
        for i, p in enumerate(products):
            print(f"{i}. {p.name} ({p.quantity} {p.unit})")
        try:
            return products[int(input("Избор: "))]
        except (ValueError, IndexError):
            print("Невалиден избор.")
            return None


    def _select_location(self, label="локация"):
        locations = self.movement_controller.location_controller.get_all()
        if not locations:
            print("Няма налични локации.")
            return None
        print(f"\nИзберете {label}:")
        for i, loc in enumerate(locations):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")
        try:
            return locations[int(input("Избор: "))]
        except (ValueError, IndexError):
            print("Невалиден избор.")
            return None

    # Създаване на IN/OUT движение
    def create_movement(self, user):
        product = self._select_product()
        if not product:
            return
        location = self._select_location("локация")
        if not location:
            return
        try:
            movement_type = MovementType.IN if int(input("0  Доставка (IN), 1  Продажба (OUT): ")) == 0 \
                else MovementType.OUT
        except ValueError:
            print("Невалиден избор.")
            return

        print(f"Мерна единица на продукта: {product.unit}")
        quantity = input("Количество: ")
        price = input("Цена: ")
        description = input("Описание: ")
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
                supplier_id = suppliers[int(input("Доставчик: "))].supplier_id
            except (ValueError, IndexError):
                print("Невалиден избор за доставчик.")
                return

        customer = None
        if movement_type == MovementType.OUT:
            customer = input("Име на клиент: ").strip() or None

        try:
            movement = self.movement_controller.add(product_id=product.product_id,
                                                    user_id=user.user_id,
                                                    location_id=location.location_id,
                                                    movement_type=movement_type,
                                                    quantity=quantity, description=description,
                                                    price=price,
                                                    customer=customer, supplier_id=supplier_id)

            print("\nДвижението е добавено успешно!")
            print(f"ID на движението: {movement.movement_id}")

            # Само при OUT - фактура
            if movement_type == MovementType.OUT:
                print("Фактурата е генерирана автоматично.")

            # Само при IN - доставка
            elif movement_type == MovementType.IN:
                print("Доставката е регистрирана успешно.")

        except ValueError as e:
            print("Грешка:", e)

    # MOVE – вътрешно преместване
    def move_between_locations(self, user):
        print("\n   Преместване между локации (MOVE)   ")

        product = self._select_product()
        if not product:
            return
        from_loc = self._select_location("ИЗХОДНА локация")
        if not from_loc:
            return
        to_loc = self._select_location("ЦЕЛЕВА локация")
        if not to_loc:
            return

        quantity = input("Количество за преместване: ")
        description = input("Описание (по избор): ")

        try:
            movement = self.movement_controller.move_product(product_id=product.product_id,
                                                             user_id=user.user_id,
                                                             from_location_id=from_loc.location_id,
                                                             to_location_id=to_loc.location_id,
                                                             quantity=float(quantity),
                                                             description=description)
            print("\nПреместването е извършено успешно!")
            print(f"От {from_loc.location_id} → към {to_loc.location_id}")
            print(f"ID на движението: {movement.movement_id}")

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
        print("\n   Разширено филтриране на движения   ")
        print("Тип движение:")
        print("0  IN (доставка)")
        print("1  OUT (продажба)")
        print("2  MOVE (преместване)")
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
        start_date = start_date or None
        end_date = end_date or None
        raw_pid = input("ID на продукт или Enter: ").strip()
        product_id = raw_pid or None
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

        print("\n   Резултати   ")
        for m in results:
            self._print_movement(m)
