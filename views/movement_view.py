from models.product import Product
from models.location import Location
from models.supplier import Supplier
from views.menu import Menu, MenuItem
from views.password_utils import format_table
import textwrap
import uuid


class MovementView:
    def __init__(self, product_controller, movement_controller, user_controller, location_controller,
                 supplier_controller=None):
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller
        self.menu = self._build_menu()

    # HELPERS
    @staticmethod
    def _format_qty_unit(quantity, unit):
        if quantity is None:
            return "0"
        if not unit:
            return str(quantity)
        return f"{quantity} {unit}"

    def _build_menu(self):
        return Menu("Меню за Доставки/Продажби/Премествания", [
            MenuItem("1", "Създаване на доставка/продажба (IN/OUT)", self.create_movement),
            MenuItem("2", "Преместване между локации (MOVE)", self.move_between_locations),
            MenuItem("3", "Търсене на движения", self.search_movements),
            MenuItem("4", "Покажи всички движения", self.show_all),
            MenuItem("5", "Разширено филтриране", self.advanced_filter),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    # INVENTORY ACCESS
    def _get_inventory(self):
        return self.product_controller.inventory_controller.data["products"]

    def _get_product_total_qty(self, product):
        inv = self._get_inventory()
        pdata = inv.get(product.product_id, {})
        locations = pdata.get("locations", {})
        return sum(float(q) for q in locations.values())

    def _get_product_warehouses_with_qty(self, product):
        inv = self._get_inventory()
        pdata = inv.get(product.product_id, {})
        locations = pdata.get("locations", {})
        return [(wh, float(qty), product.unit) for wh, qty in locations.items()]

    def _get_item_qty_text(self, item):
        if isinstance(item, Product):
            total = self._get_product_total_qty(item)
            return f" – {total} {item.unit}"
        return ""

    def _get_product_locations(self, product):
        wh_list = self._get_product_warehouses_with_qty(product)
        ids = sorted({wh for (wh, _, _) in wh_list})
        return ", ".join(ids)

    # FIXED SELECT ITEM
    def _select_item(self, items, label):
        if not items:
            print(f"Няма налични {label}.")
            return None

        print(f"\nИзберете {label}:")
        for i, item in enumerate(items, start=1):

            # FIXED: CORRECT ID DETECTION
            if isinstance(item, Product):
                item_id = item.product_id
            elif isinstance(item, Location):
                item_id = item.location_id
            elif isinstance(item, Supplier):
                item_id = item.supplier_id
            else:
                print("Непознат тип обект.")
                return None

            name = item.name
            qty_text = self._get_item_qty_text(item)
            print(f"{i}. {name}{qty_text} (ID: {item_id})")

            if isinstance(item, Product):
                locations = self._get_product_locations(item)
                if locations:
                    print(f"   Намира се в: {locations}")

        raw = input("Номер или ID (Enter = отказ): ").strip()
        if raw == "":
            return None

        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(items):
                return items[idx]
            print("Невалиден номер.\n")
            return None

        raw_lower = raw.lower()
        for item in items:
            if isinstance(item, Product):
                item_id = item.product_id
            elif isinstance(item, Location):
                item_id = item.location_id
            else:
                item_id = item.supplier_id

            if item_id.lower() == raw_lower:
                return item

        print("Невалиден ID.\n")
        return None

    # MENU
    def show_menu(self):
        user = self.user_controller.logged_user
        if not user:
            print("Трябва да сте логнат, за да правите доставки/продажби.")
            return
        while True:
            choice = self.menu.show()
            if self.menu.execute(choice, user) == "break":
                break

    # IN / OUT
    def create_movement(self, user):
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return

        print("\n0 - Доставка (IN)")
        print("1 - Продажба (OUT)")
        movement_type_choice = input("Избор: ").strip()
        movement_type = "IN" if movement_type_choice == "0" else "OUT"

        # OUT
        if movement_type == "OUT":
            wh_list = self._get_product_warehouses_with_qty(product)
            if not wh_list:
                print("\nГрешка: Няма наличност от този продукт в нито един склад.")
                return

            print("\nИзберете склад, от който ще се продаде продуктът:")
            for i, (wh, qty, unit) in enumerate(wh_list, start=1):
                loc = self.location_controller.get_by_id(wh)
                loc_name = loc.name if loc else wh
                print(f"{i}. {loc_name} – {qty} {unit} (ID: {wh})")

            raw = input("Ваш избор (номер или ID): ").strip()
            if raw == "":
                return

            chosen_wh = None

            if raw.isdigit():
                idx = int(raw) - 1
                if 0 <= idx < len(wh_list):
                    chosen_wh = wh_list[idx][0]
            else:
                for (wh, _, _) in wh_list:
                    if wh.lower() == raw.lower():
                        chosen_wh = wh
                        break

            if not chosen_wh:
                print("Невалиден избор на склад.")
                return

            location = self.location_controller.get_by_id(chosen_wh)

        # IN
        else:
            location = self._select_item(self.location_controller.get_all(), "локация")
            if not location:
                return

        quantity = input("Количество: ")
        price = input("Цена: ")
        description = input("Описание: ")
        supplier_id = None
        customer = None

        if movement_type == "IN":
            supplier = self._select_item(self.supplier_controller.get_all(), "доставчик")
            if not supplier:
                print("Грешка: При IN движение трябва да има доставчик.")
                return
            supplier_id = supplier.supplier_id

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

        # наличности по складове
        wh_list = self._get_product_warehouses_with_qty(product)
        qty_by_wh = {wh: (qty, unit) for (wh, qty, unit) in wh_list}

        if not wh_list:
            print("Грешка: Продуктът няма наличност в нито един склад.")
            return

        all_locations = self.location_controller.get_all()

        print("\nИзберете ИЗХОДНА локация (може да се мести само от локация с наличност):")
        for i, loc in enumerate(all_locations, start=1):
            qty, unit = qty_by_wh.get(loc.location_id, (0.0, product.unit))
            print(f"{i}. {loc.name} – {qty} {unit} (ID: {loc.location_id})")

        raw = input("Номер или ID: ").strip()
        if raw == "":
            return

        from_loc = None
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(all_locations):
                from_loc = all_locations[idx].location_id
        else:
            for loc in all_locations:
                if loc.location_id.lower() == raw.lower():
                    from_loc = loc.location_id
                    break

        if not from_loc:
            print("Невалидна изходна локация.")
            return

        from_qty, _ = qty_by_wh.get(from_loc, (0.0, product.unit))
        if from_qty <= 0:
            print("Грешка: Няма наличност в избраната изходна локация.")
            return

        possible_targets = [loc for loc in all_locations if loc.location_id != from_loc]

        print("\nИзберете ЦЕЛЕВА локация:")
        for i, loc in enumerate(possible_targets, start=1):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")

        raw = input("Номер или ID: ").strip()
        if raw == "":
            return

        to_loc = None
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(possible_targets):
                to_loc = possible_targets[idx].location_id
        else:
            for loc in possible_targets:
                if loc.location_id.lower() == raw.lower():
                    to_loc = loc.location_id
                    break

        if not to_loc:
            print("Невалидна целева локация.")
            return

        quantity = input("Количество за преместване: ")
        description = input("Описание (по избор): ")

        try:
            movement = self.movement_controller.move_product(
                product_id=product.product_id,
                user_id=user.user_id,
                from_loc=from_loc,
                to_loc=to_loc,
                quantity=quantity,
                description=description
            )

            print("\nПреместването е извършено успешно!")
            print(f"ID: {movement.movement_id}")

        except ValueError as e:
            print("Грешка:", e)


    def search_movements(self, _):
        keyword = input("Търси по описание (мин. 3 символа): ").strip()
        if len(keyword) < 3:
            print("Моля, въведете поне 3 символа за търсене.")
            return

        results = self.movement_controller.search_by_description(keyword)
        if not results:
            print("Няма намерени движения.")
            return

        # --- Съкратено описание за таблицата ---
        def short(text, max_len=60):
            if not text:
                return ""
            text = text.strip()
            return text if len(text) <= max_len else text[:max_len] + "..."

        columns = ["ID", "Дата", "Тип", "Количество", "Описание"]

        rows = [
            [
                m.movement_id,
                m.date,
                m.movement_type.name,
                self._format_qty_unit(m.quantity, m.unit),
                short(m.description, 60)
            ]
            for m in results
        ]

        print(format_table(columns, rows))
        print()

        # --- Детайлен изглед ---
        choice = input("Въведете ID за детайли или Enter за изход: ").strip()
        if not choice:
            return

        movement = self.movement_controller.get_by_id(choice)
        if movement is None:
            print("\nНевалидно ID. Няма движение с такъв идентификатор.\n")
            return

        print("\n--- Детайли за движение ---")
        print(f"ID: {movement.movement_id}")
        print(f"Дата: {movement.date}")
        print(f"Тип: {movement.movement_type.name}")
        print(f"Количество: {self._format_qty_unit(movement.quantity, movement.unit)}")

        # Локации
        if movement.movement_type.name == "MOVE":
            print(f"От: {movement.from_location_id}")
            print(f"До: {movement.to_location_id}")
        else:
            print(f"Локация: {movement.location_id}")

        # Цена
        if movement.price:
            print(f"Цена: {movement.price} лв.")

        # Клиент / Доставчик
        if movement.customer:
            print(f"Клиент: {movement.customer}")
        if movement.supplier_id:
            print(f"Доставчик ID: {movement.supplier_id}")

        print("\nОписание:")
        print(movement.description or "(няма)")
        print("-----------------------------\n")

    # SHOW ALL
    def show_all(self, _):
        movements = self.movement_controller.movements
        if not movements:
            print("Няма движения.")
            return

        columns = ["ID", "Дата", "Тип", "Количество"]
        rows = [
            [m.movement_id, m.date, m.movement_type.name, self._format_qty_unit(m.quantity, m.unit)]
            for m in movements
        ]

        print(format_table(columns, rows))

    def advanced_filter(self, _):
        print("\n   Разширено филтриране на движения   ")
        print("0=IN, 1=OUT, 2=MOVE")

        errors = []


        m_type_input = input("Тип movement или Enter: ").strip() or None
        movement_type = None

        if m_type_input is not None:
            if m_type_input == "0":
                movement_type = "IN"
            elif m_type_input == "1":
                movement_type = "OUT"
            elif m_type_input == "2":
                movement_type = "MOVE"
            else:
                errors.append("Невалиден тип движение. Допустими: 0=IN, 1=OUT, 2=MOVE.")


        start_date = input("Начална дата (YYYY-MM-DD) или Enter: ").strip() or None
        end_date = input("Крайна дата (YYYY-MM-DD) или Enter: ").strip() or None

        from datetime import datetime

        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                errors.append("Невалидна начална дата. Форматът е YYYY-MM-DD.")

        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                errors.append("Невалидна крайна дата. Форматът е YYYY-MM-DD.")


        product_id = input("ID на продукт или Enter: ").strip() or None
        if product_id:
            try:
                import uuid
                uuid.UUID(product_id)
                if not self.product_controller.get_by_id(product_id):
                    errors.append("Продукт с такова ID не съществува.")
            except:
                errors.append("Невалиден формат за ID на продукт.")


        location_id = input("ID на локация или Enter: ").strip() or None
        if location_id:
            try:
                uuid.UUID(location_id)
                if not self.location_controller.get_by_id(location_id):
                    errors.append("Локация с такова ID не съществува.")
            except:
                errors.append("Невалиден формат за ID на локация.")

        #  User ID
        user_id = input("ID на потребител или Enter: ").strip() or None
        if user_id:
            try:
                uuid.UUID(user_id)
                if not self.user_controller.get_by_id(user_id):
                    errors.append("Потребител с такова ID не съществува.")
            except:
                errors.append("Невалиден формат за ID на потребител.")

        # If errors - show all and stop
        if errors:
            print("\n[!] Открити са грешки:")
            for e in errors:
                print(" - " + e)
            print("\nМоля, коригирайте и опитайте отново.\n")
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
            print("\nНяма движения, които отговарят на критериите.\n")
            return

        rows = []
        columns = ["Дата", "Тип", "Продукт", "Количество", "Цена/Инфо", "Локация"]

        for m in results:
            product = self.product_controller.get_by_id(m.product_id)
            product_name = product.name if product else m.product_id

            qty = self._format_qty_unit(m.quantity, m.unit)

            if m.movement_type.name == "MOVE":
                loc_from = self.location_controller.get_by_id(m.from_location_id)
                loc_to = self.location_controller.get_by_id(m.to_location_id)
                loc_display = f"{loc_from.name if loc_from else m.from_location_id} → {loc_to.name if loc_to else m.to_location_id}"
                price_display = "-"
            else:
                loc = self.location_controller.get_by_id(m.location_id)
                loc_display = loc.name if loc else m.location_id
                price_display = f"{m.price:.2f} лв." if m.price else "-"

            rows.append([
                m.date[:16],
                m.movement_type.name,
                product_name,
                qty,
                price_display,
                loc_display
            ])

        print()
        print(format_table(columns, rows))
        print()
