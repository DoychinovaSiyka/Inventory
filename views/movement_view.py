from models.product import Product
from models.location import Location
from models.supplier import Supplier
from views.menu import Menu, MenuItem
from views.password_utils import format_table
from validators.movement_validator import MovementValidator
import textwrap, uuid


class MovementView:
    def __init__(self, product_controller, movement_controller, user_controller,
                 location_controller, supplier_controller=None):

        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller
        self.menu = self._build_menu()

    @staticmethod
    def _format_qty_unit(q, unit):
        if q is None: return "0"
        return f"{q} {unit}" if unit else str(q)

    def _build_menu(self):
        return Menu("Меню за Доставки/Продажби/Премествания", [
            MenuItem("1","Създаване на доставка/продажба (IN/OUT)", self.create_movement),
            MenuItem("2","Преместване между локации (MOVE)", self.move_between_locations),
            MenuItem("3","Търсене на движения", self.search_movements),
            MenuItem("4","Покажи всички движения", self.show_all),
            MenuItem("5","Разширено филтриране", self.advanced_filter),
            MenuItem("0","Назад", lambda u: "break")
        ])

    def _get_inventory(self):
        return self.product_controller.inventory_controller.data["products"]

    def _get_product_total_qty(self, product):
        pdata = self._get_inventory().get(product.product_id, {})
        return sum(float(q) for q in pdata.get("locations", {}).values())

    def _get_product_warehouses_with_qty(self, product):
        pdata = self._get_inventory().get(product.product_id, {})
        loc_qty = pdata.get("locations", {})
        result = []
        for loc in self.location_controller.get_all():
            if loc.location_id in loc_qty:
                qty = float(loc_qty[loc.location_id])
                result.append((loc.location_id, qty, product.unit))
        return result

    def _get_item_qty_text(self, item):
        if isinstance(item, Product):
            total = self._get_product_total_qty(item)
            return f" – {total} {item.unit}"
        return ""

    def _get_product_locations(self, product):
        wh = self._get_product_warehouses_with_qty(product)
        ids = sorted({loc for (loc,_,_) in wh})
        return ", ".join(ids)

    def _select_item(self, items, label):
        if not items:
            print(f"Няма налични {label}.")
            return None

        while True:
            print(f"\nИзберете {label}:")
            for i, item in enumerate(items, start=1):
                # Определяне на ID според типа
                if isinstance(item, Product):
                    item_id = item.product_id
                elif isinstance(item, Location):
                    item_id = item.location_id
                else:
                    item_id = item.supplier_id

                # Количество (ако е продукт)
                qty_text = self._get_item_qty_text(item)

                print(f"{i}. {item.name}{qty_text} (ID: {item_id})")

                # Показване на локации за продукт
                if isinstance(item, Product):
                    locs = self._get_product_locations(item)
                    if locs:
                        print(f"   Намира се в: {locs}")

            raw = input("Номер или ID (Enter = отказ): ").strip()

            # Enter = отказ
            if raw == "":
                print("Операцията е отказана.")
                return None

            # Избор по номер
            if raw.isdigit():
                idx = int(raw) - 1
                if 0 <= idx < len(items):
                    return items[idx]
                else:
                    print("Невалиден номер. Опитайте отново.\n")
                    continue

            # Избор по ID
            raw_l = raw.lower()
            for item in items:
                if isinstance(item, Product):
                    iid = item.product_id
                elif isinstance(item, Location):
                    iid = item.location_id
                else:
                    iid = item.supplier_id

                if iid.lower() == raw_l:
                    return item

            print("Невалиден ID. Опитайте отново.\n")

    def show_menu(self):
        user = self.user_controller.logged_user
        if not user:
            print("Трябва да сте логнат."); return
        while True:
            if self.menu.execute(self.menu.show(), user) == "break": break

    def create_movement(self, user):
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return

        print("\n0 - Доставка (IN)\n1 - Продажба (OUT)")
        # Логика за избор на IN/OUT
        while True:
            mt_raw = input("Избор (0/1, Enter = отказ): ").strip()

            if mt_raw == "":
                print("Операцията е отказана.")
                return

            if mt_raw == "0":
                movement_type = "IN"
                break
            elif mt_raw == "1":
                movement_type = "OUT"
                break
            else:
                print("[!] Невалиден избор. Моля, въведете 0 или 1.\n")

        # OUT – избор само от складове с наличност
        if movement_type == "OUT":
            wh_list = self._get_product_warehouses_with_qty(product)
            if not wh_list:
                print("\nГрешка: Няма наличност за този продукт в нито един склад.")
                return

            if len(wh_list) == 1:
                loc_id, qty, unit = wh_list[0]
                location = self.location_controller.get_by_id(loc_id)
                print(f"\nИзбран склад: {location.name} – {qty} {unit} (ID: {loc_id})")
            else:
                print("\nИзберете склад (само от тези с наличност):")
                for i, (loc_id, qty, unit) in enumerate(wh_list, start=1):
                    loc = self.location_controller.get_by_id(loc_id)
                    print(f"{i}. {loc.name} – {qty} {unit} (ID: {loc_id})")

                raw = input("Ваш избор: ").strip()
                chosen = None

                if raw.isdigit():
                    idx = int(raw) - 1
                    if 0 <= idx < len(wh_list):
                        chosen = wh_list[idx][0]
                else:
                    for loc_id, _, _ in wh_list:
                        if loc_id.lower() == raw.lower():
                            chosen = loc_id

                if not chosen:
                    print("Невалиден склад.")
                    return

                location = self.location_controller.get_by_id(chosen)

        else:
            # IN – истинска доставка - позволяваме ВСЕКИ склад
            all_locs = self.location_controller.get_all()
            if not all_locs:
                print("Грешка: Няма дефинирани локации.")
                return

            print("\nИзберете склад за доставка:")
            for idx, loc in enumerate(all_locs, start=1):
                print(f"{idx}. {loc.name} (ID: {loc.location_id})")

            raw = input("Номер или ID (Enter = отказ): ").strip()
            if raw == "":
                return

            chosen_loc = None

            if raw.isdigit():
                num = int(raw)
                for idx, loc in enumerate(all_locs, start=1):
                    if idx == num:
                        chosen_loc = loc
                        break
            else:
                raw_l = raw.lower()
                for loc in all_locs:
                    if loc.location_id.lower() == raw_l:
                        chosen_loc = loc
                        break

            if not chosen_loc:
                print("Грешка: Невалиден избор на локация.")
                return

            location = chosen_loc

        while True:
            quantity_raw = input("Количество: ").strip()
            try:
                qty = MovementValidator.parse_quantity(quantity_raw)
                break
            except Exception:
                print("Грешка: количеството трябва да е валидно число (пример: 5 или 12.5). Опитайте отново.\n")

        while True:
            price_raw = input("Цена: ").strip()
            try:
                prc = MovementValidator.parse_price(price_raw)
                break
            except Exception:
                print("Грешка: цената трябва да е валидно число (пример: 4.99). Опитайте отново.\n")

        # описание – цикъл докато е валидно
        while True:
            description = input("Описание: ").strip()
            if len(description) >= 3:
                break
            print("Грешка: описанието трябва да е поне 3 символа. Опитайте отново.\n")

        supplier_id = None
        customer = None

        if movement_type == "IN":
            # доставка - избираме доставчик
            all_suppliers = self.supplier_controller.get_all()

            print("\nИзберете доставчик:")
            for idx, s in enumerate(all_suppliers, start=1):
                print(f"{idx}. {s.name} (ID: {s.supplier_id})")

            while True:
                raw = input("Номер или ID (Enter = отказ): ").strip()

                if raw == "":
                    print("Грешка: Доставката изисква избран доставчик.")
                    continue

                supplier = None

                if raw.isdigit():
                    num = int(raw)
                    for idx, s in enumerate(all_suppliers, start=1):
                        if idx == num:
                            supplier = s
                            break
                else:
                    raw_l = raw.lower()
                    for s in all_suppliers:
                        if s.supplier_id.lower() == raw_l:
                            supplier = s
                            break

                if supplier:
                    break

                print("Грешка: Невалиден избор на доставчик.")
                print("Моля, опитайте отново.\n")

            supplier_id = supplier.supplier_id

        if movement_type == "OUT":
            customer = input("Име на клиент: ").strip() or None

        try:
            mv = self.movement_controller.add(product_id=product.product_id, user_id=user.user_id, location_id=location.location_id,
                                              movement_type=movement_type, quantity=qty, description=description,
                                              price=prc, customer=customer, supplier_id=supplier_id)

            print("\nДвижението е добавено успешно!")
            print(f"ID: {mv.movement_id}")

        except ValueError as e:
            print("Грешка:", e)

    def move_between_locations(self, user):
        print("\n   Преместване между локации (MOVE)   ")
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product: return

        wh_list = self._get_product_warehouses_with_qty(product)
        qty_by_wh = {loc: (qty,unit) for (loc,qty,unit) in wh_list}

        if not wh_list:
            print("Грешка: Няма наличност за този продукт в нито един склад."); return

        all_locs = self.location_controller.get_all()
        if not all_locs:
            print("Грешка: Няма дефинирани локации."); return

        print("\nИзберете ИЗХОДНА локация:")
        for i,loc in enumerate(all_locs, start=1):
            qty,unit = qty_by_wh.get(loc.location_id, (0.0, product.unit))
            print(f"{i}. {loc.name} – {qty} {unit} (ID: {loc.location_id})")

        raw = input("Номер или ID: ").strip()
        if raw == "": return

        from_loc = None
        if raw.isdigit():
            idx = int(raw)-1
            if 0 <= idx < len(all_locs): from_loc = all_locs[idx].location_id
        else:
            for loc in all_locs:
                if loc.location_id.lower() == raw.lower(): from_loc = loc.location_id

        if not from_loc:
            print("Невалидна изходна локация."); return

        from_qty,_ = qty_by_wh.get(from_loc, (0.0, product.unit))
        if from_qty <= 0:
            print("Грешка: Няма наличност в избраната изходна локация."); return

        targets = [loc for loc in all_locs if loc.location_id != from_loc]
        if not targets:
            print("Грешка: Няма друга локация, към която да се премести."); return

        print("\nИзберете ЦЕЛЕВА локация:")
        for i,loc in enumerate(targets, start=1):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")

        raw = input("Номер или ID: ").strip()
        if raw == "": return

        to_loc = None
        if raw.isdigit():
            idx = int(raw)-1
            if 0 <= idx < len(targets): to_loc = targets[idx].location_id
        else:
            for loc in targets:
                if loc.location_id.lower() == raw.lower(): to_loc = loc.location_id

        if not to_loc:
            print("Невалидна целева локация."); return

        # количество – цикъл докато е валидно
        while True:
            qty_raw = input("Количество за преместване: ").strip()
            try:
                qty = MovementValidator.parse_quantity(qty_raw)
                break
            except Exception:
                print("Грешка: количеството трябва да е валидно число. Опитайте отново.\n")

        desc = input("Описание (по избор): ")

        try:
            mv = self.movement_controller.move_product(product_id=product.product_id,user_id=user.user_id,
                from_loc=from_loc, to_loc=to_loc, quantity=qty, description=desc)
            print("\nПреместването е извършено успешно!")
            print(f"ID: {mv.movement_id}")

        except ValueError as e:
            print("Грешка:", e)

    def search_movements(self, _):
        kw = input("Търси по описание (мин. 3 символа, Enter = отказ): ").strip()
        if kw == "":
            print("Операцията е отказана.")
            return
        if len(kw) < 3:
            print("Моля, въведете поне 3 символа.")
            return

        results = self.movement_controller.search_by_description(kw)
        if not results:
            print("Няма намерени движения."); return

        def short(t, n=60):
            if not t: return ""
            t = t.strip()
            return t if len(t) <= n else t[:n] + "..."

        columns = ["ID","Дата","Тип","Количество","Описание"]
        rows = [[m.movement_id, m.date, m.movement_type.name,
                 self._format_qty_unit(m.quantity, m.unit),
                 short(m.description,60)] for m in results]

        print(format_table(columns, rows)); print()

        choice = input("ID за детайли или Enter: ").strip()
        if not choice: return

        mv = self.movement_controller.get_by_id(choice)
        if not mv:
            print("\nНевалидно ID.\n"); return

        print("\n--- Детайли за движение ---")
        print(f"ID: {mv.movement_id}")
        print(f"Дата: {mv.date}")
        print(f"Тип: {mv.movement_type.name}")
        print(f"Количество: {self._format_qty_unit(mv.quantity, mv.unit)}")

        if mv.movement_type.name == "MOVE":
            print(f"От: {mv.from_location_id}")
            print(f"До: {mv.to_location_id}")
        else:
            print(f"Локация: {mv.location_id}")

        if mv.price: print(f"Цена: {mv.price} лв.")
        if mv.customer: print(f"Клиент: {mv.customer}")
        if mv.supplier_id: print(f"Доставчик ID: {mv.supplier_id}")

        print("\nОписание:")
        print(mv.description or "(няма)")
        print("-----------------------------\n")

    def show_all(self, _):
        mv = self.movement_controller.movements
        if not mv:
            print("Няма движения."); return

        columns = ["ID","Дата","Тип","Количество"]
        rows = [[m.movement_id, m.date, m.movement_type.name,
                 self._format_qty_unit(m.quantity, m.unit)] for m in mv]

        print(format_table(columns, rows))

    def advanced_filter(self, _):
        print("\n   Разширено филтриране на движения   ")
        print("0=IN, 1=OUT, 2=MOVE")

        errors = []
        m_type_input = input("Тип movement или Enter: ").strip() or None
        movement_type = None

        if m_type_input:
            movement_type = {"0":"IN","1":"OUT","2":"MOVE"}.get(m_type_input)
            if not movement_type:
                errors.append("Невалиден тип движение.")

        start_date = input("Начална дата (YYYY-MM-DD) или Enter: ").strip() or None
        end_date   = input("Крайна дата (YYYY-MM-DD) или Enter: ").strip() or None

        from datetime import datetime
        if start_date:
            try: datetime.strptime(start_date,"%Y-%m-%d")
            except: errors.append("Невалидна начална дата.")
        if end_date:
            try: datetime.strptime(end_date,"%Y-%m-%d")
            except: errors.append("Невалидна крайна дата.")

        product_id = input("ID на продукт или Enter: ").strip() or None
        if product_id:
            try:
                uuid.UUID(product_id)
                if not self.product_controller.get_by_id(product_id):
                    errors.append("Несъществуващ продукт.")
            except:
                errors.append("Невалиден формат за ID на продукт.")

        location_id = input("ID на локация или Enter: ").strip() or None
        if location_id:
            try:
                uuid.UUID(location_id)
                if not self.location_controller.get_by_id(location_id):
                    errors.append("Несъществуваща локация.")
            except:
                errors.append("Невалиден формат за ID на локация.")

        user_id = input("ID на потребител или Enter: ").strip() or None
        if user_id:
            try:
                uuid.UUID(user_id)
                if not self.user_controller.get_by_id(user_id):
                    errors.append("Несъществуващ потребител.")
            except:
                errors.append("Невалиден формат за ID на потребител.")

        if errors:
            print("\n[!] Открити са грешки:")
            for e in errors:
                print(" - " + e)
            print("\nМоля, коригирайте и опитайте отново.\n")
            return

        results = self.movement_controller.advanced_filter(movement_type=movement_type,
                                                           start_date=start_date, end_date=end_date, product_id=product_id,
                                                           location_id=location_id, user_id=user_id)
        if not results:
            print("\nНяма движения по тези критерии.\n")
            return

        rows = []
        columns = ["Дата","Тип","Продукт","Количество","Цена/Инфо","Локация"]

        for m in results:
            product = self.product_controller.get_by_id(m.product_id)
            pname = product.name if product else m.product_id
            qty = self._format_qty_unit(m.quantity, m.unit)

            if m.movement_type.name == "MOVE":
                loc_from = self.location_controller.get_by_id(m.from_location_id)
                loc_to = self.location_controller.get_by_id(m.to_location_id)
                loc_disp = f"{loc_from.name if loc_from else m.from_location_id} → {loc_to.name if loc_to else m.to_location_id}"
                price_disp = "-"
            else:
                loc = self.location_controller.get_by_id(m.location_id)
                loc_disp = loc.name if loc else m.location_id
                price_disp = f"{m.price:.2f} лв." if m.price else "-"

            rows.append([m.date[:16], m.movement_type.name, pname, qty, price_disp, loc_disp])

        print()
        print(format_table(columns, rows))
        print()
