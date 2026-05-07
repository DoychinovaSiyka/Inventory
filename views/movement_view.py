from models.product import Product
from models.location import Location
from views.menu import Menu, MenuItem
from views.password_utils import format_table


class MovementView:
    def __init__(self, product_controller, movement_controller, user_controller, location_controller,
                 supplier_controller):
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller

    def _get_product_total_qty(self, product):
        return self.movement_controller.inventory_controller.get_total_stock(product.product_id)

    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice == "0" or choice is None:
                break
            result = menu_obj.execute(choice, user)
            if result == "break":
                break

    def show_menu(self, user):
        menu = Menu("Логистични операции", [
            MenuItem("1", "Доставка (IN)", lambda u: self.handle_in(u)),
            MenuItem("2", "Продажба / изписване (OUT)", lambda u: self.handle_out(u)),
            MenuItem("3", "Преместване между складове (MOVE)", lambda u: self.handle_move(u)),
            MenuItem("4", "Хронология на движенията", lambda u: self.show_history(u)),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)

    def _select_item(self, items, label):
        if not items:
            print(f"\nНяма налични {label}.\n")
            return None

        while True:
            print(f"\nИзбор на {label}:")
            for i, item in enumerate(items, 1):
                qty_info = ""
                if isinstance(item, Product):
                    full_id = item.product_id
                    qty_info = f" | Налично: {self._get_product_total_qty(item)} {item.unit}"
                elif isinstance(item, Location):
                    full_id = item.location_id
                else:
                    full_id = getattr(item, 'supplier_id', '')

                print(f"{i}. {item.name}{qty_info} (ID: {full_id[:8]})")

            choice = input(f"\nИзберете {label} (номер/ID или 'отказ'): ").strip()
            if not choice or choice.lower() == 'отказ':
                return None

            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(items):
                    return items[index]

            choice_lower = choice.lower()
            for item in items:
                f_id = getattr(item, 'product_id',
                               getattr(item, 'location_id', getattr(item, 'supplier_id', ''))).lower()
                if f_id.startswith(choice_lower):
                    return item

            print("Невалиден избор. Опитайте отново.")

    def handle_in(self, user):
        if not user:
            print("Липсва активен потребител.")
            return

        print("\nНова доставка")
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return
        supplier = self._select_item(self.supplier_controller.get_all(), "доставчик")
        if not supplier:
            return
        location = self._select_item(self.location_controller.get_all(), "склад")
        if not location:
            return

        while True:
            qty_raw = input(f"Количество ({product.unit}): ").strip()
            if qty_raw.lower() == 'отказ':
                return
            try:
                qty = float(qty_raw)
                if qty <= 0:
                    print("Количеството трябва да е положително.")
                    continue
                break
            except ValueError:
                print("Въведете валидно число.")

        while True:
            price_raw = input(f"Цена (Enter за {product.price}): ").strip()
            if not price_raw:
                price = product.price
                break
            try:
                price = float(price_raw)
                if price < 0:
                    print("Цената не може да е отрицателна.")
                    continue
                break
            except ValueError:
                print("Въведете валидна цена.")

        try:
            self.movement_controller.add_in(
                product.product_id, qty, price, location.location_id,
                supplier.supplier_id, user.user_id
            )
            print(f"\nДобавени са {qty} {product.unit}.")
        except Exception as e:
            print(f"Грешка при запис: {e}")

    def handle_out(self, user):
        if not user:
            return

        print("\nНова продажба / изписване")
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return

        warehouses = [
            loc for loc in self.location_controller.get_all()
            if self.movement_controller.inventory_controller.get_stock_by_location(
                product.product_id, loc.location_id
            ) > 0
        ]

        if not warehouses:
            print(f"Продуктът '{product.name}' не е наличен в складовете.")
            return

        location = self._select_item(warehouses, "склад")
        if not location:
            return

        max_qty = self.movement_controller.inventory_controller.get_stock_by_location(
            product.product_id, location.location_id
        )

        customer = input("Клиент: ").strip() or "Анонимен"

        while True:
            qty_raw = input(f"Количество (макс {max_qty}): ").strip()
            if qty_raw.lower() == 'отказ':
                return
            try:
                qty = float(qty_raw)
                if qty <= 0:
                    print("Количеството трябва да е над 0.")
                    continue
                if qty > max_qty:
                    print(f"Недостатъчна наличност (налично: {max_qty}).")
                    continue
                break
            except ValueError:
                print("Въведете число.")

        try:
            self.movement_controller.add_out(
                product.product_id, qty, customer, location.location_id, user.user_id
            )
            print(f"\nИзписани са {qty} {product.unit}.")
        except Exception as e:
            print(f"Грешка при изписване: {e}")

    def handle_move(self, user):
        if not user:
            return

        print("\nПреместване между складове")
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return

        from_loc = self._select_item(self.location_controller.get_all(), "изходен склад")
        if not from_loc:
            return

        max_qty = self.movement_controller.inventory_controller.get_stock_by_location(
            product.product_id, from_loc.location_id
        )

        if max_qty <= 0:
            print(f"Няма наличност от '{product.name}' в този склад.")
            return

        to_loc = self._select_item(self.location_controller.get_all(), "целеви склад")
        if not to_loc or to_loc.location_id == from_loc.location_id:
            print("Невалиден избор на склад.")
            return

        while True:
            qty_raw = input(f"Количество (налично {max_qty}): ").strip()
            if qty_raw.lower() == 'отказ':
                return
            try:
                qty = float(qty_raw)
                if 0 < qty <= max_qty:
                    break
                print(f"Невалидно количество (налично: {max_qty}).")
            except ValueError:
                print("Въведете число.")

        try:
            self.movement_controller.move_stock(
                product.product_id, qty, from_loc.location_id,
                to_loc.location_id, user.user_id
            )
            print("\nПреместването е извършено.")
        except Exception as e:
            print(f"Грешка при преместване: {e}")

    def show_history(self, _):
        print("\nИстория на движенията")

        results = None

        try:
            results = self.movement_controller.get_all()
        except:
            pass

        if results is None:
            try:
                results = self.movement_controller.movements
            except:
                results = None

        if isinstance(results, dict):
            temp_list = []
            for key in results:
                temp_list.append(results[key])
            results = temp_list

        if results is None or len(results) == 0:
            print("\nНяма записани движения.\n")
            input("Натиснете Enter...")
            return

        columns = ["ID", "Дата", "Тип", "Продукт", "Кол.", "Партньор", "Склад/Път"]
        rows = []

        reversed_list = list(results)
        reversed_list.reverse()

        for m in reversed_list:
            product_obj = self.product_controller.get_by_id(m.product_id)

            if product_obj is not None:
                product_name = product_obj.name
                product_unit = product_obj.unit
            else:
                product_name = "Unknown"
                product_unit = ""

            if m.movement_type.name == "IN":
                supplier_obj = self.supplier_controller.get_by_id(m.supplier_id)
                partner = supplier_obj.name if supplier_obj else "Доставчик"

            elif m.movement_type.name == "OUT":
                partner = m.customer if m.customer else "Клиент"

            else:
                partner = "Вътрешно"

            if m.movement_type.name == "MOVE":
                from_loc = self.location_controller.get_by_id(m.from_location_id)
                to_loc = self.location_controller.get_by_id(m.to_location_id)

                if from_loc and to_loc:
                    location_text = from_loc.name[:8] + "->" + to_loc.name[:8]
                else:
                    location_text = "MOVE"
            else:
                loc_obj = self.location_controller.get_by_id(m.location_id)
                location_text = loc_obj.name if loc_obj else "-"

            short_id = m.movement_id[:8]
            short_date = m.date[5:16]
            short_type = m.movement_type.name
            short_product = product_name[:12]
            quantity_text = str(m.quantity) + " " + product_unit
            short_partner = partner[:12]

            row = [
                short_id, short_date, short_type, short_product,
                quantity_text, short_partner, location_text
            ]

            rows.append(row)

        print("\n" + format_table(columns, rows))
        input("\nНатиснете Enter за връщане...")
