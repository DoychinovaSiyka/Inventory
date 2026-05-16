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


    def _float(self, prompt, allow_empty=False, default=None):
        while True:
            val = input(prompt).strip()
            if not val and allow_empty:
                return default

            if not val:
                print("Моля въведете число.")
                continue

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
            MenuItem("4", "Търсене на движения", self.advanced_search),
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

        qty = self._float(f"Количество ({product.unit}): ")
        price = self._float(f"Цена (Enter за {product.price} лв.): ",
                            allow_empty=True, default=product.price)

        movement = self.movement_controller.add_in(str(product.product_id), qty, price,
                                                   str(location.location_id), str(supplier.supplier_id),
                                                   str(user.user_id))

        print(f"\nДобавени {qty:.2f} {product.unit} от {product.name}.")




    def _get_locations_with_stock(self, product):
        valid = []
        for loc in self.location_controller.get_all():
            stock = self.inventory_controller.get_stock(str(product.product_id), str(loc.location_id))
            if stock > 0:
                valid.append((loc, stock))
        return valid

    def _select_location_for_sale(self, product):
        valid = self._get_locations_with_stock(product)
        if not valid:
            print(f"\n'{product.name}' не е наличен в нито един склад.")
            return None

        print("\nИзбор на склад за продажба:")
        for i, (loc, qty) in enumerate(valid, 1):
            print(f"{i}. {loc.name} (налично: {qty:.2f} {product.unit})")

        choice = input("\nНомер (Enter за връщане): ").strip()
        if not choice.isdigit():
            return None

        idx = int(choice) - 1
        if 0 <= idx < len(valid):
            return valid[idx][0]

        print("Невалиден избор.")
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

        max_stock = self.inventory_controller.get_stock(str(product.product_id),
                                                        str(location.location_id))


        qty = self._float(f"Количество (макс {max_stock}): ")
        if qty > max_stock:
            print(f"Няма толкова наличност ({max_stock}).")
            return

        sale_price = self._float(f"Цена (Enter за {product.price} лв.): ", allow_empty=True,
                                 default=product.price)

        try:
            self.movement_controller.add_out(str(product.product_id), qty, customer,
                                             str(location.location_id), str(user.user_id),
                                             sale_price)
            print(f"\nПродадени {qty:.2f} {product.unit} на {customer}.")
        except Exception as e:
            print(f"Проблем при продажбата: {e}")




    def process_transfer(self, user):
        print("\nВЪТРЕШНО ПРЕМЕСТВАНЕ")
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return
        product_id = str(product.product_id)


        from_loc = None
        while True:
            valid_sources = [loc for loc in self.location_controller.get_all()
                             if self.inventory_controller.get_stock(product_id, str(loc.location_id)) > 0]

            if not valid_sources:
                print(f"\nГрешка: Продуктът '{product.name}' не е наличен в нито един склад.")
                return

            from_loc = self._select_item(valid_sources, "склад ИЗТОЧНИК (с наличност)")
            if from_loc:
                break
            print("Изборът на източник е задължителен за трансфер.")
            if input("Натиснете '0' за отказ или Enter за нов опит: ").strip() == "0": return

        from_loc_id = str(from_loc.location_id)
        available = self.inventory_controller.get_stock(product_id, from_loc_id)
        print(f"--- Налично в {from_loc.name}: {available:.2f} {product.unit} ---")


        to_loc = None
        while True:
            other_locations = [loc for loc in self.location_controller.get_all()
                               if str(loc.location_id) != from_loc_id]

            if not other_locations:
                print("Грешка: Няма друг заведен склад, към който да преместите стоката.")
                return

            to_loc = self._select_item(other_locations, "склад ПОЛУЧАТЕЛ")
            if to_loc:
                break
            print(f"Не можете да преместите стока обратно в същия склад ({from_loc.name}).")
            if input("Натиснете '0' за отказ или Enter за нов опит: ").strip() == "0": return


        qty = 0
        while True:
            qty = self._float(f"Количество за местене (макс {available} {product.unit}): ")

            if 0 < qty <= available:
                break

            if qty <= 0:
                print("Грешка: Количеството трябва да е по-голямо от нула.")
            else:
                print(f"Грешка: Недостатъчна наличност. Максимумът е {available:.2f}.")

            if input("Желаете ли нов опит? (Enter за да, '0' за отказ): ").strip() == "0": return


        try:
            self.movement_controller.move_stock(product_id=product_id, quantity=qty, from_loc=from_loc_id,
                                                to_loc=str(to_loc.location_id), user_id=str(user.user_id))
            print(f"\nПреместени {qty:.2f} {product.unit} от {from_loc.name} в {to_loc.name}.")
        except Exception as e:
            print(f"\nКритична грешка при запис: {e}")


    def advanced_search(self, user):
        print("\n ТЪРСЕНЕ НА ДВИЖЕНИЯ ")
        print("1. По Тип (IN/OUT/MOVE)")
        print("2. По Продукт")
        print("3. По Дата (ГГГГ-ММ-ДД)")
        print("4. По Склад")
        print("0. Всички движения")

        choice = input("\nВашият избор: ").strip()
        search_params = {}

        if choice == "1":
            print("1. IN\n2. OUT\n3. MOVE")
            sub = input("Избор: ").strip()
            mapping = {"1": "IN", "2": "OUT", "3": "MOVE"}
            search_params["movement_type"] = mapping.get(sub, "IN")

        elif choice == "2":
            product = self._select_item(self.product_controller.get_all(), "продукт")
            if product:
                search_params["product_id"] = str(product.product_id)

        elif choice == "3":
            date_str = input("Въведете дата (ГГГГ-ММ-ДД): ").strip()
            search_params["date"] = date_str

        elif choice == "4":
            loc = self._select_item(self.location_controller.get_all(), "склад")
            if loc:
                search_params["location_id"] = str(loc.location_id)

        elif choice != "0":
            print("Невалиден избор.")
            return

        results = self.movement_controller.search_movements(**search_params)

        if not results:
            print("\nНяма намерени движения.")
            return

        headers = ["Дата", "Тип", "Продукт", "Кол.", "Склад/Обект"]
        rows = []

        for m in results:
            if m.movement_type.name == "IN":
                target = "От доставчик"
            elif m.movement_type.name == "OUT":
                target = f"Към {m.customer}"
            else:
                target = "Трансфер"

            rows.append([str(m.date)[:10], m.movement_type.name, m.product_name, f"{m.quantity} {m.unit}", target])

        print(f"\nНамерени резултати: {len(results)}")
        print(format_table(headers, rows))
