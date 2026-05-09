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

    # --- Помощни методи за конзолна валидация (While True) ---

    def _ask_float(self, prompt, allow_empty=False, default=None):
        """Принуждава потребителя да въведе валидно число."""
        while True:
            val = input(prompt).strip()
            if val.lower() == 'отказ': return 'cancel'
            if not val and allow_empty: return default
            try:
                num = float(val)
                if num < 0:
                    print("Грешка: Числото не може да е отрицателно!")
                    continue
                return num
            except ValueError:
                print("Грешка: Моля, въведете валидно число или 'отказ'.")

    def _select_item(self, items, label):
        """Интерактивен избор на обект с While True защита."""
        if not items:
            print(f"\nНяма налични {label}.\n")
            return None

        while True:
            print(f"\nИЗБОР НА {label.upper()}:")
            for i, item in enumerate(items, 1):
                item_id = getattr(item, 'product_id', getattr(item, 'location_id', getattr(item, 'supplier_id', 'ID')))
                print(f"{i}. {item.name} (ID: {item_id[:8]})")

            choice = input(f"\nИзберете номер или ID (Enter за отказ): ").strip()
            if not choice: return None
            if choice.lower() == 'отказ': return None

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    return items[index]

            # Търсене по ID
            found = next((item for item in items if
                          getattr(item, 'product_id', getattr(item, 'location_id', '')).startswith(choice.lower())),
                         None)
            if found: return found
            print("Невалиден избор. Опитайте отново.")

    # --- Основни методи на менюто ---

    def show_menu(self, user):
        menu = Menu("Логистични операции", [
            MenuItem("1", "Доставка (IN)", self.handle_in),
            MenuItem("2", "Продажба / изписване (OUT)", self.handle_out),
            MenuItem("3", "Преместване (MOVE)", self.handle_move),
            MenuItem("4", "Хронология на движенията", self.show_history),
            MenuItem("0", "Назад", lambda u: "break")])

        while True:
            choice = menu.show()
            if choice == "0" or choice is None: break
            if menu.execute(choice, user) == "break": break

    def handle_in(self, user):
        print("\n--- НОВА ДОСТАВКА ---")
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product: return
        supplier = self._select_item(self.supplier_controller.get_all(), "доставчик")
        if not supplier: return
        location = self._select_item(self.location_controller.get_all(), "склад")
        if not location: return

        qty = self._ask_float(f"Количество ({product.unit}): ")
        if qty == 'cancel': return

        price = self._ask_float(f"Цена (Enter за {product.price}): ", allow_empty=True, default=product.price)
        if price == 'cancel': return

        try:
            self.movement_controller.add_in(product.product_id, qty, price,
                                            location.location_id, supplier.supplier_id, user.user_id)
            print(f"\n[OK] Заприходени са {qty} {product.unit}.")
        except Exception as e:
            print(f"Грешка: {e}")

    def handle_out(self, user):
        print("\n--- НОВА ПРОДАЖБА ---")
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product: return
        location = self._select_item(self.location_controller.get_all(), "склад")
        if not location: return

        customer = input("Клиент (Enter за Анонимен): ").strip() or "Анонимен"

        qty = self._ask_float(f"Количество за изписване ({product.unit}): ")
        if qty == 'cancel': return

        try:
            self.movement_controller.add_out(product.product_id, qty, customer,
                                             location.location_id, user.user_id)
            print(f"\n[OK] Изписани са {qty} {product.unit}.")
        except Exception as e:
            print(f"Грешка: {e}")

    def handle_move(self, user):
        print("\n--- ПРЕМЕСТВАНЕ ---")
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product: return
        from_loc = self._select_item(self.location_controller.get_all(), "от склад")
        if not from_loc: return
        to_loc = self._select_item(self.location_controller.get_all(), "към склад")
        if not to_loc: return

        qty = self._ask_float(f"Количество за преместване: ")
        if qty == 'cancel': return

        try:
            self.movement_controller.move_stock(product.product_id, qty, from_loc.location_id,
                                                to_loc.location_id, user.user_id)
            print("\n[OK] Наличността е преместена.")
        except Exception as e:
            print(f"Грешка: {e}")

    def show_history(self, _):
        movements = self.movement_controller.get_all()
        if not movements:
            print("\nНяма записани движения.")
            return

        rows = []
        for m in reversed(movements):
            prod = self.product_controller.get_by_id(m.product_id)
            p_name = prod.name[:12] if prod else "Unknown"

            # Определяне на партньор и локация
            if m.movement_type.name == "IN":
                supp = self.supplier_controller.get_by_id(m.supplier_id)
                partner = (supp.name if supp else "Доставчик")[:12]
                loc_text = self.location_controller.get_by_id(m.location_id).name[:10]
            elif m.movement_type.name == "OUT":
                partner = (m.customer if m.customer else "Клиент")[:12]
                loc_text = self.location_controller.get_by_id(m.location_id).name[:10]
            else:
                partner = "Вътрешно"
                f_loc = self.location_controller.get_by_id(m.from_location_id)
                t_loc = self.location_controller.get_by_id(m.to_location_id)
                loc_text = f"{f_loc.name[:5]}->{t_loc.name[:5]}" if f_loc and t_loc else "MOVE"

            rows.append([m.movement_id[:8], m.date[5:16], m.movement_type.name,
                         p_name, f"{m.quantity}", partner, loc_text])

        print("\nХРОНОЛОГИЯ")
        print(format_table(["ID", "Дата", "Тип", "Продукт", "Кол.", "Партньор", "Локация"], rows))
        input("\nНатиснете Enter за връщане...")