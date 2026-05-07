from models.product import Product
from models.location import Location
from views.menu import Menu, MenuItem
from views.password_utils import format_table
from validators.movement_validator import MovementValidator


class MovementView:
    def __init__(self, product_controller, movement_controller, user_controller, location_controller,
                 supplier_controller):
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller

    def _get_product_total_qty(self, product):
        """СИНХРОН: Използваме inventory_controller за наличностите."""
        return self.movement_controller.inventory_controller.get_total_stock(product.product_id)

    def _get_product_warehouses_with_qty(self, product):
        """СИНХРОН: Връща локациите, където продуктът реално е наличен."""
        all_locs = self.location_controller.get_all()
        result = []
        for loc in all_locs:
            qty = self.movement_controller.inventory_controller.get_stock_by_location(
                product.product_id, loc.location_id
            )
            if qty > 0:
                result.append(loc)
        return result

    def _select_item(self, items, label):
        """СИНХРОН: Позволява избор чрез кратките 8-символни ID-та."""
        if not items:
            print(f"\n[!] Няма налични {label} в системата.\n")
            return None

        print(f"\n--- Избор на {label} ---")
        for i, item in enumerate(items, 1):
            # Универсално взимане на ID, независимо от типа обект
            iid = getattr(item, 'product_id', getattr(item, 'location_id', getattr(item, 'supplier_id', '???')))
            qty_info = ""
            if isinstance(item, Product):
                qty_info = f" | Налично: {self._get_product_total_qty(item)} {item.unit}"

            print(f"{i}. {item.name}{qty_info} (ID: {iid})")

        choice = input(f"\nИзберете {label} (Номер или ID, Enter за отказ): ").strip()
        if not choice: return None

        # Проверка по номер в списъка
        if choice.isdigit() and 0 < int(choice) <= len(items):
            return items[int(choice) - 1]

        # Проверка по кратко или пълно ID
        for item in items:
            iid = getattr(item, 'product_id', getattr(item, 'location_id', getattr(item, 'supplier_id', '')))
            if iid.lower() == choice.lower():
                return item

        print("[!] Невалиден избор.")
        return None

    def _display_results(self, results):
        """СИНХРОН: Таблица със същия стил като в ProductMenuView."""
        if not results:
            print("\n[!] Няма записани движения по този критерий.\n")
            return

        # Добавяме ID на самото движение за по-добра проследяемост
        columns = ["ID", "Дата", "Тип", "Продукт", "К-во", "Партньор", "Склад/Път"]
        rows = []

        for m in results:
            product = self.product_controller.get_by_id(m.product_id)
            p_name = product.name if product else "???"
            p_unit = product.unit if product else ""

            # Логика за Партньор (Доставчик или Клиент)
            partner = "Вътрешно"
            if m.movement_type.name == "IN":
                sup = self.supplier_controller.get_by_id(m.supplier_id) if m.supplier_id else None
                partner = sup.name if sup else "Доставчик"
            elif m.movement_type.name == "OUT":
                partner = f"Кл: {m.customer}" if m.customer else "Клиент"

            # Логика за Локация
            if m.movement_type.name == "MOVE":
                l_from = self.location_controller.get_by_id(m.from_location_id)
                l_to = self.location_controller.get_by_id(m.to_location_id)
                loc_text = f"{l_from.name if l_from else '?'} -> {l_to.name if l_to else '?'}"
            else:
                loc = self.location_controller.get_by_id(m.location_id)
                loc_text = loc.name if loc else "-"

            rows.append([
                m.movement_id[:8],  # Показваме първите 8 знака от ID-то
                m.date[5:16],  # Съкратена дата (Месец-Ден Час:Мин)
                m.movement_type.name,
                p_name,
                f"{m.quantity} {p_unit}",
                partner,
                loc_text
            ])

        print(format_table(columns, rows))
        input("\nНатиснете Enter за връщане към менюто...")