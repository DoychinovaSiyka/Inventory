from models.product import Product
from models.location import Location
from models.supplier import Supplier
from views.menu import Menu, MenuItem
from views.password_utils import format_table
from validators.movement_validator import MovementValidator


class MovementView:
    def __init__(self, product_controller, movement_controller, user_controller, location_controller, supplier_controller):

        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller


    @staticmethod
    def _format_qty_unit(quantity, unit):
        """Форматира количество + мерна единица."""
        if quantity is None:
            return "0"
        if unit:
            return f"{quantity} {unit}"
        return str(quantity)

    def _get_inventory(self):
        """Връща инвентара от контролера."""
        inventory_data = self.movement_controller.inventory_controller.data
        return inventory_data.get("products", {})

    def _get_product_total_qty(self, product):
        """Общо количество от всички локации."""
        inventory = self._get_inventory()
        product_entry = inventory.get(product.product_id, {})
        locations = product_entry.get("locations", {})
        total = 0.0
        for qty in locations.values():
            try:
                total += float(qty)
            except:
                pass
        return total

    def _get_product_warehouses_with_qty(self, product):
        """Връща списък от Location обекти, където продуктът е наличен."""
        inventory = self._get_inventory()
        product_entry = inventory.get(product.product_id, {})
        loc_qty = product_entry.get("locations", {})

        result = []
        for loc_id, qty in loc_qty.items():
            try:
                if float(qty) > 0:
                    loc_obj = self.location_controller.get_by_id(loc_id)
                    if loc_obj:
                        result.append(loc_obj)
            except:
                continue
        return result

    def _select_item(self, items, label):
        """Класически избор на елемент от списък."""
        if not items:
            print(f"\nНяма налични {label}.\n")
            return None

        while True:
            print(f"\nИзберете {label}:")
            index = 1
            for item in items:
                if isinstance(item, Product):
                    item_id = item.product_id
                    total_qty = self._get_product_total_qty(item)
                    qty_text = f" – {total_qty} {item.unit}"
                elif isinstance(item, Location):
                    item_id = item.location_id
                    qty_text = ""
                else:
                    item_id = item.supplier_id
                    qty_text = ""

                print(f"{index}. {item.name}{qty_text} (ID: {item_id})")
                index += 1

            raw = input("Номер или ID (Enter = отказ): ").strip()
            if raw == "":
                print("Операцията е отказана.")
                return None

            if raw.isdigit():
                pos = int(raw) - 1
                if 0 <= pos < len(items):
                    return items[pos]
                print("Невалиден номер.\n")
                continue

            raw_lower = raw.lower()
            for item in items:
                if isinstance(item, Product):
                    iid = item.product_id
                elif isinstance(item, Location):
                    iid = item.location_id
                else:
                    iid = item.supplier_id

                if iid.lower() == raw_lower:
                    return item

            print("Невалиден ID.\n")


    def show_menu(self):
        user = self.user_controller.logged_user
        if not user:
            print("Трябва да сте логнат.")
            return

        menu_items = [MenuItem("1", "Създаване на движение (IN/OUT)", self.create_movement),
            MenuItem("2", "Преместване между локации (MOVE)", self.move_between_locations),
            MenuItem("3", "Всички движения", self.show_all_movements),
            MenuItem("4", "Филтриране на движения", self.menu_filter),
            MenuItem("0", "Назад", self._break_menu)]

        menu = Menu("ДВИЖЕНИЯ (IN / OUT / MOVE)", menu_items)

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    def _break_menu(self, _):
        return "break"

    def show_all_movements(self, _):
        movements = self.movement_controller.movements
        self._display_results(movements)


    def menu_filter(self, user):
        submenu_items = [MenuItem("1", "Само IN (доставки)", self._filter_in),
                         MenuItem("2", "Само OUT (продажби)", self._filter_out),
                         MenuItem("3", "Само MOVE (премествания)", self._filter_move),
                         MenuItem("0", "Назад", self._break_menu)]

        submenu = Menu("ФИЛТРИРАНЕ НА ДВИЖЕНИЯ", submenu_items)
        submenu.show_loop(user)

    def _filter_in(self, _):
        results = self.movement_controller.advanced_filter(movement_type="IN")
        self._display_results(results)

    def _filter_out(self, _):
        results = self.movement_controller.advanced_filter(movement_type="OUT")
        self._display_results(results)

    def _filter_move(self, _):
        results = self.movement_controller.advanced_filter(movement_type="MOVE")
        self._display_results(results)


    def _display_results(self, results):
        if not results:
            print("\nНяма движения по зададения критерий.\n")
            return

        columns = ["Дата", "Тип", "Продукт", "Количество", "Партньор", "Склад/Път"]
        rows = []

        for m in results:
            product = self.product_controller.get_by_id(m.product_id)
            product_name = product.name if product else "???"

            if m.movement_type.name == "IN":
                supplier = None
                if self.supplier_controller and m.supplier_id:
                    supplier = self.supplier_controller.get_by_id(m.supplier_id)
                partner = supplier.name if supplier else "Доставчик"

            elif m.movement_type.name == "OUT":
                if m.customer:
                    partner = f"Кл: {m.customer}"
                else:
                    partner = "Клиент"

            else:
                partner = "Вътрешно"

            if m.movement_type.name == "MOVE":
                loc_from = self.location_controller.get_by_id(m.from_location_id)
                loc_to = self.location_controller.get_by_id(m.to_location_id)
                loc_text = f"{loc_from.name if loc_from else '?'} -> {loc_to.name if loc_to else '?'}"
            else:
                loc = self.location_controller.get_by_id(m.location_id)
                loc_text = loc.name if loc else "-"

            rows.append([m.date[:16], m.movement_type.name, product_name,
                         self._format_qty_unit(m.quantity, m.unit), partner, loc_text])

        print(format_table(columns, rows))



    def create_movement(self, user):
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return

        print("\n0 - Доставка (IN)")
        print("1 - Продажба (OUT)")
        choice = input("Избор (0/1, Enter = отказ): ").strip()
        if choice == "":
            print("Операцията е отказана.")
            return

        if choice == "0":
            movement_type = "IN"
        elif choice == "1":
            movement_type = "OUT"
        else:
            print("Невалиден избор.")
            return

        if movement_type == "OUT":
            warehouses = self._get_product_warehouses_with_qty(product)
            location = self._select_item(warehouses, "склад")
        else:
            all_locations = self.location_controller.get_all()
            location = self._select_item(all_locations, "склад за доставка")

        if not location:
            return

        try:
            qty = MovementValidator.parse_quantity(input("Количество: ").strip())
            price = MovementValidator.parse_price(input("Цена: ").strip())
        except:
            print("Грешка: невалидни данни.")
            return

        supplier_id = None
        customer = None

        if movement_type == "IN":
            supplier = self._select_item(self.supplier_controller.get_all(), "доставчик")
            if not supplier:
                return
            supplier_id = supplier.supplier_id
        else:
            customer = input("Име на клиент: ").strip()
            if not customer:
                print("Клиентът е задължителен.")
                return

        try:
            mv = self.movement_controller.add(product_id=product.product_id, user_id=user.user_id, location_id=location.location_id,
                                              movement_type=movement_type, quantity=str(qty), price=str(price),
                                              customer=customer, supplier_id=supplier_id)
            print(f"\nДвижението е добавено! ID: {mv.movement_id}")
        except Exception as e:
            print("Грешка:", e)



    def move_between_locations(self, user):
        print("\n   Преместване между локации (MOVE)   ")

        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return

        from_location = self._select_item(self._get_product_warehouses_with_qty(product),"изходна локация")
        if not from_location:
            return

        all_locations = self.location_controller.get_all()
        possible_targets = []
        for loc in all_locations:
            if loc.location_id != from_location.location_id:
                possible_targets.append(loc)

        to_location = self._select_item(possible_targets, "целева локация")
        if not to_location:
            return

        qty_raw = input("Количество: ").strip()
        try:
            qty = MovementValidator.parse_quantity(qty_raw)
        except:
            print("Грешка: невалидно количество.")
            return

        try:
            mv = self.movement_controller.add(product_id=product.product_id, user_id=user.user_id, location_id=None,
                                              movement_type="MOVE", quantity=str(qty), price="0",
                                              from_location_id=from_location.location_id, to_location_id=to_location.location_id)
            print(f"\nПреместено! ID: {mv.movement_id}")
        except Exception as e:
            print("Грешка:", e)
