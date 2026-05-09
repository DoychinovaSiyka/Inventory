from views.menu import Menu, MenuItem
from views.password_utils import format_table


class MovementView:
    def __init__(self, product_controller, movement_controller, user_controller, location_controller,
                 supplier_controller, inventory_controller):
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller
        self.inventory_controller = inventory_controller

    def _ask_float(self, prompt, allow_empty=False, default=None):
        while True:
            val = input(prompt).strip()
            if val.lower() == 'отказ':
                return 'cancel'
            if not val and allow_empty:
                return default
            try:
                num = float(val)
                if num < 0:
                    print("Грешка: Числото не може да е отрицателно!")
                    continue
                return num
            except ValueError:
                print("Грешка: Моля, въведете валидно число или 'отказ'.")

    def _select_item(self, items, label):
        if not items:
            print(f"\nНяма налични {label}.\n")
            return None

        while True:
            print(f"\nИЗБОР НА {label.upper()}:")
            for i, item in enumerate(items, 1):
                item_id = getattr(item, 'product_id', getattr(item, 'location_id', getattr(item, 'supplier_id', 'ID')))
                print(f"{i}. {item.name} (ID: {str(item_id)[:8]})")

            choice = input(f"\nИзберете номер или ID (Enter за отказ): ").strip()
            if not choice: return None
            if choice.lower() == 'отказ': return None

            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(items):
                    return items[index]
                else:
                    print("Грешка: Невалиден номер.")
                    continue

            found = None
            for item in items:
                item_id = str(
                    getattr(item, 'product_id', getattr(item, 'location_id', getattr(item, 'supplier_id', ''))))
                if item_id.lower().startswith(choice.lower()):
                    found = item
                    break

            if found: return found
            print("Грешка: Невалиден избор. Опитайте отново.")

    def show_menu(self, user):
        menu = Menu("Логистични операции", [
            MenuItem("1", "Доставка (Заприхождаване)", self.process_delivery),
            MenuItem("2", "Продажба (Изписване)", self.process_sale),
            MenuItem("3", "Вътрешно преместване", self.process_transfer),
            MenuItem("4", "Хронология на движенията", self.show_history),
            MenuItem("0", "Назад", lambda u: "break")
        ])

        while True:
            choice = menu.show()
            if choice == "0" or choice is None: break
            if menu.execute(choice, user) == "break": break

    def process_delivery(self, user):
        print("\n--- НОВА ДОСТАВКА (ВХОД) ---")
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product: return

        supplier = self._select_item(self.supplier_controller.get_all(), "доставчик")
        if not supplier: return

        location = self._select_item(self.location_controller.get_all(), "склад за съхранение")
        if not location: return

        qty = self._ask_float(f"Количество ({product.unit}): ")
        if qty == 'cancel': return

        price = self._ask_float(f"Цена на доставка (Enter за {product.price}): ", allow_empty=True,
                                default=product.price)
        if price == 'cancel': return

        try:
            self.movement_controller.add_in(
                product.product_id, qty, price,
                location.location_id, supplier.supplier_id, user.user_id
            )
            print(f"\n[OK] Успешно заприходени {qty:.2f} {product.unit} от {product.name}.")
        except Exception as e:
            print(f"Грешка при запис: {e}")

    def process_sale(self, user):
        print("\n--- НОВА ПРОДАЖБА (ИЗХОД) ---")
        selected_prod = self._select_item(self.product_controller.get_all(), "продукт за продажба")
        if not selected_prod: return

        # Взимаме пресен обект от базата
        product = self.product_controller.get_by_id(selected_prod.product_id)

        valid_locations = []
        for loc in self.location_controller.get_all():
            stock = self.inventory_controller.get_stock(product.product_id, loc.location_id)
            if stock > 0:
                valid_locations.append((loc, f"{loc.name} (Налично: {stock:.2f} {product.unit})"))

        if not valid_locations:
            print(f"\nГрешка: Няма наличност от '{product.name}' в нито един склад!")
            input("Натиснете Enter за връщане...")
            return

        print("\nИЗБОР НА СКЛАД:")
        for i, (loc, disp) in enumerate(valid_locations, 1):
            print(f"{i}. {disp}")

        l_choice = input("\nИзберете номер (Enter за отказ): ").strip()
        if not l_choice or not l_choice.isdigit(): return
        idx = int(l_choice) - 1
        if not (0 <= idx < len(valid_locations)): return
        location = valid_locations[idx][0]

        customer = input("Име на клиент (Enter за 'Анонимен'): ").strip() or "Анонимен"

        max_stock = self.inventory_controller.get_stock(product.product_id, location.location_id)
        qty = self._ask_float(f"Количество за продажба (Макс: {max_stock}): ")
        if qty == 'cancel': return
        if qty > max_stock:
            print(f"Грешка: Не можете да изпишете повече от наличното ({max_stock})!")
            return

        # ТУК Е КЛЮЧЪТ: Продажна цена
        sale_price = self._ask_float(f"Цена на продажба (Enter за каталожна {product.price} лв.): ",
                                     allow_empty=True, default=product.price)
        if sale_price == 'cancel': return

        try:
            # Предаваме sale_price към оправения метод в Controller-а
            self.movement_controller.add_out(
                product.product_id, qty, customer,
                location.location_id, user.user_id, sale_price
            )
            print(f"\n[OK] Продажбата на {qty:.2f} {product.unit} е отразена успешно по {sale_price:.2f} лв.")
        except Exception as e:
            print(f"Грешка при продажбата: {e}")

    def process_transfer(self, user):
        print("\n--- ВЪТРЕШНО ПРЕМЕСТВАНЕ ---")
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product: return

        from_loc = self._select_item(self.location_controller.get_all(), "склад ИЗТОЧНИК")
        if not from_loc: return

        to_loc = self._select_item(self.location_controller.get_all(), "склад ПОЛУЧАТЕЛ")
        if not to_loc: return

        if from_loc.location_id == to_loc.location_id:
            print("Грешка: Складовете трябва да са различни!")
            return

        qty = self._ask_float(f"Количество за преместване: ")
        if qty == 'cancel': return

        try:
            self.movement_controller.move_stock(
                product.product_id, qty, from_loc.location_id,
                to_loc.location_id, user.user_id
            )
            print(f"\n[OK] Трансферът завърши успешно.")
        except Exception as e:
            print(f"Грешка: {e}")

    def show_history(self, _):
        movements = self.movement_controller.get_all()
        if not movements:
            print("\nНяма история на движенията.")
            return

        rows = []
        for m in reversed(movements):
            prod = self.product_controller.get_by_id(m.product_id)
            p_name = prod.name[:15] if prod else "---"
            m_type = m.movement_type.name if hasattr(m.movement_type, 'name') else str(m.movement_type)

            # Форматираме партньора и локацията според типа
            if m_type == "IN":
                supp = self.supplier_controller.get_by_id(m.supplier_id)
                partner = (supp.name if supp else "Доставчик")[:12]
                loc_obj = self.location_controller.get_by_id(m.location_id)
                loc_text = loc_obj.name[:10] if loc_obj else "N/A"
            elif m_type == "OUT":
                partner = (m.customer if m.customer else "Клиент")[:12]
                loc_obj = self.location_controller.get_by_id(m.location_id)
                loc_text = loc_obj.name[:10] if loc_obj else "N/A"
            else:
                partner = "Трансфер"
                f_loc = self.location_controller.get_by_id(m.from_location_id)
                t_loc = self.location_controller.get_by_id(m.to_location_id)
                loc_text = f"{f_loc.name[:5]}->{t_loc.name[:5]}" if f_loc and t_loc else "MOVE"

            rows.append([
                str(m.movement_id)[:8],
                str(m.date)[5:16],
                m_type,
                p_name,
                f"{m.quantity:.2f}",
                f"{float(m.price):.2f}",  # Добавена колона цена
                partner,
                loc_text
            ])

        print("\n--- ХРОНОЛОГИЯ НА ОПЕРАЦИИТЕ ---")
        headers = ["ID", "Дата", "Тип", "Продукт", "К-во", "Цена", "Партньор", "Локация"]
        print(format_table(headers, rows))
        input("\nНатиснете Enter за връщане...")