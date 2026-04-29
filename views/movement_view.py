from models.product import Product
from models.location import Location
from models.supplier import Supplier
from views.menu import Menu, MenuItem
from views.password_utils import format_table
from validators.movement_validator import MovementValidator
from datetime import datetime
import textwrap, uuid


class MovementView:
    def __init__(self, product_controller, movement_controller, user_controller,
                 location_controller, supplier_controller=None):

        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller

    @staticmethod
    def _format_qty_unit(q, unit):
        if q is None:
            return "0"
        return f"{q} {unit}" if unit else str(q)

    def _build_menu(self):
        return Menu("Меню за Доставки/Продажби/Премествания", [
            MenuItem("1", "Създаване на доставка/продажба (IN/OUT)", self.create_movement),
            MenuItem("2", "Преместване между локации (MOVE)", self.move_between_locations),
            MenuItem("3", "Търсене на движения", self.search_movements),
            MenuItem("4", "Покажи всички движения", self.show_all),
            MenuItem("5", "Разширено филтриране", self.advanced_filter),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    def _truncate(self, text, length=20):
        if text is None:
            return "-"
        text = str(text)
        return (text[:length - 3] + '...') if len(text) > length else text
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
        ids = sorted({loc for (loc, _, _) in wh})
        return ", ".join(ids)

    def _select_item(self, items, label):
        if not items:
            print(f"Няма налични {label}.")
            return None

        while True:
            print(f"\nИзберете {label}:")
            for i, item in enumerate(items, start=1):
                if isinstance(item, Product):
                    item_id = item.product_id
                elif isinstance(item, Location):
                    item_id = item.location_id
                else:
                    item_id = item.supplier_id

                qty_text = self._get_item_qty_text(item)
                print(f"{i}. {item.name}{qty_text} (ID: {item_id})")

                if isinstance(item, Product):
                    locs = self._get_product_locations(item)
                    if locs:
                        print(f"   Намира се в: {locs}")

            raw = input("Номер или ID (Enter = отказ): ").strip()
            if raw == "":
                print("Операцията е отказана.")
                return None

            if raw.isdigit():
                idx = int(raw) - 1
                if 0 <= idx < len(items):
                    return items[idx]
                else:
                    print("Невалиден номер. Опитайте отново.\n")
                    continue

            raw_l = raw.lower()
            for item in items:
                iid = item.product_id if isinstance(item, Product) else (
                    item.location_id if isinstance(item, Location) else item.supplier_id)
                if iid.lower() == raw_l:
                    return item
            print("Невалиден ID. Опитайте отново.\n")

    def show_menu(self):
        user = self.user_controller.logged_user
        if not user:
            print("Трябва да сте логнат.")
            return

        menu = self._build_menu()
        while True:
            choice = menu.show()
            if choice == "0":
                break
            menu.execute(choice, user)

    def create_movement(self, user):
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product:
            return

        print("\n0 - Доставка (IN)\n1 - Продажба (OUT)")
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

        # --- ИЗБОР НА ЛОКАЦИЯ ---
        if movement_type == "OUT":
            wh_list = self._get_product_warehouses_with_qty(product)
            if not wh_list:
                print("\nГрешка: Няма наличност за този продукт в нито един склад.")
                return

            print("\nИзберете склад (само от тези с наличност):")
            for i, (loc_id, qty, unit) in enumerate(wh_list, start=1):
                loc = self.location_controller.get_by_id(loc_id)
                print(f"{i}. {loc.name} – {qty} {unit} (ID: {loc_id})")

            raw = input("Номер или ID: ").strip()
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
            all_locs = self.location_controller.get_all()
            print("\nИзберете склад за доставка:")
            for idx, loc in enumerate(all_locs, start=1):
                print(f"{idx}. {loc.name} (ID: {loc.location_id})")

            raw = input("Номер или ID: ").strip()
            chosen_loc = None
            if raw.isdigit():
                num = int(raw)
                if 0 < num <= len(all_locs):
                    chosen_loc = all_locs[num - 1]
            else:
                for loc in all_locs:
                    if loc.location_id.lower() == raw.lower():
                        chosen_loc = loc
                        break
            if not chosen_loc:
                print("Грешка: Невалиден избор на локация.")
                return
            location = chosen_loc

        # --- КОЛИЧЕСТВО, ЦЕНА И ОПИСАНИЕ ---
        while True:
            quantity_raw = input("Количество: ").strip()
            try:
                qty = MovementValidator.parse_quantity(quantity_raw)
                break
            except:
                print("Грешка: количеството трябва да е валидно число.\n")

        while True:
            price_raw = input("Цена: ").strip()
            try:
                prc = MovementValidator.parse_price(price_raw)
                break
            except:
                print("Грешка: цената трябва да е валидно число.\n")

        while True:
            description = input("Описание: ").strip()
            if len(description) >= 3:
                break
            print("Грешка: описанието трябва да е поне 3 символа.\n")

        supplier_id = None
        customer = None

        # --- ЛОГИКА ЗА IN (Доставчик) ---
        if movement_type == "IN":
            all_suppliers = self.supplier_controller.get_all()
            print("\nИзберете доставчик:")
            for idx, s in enumerate(all_suppliers, start=1):
                print(f"{idx}. {s.name} (ID: {s.supplier_id})")

            while True:
                raw = input("Номер или ID: ").strip()
                supplier = None
                if raw.isdigit():
                    num = int(raw)
                    if 0 < num <= len(all_suppliers):
                        supplier = all_suppliers[num - 1]
                else:
                    for s in all_suppliers:
                        if s.supplier_id.lower() == raw.lower():
                            supplier = s
                            break
                if supplier:
                    supplier_id = supplier.supplier_id
                    break
                print("Грешка: Изборът на доставчик е задължителен за IN.")

        # --- ЛОГИКА ЗА OUT (Клиент - БЕТОНИРАНА) ---
        if movement_type == "OUT":
            while True:
                customer_input = input("Име на клиент (Задължително): ").strip()
                if customer_input:
                    customer = customer_input
                    break
                print("[!] Клиентът не може да бъде празен при продажба.")

        try:
            mv = self.movement_controller.add(
                product_id=product.product_id,
                user_id=user.user_id,
                location_id=location.location_id,
                movement_type=movement_type,
                quantity=str(qty),
                description=description,
                price=str(prc),
                customer=customer,
                supplier_id=supplier_id
            )
            print(f"\n[OK] Движението е добавено! ID: {mv.movement_id}")
        except ValueError as e:
            print("Грешка при запис:", e)

    def move_between_locations(self, user):
        # (Запазено както в оригиналния код, но с оправени препратки към контролери)
        print("\n   Преместване между локации (MOVE)   ")
        product = self._select_item(self.product_controller.get_all(), "продукт")
        if not product: return

        wh_list = self._get_product_warehouses_with_qty(product)
        if not wh_list:
            print("Грешка: Няма наличност за преместване.")
            return

        all_locs = self.location_controller.get_all()
        print("\nИзберете ИЗХОДНА локация:")
        for i, loc in enumerate(all_locs, start=1):
            qty = next((q for lid, q, u in wh_list if lid == loc.location_id), 0.0)
            print(f"{i}. {loc.name} – {qty} {product.unit} (ID: {loc.location_id})")

        raw = input("Номер или ID: ").strip()
        from_loc = None
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(all_locs): from_loc = all_locs[idx].location_id
        else:
            for loc in all_locs:
                if loc.location_id.lower() == raw.lower(): from_loc = loc.location_id

        if not from_loc: return

        print("\nИзберете ЦЕЛЕВА локация:")
        targets = [l for l in all_locs if l.location_id != from_loc]
        for i, loc in enumerate(targets, start=1):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")

        raw_to = input("Номер или ID: ").strip()
        to_loc = None
        if raw_to.isdigit():
            idx = int(raw_to) - 1
            if 0 <= idx < len(targets): to_loc = targets[idx].location_id
        else:
            for loc in targets:
                if loc.location_id.lower() == raw_to.lower(): to_loc = loc.location_id

        if not to_loc: return

        qty_raw = input("Количество: ").strip()
        qty = MovementValidator.parse_quantity(qty_raw)
        desc = input("Описание: ")

        try:
            mv = self.movement_controller.add(
                product_id=product.product_id,
                user_id=user.user_id,
                location_id=None,
                movement_type="MOVE",
                quantity=str(qty),
                description=desc,
                price="0",
                from_location_id=from_loc,
                to_location_id=to_loc
            )
            print(f"\n[OK] Преместено! ID: {mv.movement_id}")
        except ValueError as e:
            print("Грешка:", e)

    def search_movements(self, _):
        kw = input("Търсене: ").strip()
        if not kw or len(kw) < 2:
            print("[!] Въведете поне 2 символа за търсене.")
            return

        results = self.movement_controller.search_by_description(kw)

        if not results:
            print(f"\n[!] Няма намерени данни за '{kw}'.\n")
            return

        # Настройваме колоните точно по твоя модел
        columns = ["Дата", "Продукт", "Тип", "Кол.", "Към/От", "Склад"]
        rows = []

        for m in results:
            # Логика за Партньора (Към/От)
            partner_display = "-"
            if m.movement_type.name == "IN":
                supp = self.supplier_controller.get_by_id(m.supplier_id) if self.supplier_controller else None
                partner_display = supp.name if supp else (m.supplier_id or "Доставчик")
            elif m.movement_type.name == "OUT":
                partner_display = f"Клиент: {m.customer}" if m.customer else "Краен клиент"
            else:
                partner_display = "Вътрешно"

            # Логика за Склад
            if m.movement_type.name == "MOVE":
                loc_f = self.location_controller.get_by_id(m.from_location_id)
                loc_t = self.location_controller.get_by_id(m.to_location_id)
                loc_display = f"{loc_f.name if loc_f else '?'} -> {loc_t.name if loc_t else '?'}"
            else:
                loc = self.location_controller.get_by_id(m.location_id)
                loc_display = loc.name if loc else (m.location_id or "-")

            rows.append([
                str(m.date)[:16],
                str(m.product_name)[:15],  # Режем директно тук
                m.movement_type.name,
                self._format_qty_unit(m.quantity, m.unit),
                str(partner_display)[:25],  # Режем директно тук
                str(loc_display)[:40]  # Режем директно тук
            ])

        print(f"\nРезултати за търсене '{kw}':")
        print(format_table(columns, rows))

    def show_all(self, _):
        mv = self.movement_controller.movements
        if not mv:
            return

        columns = ["ID", "Дата", "Тип", "Количество", "Склад"]
        rows = []

        for m in mv:
            if m.movement_type.name == "MOVE":
                loc_f = self.location_controller.get_by_id(m.from_location_id)
                loc_t = self.location_controller.get_by_id(m.to_location_id)

                from_name = loc_f.name if loc_f else m.from_location_id
                to_name = loc_t.name if loc_t else m.to_location_id

                loc_display = f"{from_name} -> {to_name}"
            else:
                loc = self.location_controller.get_by_id(m.location_id)
                loc_display = loc.name if loc else "-"

            rows.append([
                m.movement_id[:8],
                m.date[:16],
                m.movement_type.name,
                self._format_qty_unit(m.quantity, m.unit),
                loc_display
            ])

        print(format_table(columns, rows))

    def advanced_filter(self, _):
        print("\n   Разширено филтриране на движения   ")
        print("0=IN, 1=OUT, 2=MOVE")

        # --- ВАЛИДАЦИЯ НА MOVEMENT TYPE ---
        m_type_input = input("Тип movement: ").strip()

        if m_type_input not in ["", "0", "1", "2"]:
            print("[!] Невалиден тип движение. Допустими: 0=IN, 1=OUT, 2=MOVE.")
            return

        m_type = {"0": "IN", "1": "OUT", "2": "MOVE"}.get(m_type_input)

        # --- ИЗВИКВАНЕ НА КОНТРОЛЕРА ---
        results = self.movement_controller.advanced_filter(movement_type=m_type)
        if not results:
            print("\nНяма движения по зададените критерии.")
            return

        # --- ТАБЛИЦА ---
        columns = ["Дата", "Тип", "Продукт", "Количество", "Партньор", "Склад/Път"]
        rows = []

        for m in results:
            product = self.product_controller.get_by_id(m.product_id)
            pname = product.name if product else "???"

            # --- ПАРТНЬОР ---
            if m.movement_type.name == "IN":
                s_id = m.supplier_id or (product.supplier_id if product else None)
                s = self.supplier_controller.get_by_id(s_id) if s_id else None
                partner = s.name if s else "Доставчик"

            elif m.movement_type.name == "OUT":
                partner = f"Кл: {m.customer}" if m.customer else "Краен клиент"

            elif m.movement_type.name == "MOVE":
                partner = "Вътрешно"

            else:
                partner = "-"

            # --- ЛОКАЦИЯ / ПЪТ ---
            if m.movement_type.name == "MOVE":
                loc_f = self.location_controller.get_by_id(m.from_location_id)
                loc_t = self.location_controller.get_by_id(m.to_location_id)

                from_name = loc_f.name if loc_f else (m.from_location_id or "?")
                to_name = loc_t.name if loc_t else (m.to_location_id or "?")

                loc_disp = f"{from_name} -> {to_name}"

            else:
                loc = self.location_controller.get_by_id(m.location_id)
                loc_disp = loc.name if loc else "-"

            # --- ДОБАВЯМЕ РЕД ---
            rows.append([
                m.date[:16],
                m.movement_type.name,
                pname,
                self._format_qty_unit(m.quantity, m.unit),
                partner,
                loc_disp
            ])

        # --- ПЕЧАТ НА ТАБЛИЦАТА ---
        print(format_table(columns, rows, col_widths=[18, 6, 20, 12, 28, 70]))
