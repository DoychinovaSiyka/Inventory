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

    # ПОМОЩНИ МЕТОДИ

    def _ask_float(self, prompt, allow_empty=False, default=None):
        while True:
            val = input(prompt).strip()

            if val.lower() == "отказ":
                return "cancel"

            if not val and allow_empty:
                return default

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

        while True:
            print(f"\nИзбор на {label}:")
            for i, item in enumerate(items, 1):

                if label in ["продукт", "продукт за продажба"]:
                    item_id = item.product_id
                elif label == "доставчик":
                    item_id = item.supplier_id
                elif label in ["склад", "склад за съхранение", "склад ИЗТОЧНИК", "склад ПОЛУЧАТЕЛ"]:
                    item_id = item.location_id
                else:
                    item_id = "ID"

                print(f"{i}. {item.name} (ID: {str(item_id)[:8]})")

            choice = input("\nНомер или ID (Enter за отказ): ").strip()

            if not choice or choice.lower() == "отказ":
                return None

            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(items):
                    return items[index]
                print("Невалиден номер.")
                continue

            for item in items:
                if label in ["продукт", "продукт за продажба"]:
                    item_id = str(item.product_id)
                elif label == "доставчик":
                    item_id = str(item.supplier_id)
                elif label in ["склад", "склад за съхранение", "склад ИЗТОЧНИК", "склад ПОЛУЧАТЕЛ"]:
                    item_id = str(item.location_id)
                else:
                    item_id = ""

                if item_id.startswith(choice):
                    return item

            print("Невалиден избор. Опитайте пак.")

    # ГЛАВНО МЕНЮ

    def show_menu(self, user):
        menu = Menu("Логистични операции", [
            MenuItem("1", "Доставка (вход)", self.process_delivery),
            MenuItem("2", "Продажба (изход)", self.process_sale),
            MenuItem("3", "Вътрешно преместване", self.process_transfer),
            MenuItem("4", "Хронология", self.show_history),
            MenuItem("0", "Назад", lambda u: "break")
        ])

        while True:
            choice = menu.show()
            if choice == "0" or choice is None:
                break
            if menu.execute(choice, user) == "break":
                break

    # ДОСТАВКА (IN)

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
        if qty == "cancel":
            return

        price = self._ask_float(
            f"Цена (Enter за {product.price} лв.): ",
            allow_empty=True,
            default=product.price
        )
        if price == "cancel":
            return

        try:
            self.movement_controller.add_in(
                product.product_id,
                qty,
                price,
                location.location_id,
                supplier.supplier_id,
                user.user_id
            )
            print(f"\nДобавени {qty:.2f} {product.unit} от {product.name}.")
        except Exception as e:
            print(f"Проблем при запис: {e}")

    # ПРОДАЖБА (OUT)

    def _get_locations_with_stock(self, product):
        valid = []
        for loc in self.location_controller.get_all():
            stock = self.inventory_controller.get_stock(product.product_id, loc.location_id)
            if stock > 0:
                valid.append((loc, f"{loc.name} (налично: {stock:.2f} {product.unit})"))
        return valid

    def _select_location_for_sale(self, product):
        valid = self._get_locations_with_stock(product)

        if not valid:
            print(f"\n'{product.name}' не е наличен в нито един склад.")
            input("Enter за връщане...")
            return None

        print("\nИзбор на склад за продажба:")
        for i, (_, text) in enumerate(valid, 1):
            print(f"{i}. {text}")

        choice = input("\nНомер (Enter за отказ): ").strip()
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

        product = self.product_controller.get_by_id(selected.product_id)

        location = self._select_location_for_sale(product)
        if not location:
            return

        customer = input("Клиент (Enter за 'Общ клиент'): ").strip() or "Общ клиент"

        max_stock = self.inventory_controller.get_stock(product.product_id, location.location_id)
        qty = self._ask_float(f"Количество (макс {max_stock}): ")
        if qty == "cancel":
            return
        if qty > max_stock:
            print(f"Няма толкова наличност ({max_stock}).")
            return

        sale_price = self._ask_float(
            f"Цена (Enter за {product.price} лв.): ",
            allow_empty=True,
            default=product.price
        )
        if sale_price == "cancel":
            return

        try:
            self.movement_controller.add_out(
                product.product_id,
                qty,
                customer,
                location.location_id,
                user.user_id,
                sale_price
            )
            print(f"\nПродадени {qty:.2f} {product.unit} на {customer}.")
        except Exception as e:
            print(f"Проблем при продажбата: {e}")

    # ПРЕМЕСТВАНЕ (MOVE)

    def process_transfer(self, user):
        print("\nВътрешно преместване")

        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return

        from_loc = self._select_item(self.location_controller.get_all(), "склад ИЗТОЧНИК")
        if not from_loc:
            return

        to_loc = self._select_item(self.location_controller.get_all(), "склад ПОЛУЧАТЕЛ")
        if not to_loc:
            return

        if from_loc.location_id == to_loc.location_id:
            print("Двата склада съвпадат.")
            return

        qty = self._ask_float(f"Количество ({product.unit}): ")
        if qty == "cancel":
            return

        try:
            self.movement_controller.move_stock(
                product.product_id,
                qty,
                from_loc.location_id,
                to_loc.location_id,
                user.user_id
            )
            print(f"\nПреместени {qty:.2f} {product.unit}.")
        except Exception as e:
            print(f"Проблем при преместването: {e}")

    # ХРОНОЛОГИЯ

    def _format_movement_row(self, m):
        prod = self.product_controller.get_by_id(m.product_id)
        p_name = prod.name[:15] if prod else "---"

        m_type = m.movement_type.name if hasattr(m.movement_type, "name") else str(m.movement_type)

        if m_type == "IN":
            supp = self.supplier_controller.get_by_id(m.supplier_id)
            partner = (supp.name if supp else "Доставчик")[:12]
            loc = self.location_controller.get_by_id(m.location_id)
            loc_text = loc.name[:10] if loc else "Склад"

        elif m_type == "OUT":
            partner = (m.customer if m.customer else "Клиент")[:12]
            loc = self.location_controller.get_by_id(m.location_id)
            loc_text = loc.name[:10] if loc else "Склад"

        else:
            partner = "Трансфер"
            f_loc = self.location_controller.get_by_id(m.from_location_id)
            t_loc = self.location_controller.get_by_id(m.to_location_id)
            loc_text = f"{f_loc.name[:5]}->{t_loc.name[:5]}" if f_loc and t_loc else "MOVE"

        return [
            str(m.movement_id)[:8],
            str(m.date)[5:16],
            m_type,
            p_name,
            f"{m.quantity:.2f}",
            f"{float(m.price):.2f}",
            partner,
            loc_text
        ]

    def show_history(self, _):
        movements = self.movement_controller.get_all()
        if not movements:
            print("\nНяма движения.")
            return

        rows = [self._format_movement_row(m) for m in reversed(movements)]

        print("\nХронология на движенията")
        headers = ["ID", "Дата", "Тип", "Продукт", "К-во", "Цена", "Партньор", "Локация"]
        print(format_table(headers, rows))
        input("\nEnter за връщане...")
