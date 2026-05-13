from views.menu import Menu, MenuItem
from views.password_utils import format_table


class MovementView:
    def __init__(self, product_controller, movement_controller, user_controller,
                 location_controller, supplier_controller, inventory_controller):

        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller
        self.inventory_controller = inventory_controller


    def _ask_float(self, prompt, allow_empty=False, default=None):
        while True:
            val = input(prompt).strip()
            if not val and allow_empty:
                return default
            if not val:
                return None
            try:
                num = float(val)
                if num < 0:
                    print("Числото не може да е отрицателно.")
                    continue
                return num
            except ValueError:
                print("Невалидно число. Опитайте пак.")



    def _select_item(self, items, label):
        if not items:
            print(f"\nНяма {label}.\n")
            return None

        def get_id(obj):
            if label in ["продукт", "продукт за продажба"]:
                return str(obj.product_id)
            elif label == "доставчик":
                return str(obj.supplier_id)
            else:
                return str(obj.location_id)

        while True:
            print(f"\nИзбор на {label}:")
            for i, item in enumerate(items, 1):
                print(f"{i}. {item.name} (ID: {get_id(item)[:8]})")

            choice = input("\nНомер или ID (Enter за връщане): ").strip()
            if not choice:
                return None

            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(items):
                    return items[index]
                print("Невалиден номер.")
                continue

            matches = [item for item in items if get_id(item).startswith(choice)]

            if len(matches) == 1:
                return matches[0]

            if len(matches) > 1:
                print("Няколко ID започват така. Въведете повече символи.")
            else:
                print("Невалиден избор. Опитайте пак.")

    def show_menu(self, user):
        menu = Menu("Логистични операции", [
            MenuItem("1", "Доставка (вход)", self.process_delivery),
            MenuItem("2", "Продажба (изход)", self.process_sale),
            MenuItem("3", "Вътрешно преместване", self.process_transfer),
            MenuItem("0", "Назад", lambda u: "break")])

        while True:
            choice = menu.show()
            if choice in ("0", None):
                break
            if menu.execute(choice, user) == "break":
                break



    def process_delivery(self, user):
        print("\nНова доставка")
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return

        supplier = self._select_item(self.supplier_controller.get_all(), "доставчик")
        if not supplier:
            return

        location = self._select_item(self.location_controller.get_all(), "склад за съхранение")
        if not location:
            return

        qty = self._ask_float(f"Количество ({product.unit}): ")
        if qty is None:
            return

        price = self._ask_float(f"Цена (Enter за {product.price} лв.): ", allow_empty=True, default=product.price)
        if price == "cancel":
            return

        # 🔥 ПЪЛНИ UUID — НИКАКВИ [:8]
        movement = self.movement_controller.add_in(
            str(product.product_id),
            qty,
            price,
            str(location.location_id),
            str(supplier.supplier_id),
            str(user.user_id)
        )

        if not movement:
            return

        print(f"\nДобавени {qty:.2f} {product.unit} от {product.name}.")



    def _get_locations_with_stock(self, product):
        valid = []
        for loc in self.location_controller.get_all():
            stock = self.inventory_controller.get_stock(str(product.product_id), str(loc.location_id))
            if stock > 0:
                valid.append((loc, f"{loc.name} (налично: {stock:.2f} {product.unit})"))
        return valid


    def _select_location_for_sale(self, product):
        valid = self._get_locations_with_stock(product)
        if not valid:
            print(f"\n'{product.name}' не е наличен в нито един склад.")
            return None

        print("\nИзбор на склад за продажба:")
        for i, (_, text) in enumerate(valid, 1):
            print(f"{i}. {text}")

        choice = input("\nНомер (Enter за връщане): ").strip()
        if not choice.isdigit():
            return None

        idx = int(choice) - 1
        if 0 <= idx < len(valid):
            return valid[idx][0]

        return None


    def process_sale(self, user):
        print("\nНова продажба")
        selected = self._select_item(self.product_controller.get_all(), "продукт за продажба")
        if not selected:
            return

        product = self.product_controller.get_by_id(str(selected.product_id))
        location = self._select_location_for_sale(product)
        if not location:
            return

        customer = input("Клиент (Enter за 'Общ клиент'): ").strip() or "Общ клиент"

        max_stock = self.inventory_controller.get_stock(str(product.product_id), str(location.location_id))
        qty = self._ask_float(f"Количество (макс {max_stock}): ")
        if qty is None:
            return
        if qty > max_stock:
            print(f"Няма толкова наличност ({max_stock}).")
            return

        sale_price = self._ask_float(f"Цена (Enter за {product.price} лв.): ", allow_empty=True, default=product.price)
        if sale_price == "cancel":
            return

        try:
            self.movement_controller.add_out(
                str(product.product_id),
                qty,
                customer,
                str(location.location_id),
                str(user.user_id),
                sale_price
            )
            print(f"\nПродадени {qty:.2f} {product.unit} на {customer}.")
        except Exception as e:
            print(f"Проблем при продажбата: {e}")

    def process_transfer(self, user):
        print("\nВътрешно преместване")

        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return

        product_id = str(product.product_id)

        print("\nСкладове, в които има наличност от този продукт:")

        valid_sources = []
        for loc in self.location_controller.get_all():
            loc_id = str(loc.location_id)
            qty = self.inventory_controller.get_stock(product_id, loc_id)
            if qty > 0:
                valid_sources.append((loc, qty))

        if not valid_sources:
            print(f"\n'{product.name}' не е наличен в нито един склад.")
            return

        for i, (loc, qty) in enumerate(valid_sources, 1):
            print(f"{i}. {loc.name} ({loc.location_id}) – {qty:.2f} {product.unit}")

        choice = input("\nИзберете склад ИЗТОЧНИК: ").strip()
        if not choice.isdigit():
            print("Невалиден избор.")
            return

        idx = int(choice) - 1
        if idx < 0 or idx >= len(valid_sources):
            print("Невалиден избор.")
            return

        from_loc = valid_sources[idx][0]
        from_loc_id = str(from_loc.location_id)
        available = valid_sources[idx][1]

        print(f"\nИзбран склад ИЗТОЧНИК: {from_loc.name} (налично: {available:.2f} {product.unit})")

        print("\nИзбор на склад ПОЛУЧАТЕЛ:")
        all_locs = [loc for loc in self.location_controller.get_all() if str(loc.location_id) != from_loc_id]

        for i, loc in enumerate(all_locs, 1):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")

        choice = input("\nНомер или ID (Enter за връщане): ").strip()
        if not choice:
            return

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(all_locs):
                to_loc = all_locs[idx]
            else:
                print("Невалиден избор.")
                return
        else:
            matches = [loc for loc in all_locs if str(loc.location_id).startswith(choice)]
            if len(matches) == 1:
                to_loc = matches[0]
            else:
                print("Невалиден избор.")
                return

        to_loc_id = str(to_loc.location_id)

        qty = self._ask_float(f"Количество ({product.unit}, макс {available}): ")
        if qty is None:
            return
        if qty > available:
            print(f"Няма толкова наличност ({available}).")
            return

        try:
            self.movement_controller.move_stock(
                product_id,
                qty,
                from_loc_id,
                to_loc_id,
                str(user.user_id)
            )
            print(f"\nПреместени {qty:.2f} {product.unit} от {from_loc.name} към {to_loc.name}.")
        except Exception as e:
            print(f"Проблем при преместването: {e}")
