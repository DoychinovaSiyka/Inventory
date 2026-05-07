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
        """Връща общото количество от всички локации."""
        return self.movement_controller.inventory_controller.get_total_stock(product.product_id)

    def _get_product_warehouses_with_qty(self, product):
        """Връща списък с локации, в които продуктът има наличност."""
        result = []
        for loc in self.location_controller.get_all():
            qty = self.movement_controller.inventory_controller.get_stock_by_location(product.product_id, loc.location_id)
            if qty > 0:
                result.append(loc)
        return result

    def _select_item(self, items, label):
        """Позволява избор по номер или по начало на ID (кратко или пълно)."""
        if not items:
            print(f"\nНяма налични {label}.\n")
            return None

        print(f"\n--- Избор на {label} ---")
        for i, item in enumerate(items, 1):
            if isinstance(item, Product):
                full_id = item.product_id
            elif isinstance(item, Location):
                full_id = item.location_id
            else:
                full_id = item.supplier_id

            print(f"{i}. {item.name} [ID: {full_id[:8]}]")

            qty_info = ""
            if isinstance(item, Product):
                qty_info = f" | Налично: {self._get_product_total_qty(item)} {item.unit}"

            print(f"{i}. {item.name}{qty_info} [ID: {full_id[:8]}]")

        choice = input(f"\nИзберете {label} (номер или ID, Enter за отказ): ").strip()
        if not choice:
            return None

        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(items):
                return items[index]

        choice_lower = choice.lower()
        for item in items:
            if isinstance(item, Product):
                full_id = item.product_id
            elif isinstance(item, Location):
                full_id = item.location_id
            elif isinstance(item, Supplier):
                full_id = item.supplier_id
            else:
                continue

            if full_id.lower().startswith(choice_lower):
                return item

        print("Невалиден избор. Обектът не е намерен.")
        return None

    def _display_results(self, results):
        if not results:
            print("\n--- Няма движения по този критерий ---\n")
            return

        columns = ["ID", "Дата", "Тип", "Продукт", "Количество", "Партньор", "Склад/Път"]
        rows = []

        for m in results:
            product = self.product_controller.get_by_id(m.product_id)
            p_name = product.name if product else "-"
            p_unit = product.unit if product else "-"

            if m.movement_type.name == "IN":
                sup = self.supplier_controller.get_by_id(m.supplier_id) if m.supplier_id else None
                partner = sup.name if sup else "Доставчик"
            elif m.movement_type.name == "OUT":
                partner = m.customer if m.customer else "Клиент"
            else:
                partner = "Вътрешно"

            if m.movement_type.name == "MOVE":
                loc_from = self.location_controller.get_by_id(m.from_location_id)
                loc_to = self.location_controller.get_by_id(m.to_location_id)
                loc_text = f"{(loc_from.name if loc_from else '-')[:10]} -> {(loc_to.name if loc_to else '-')[:10]}"
            else:
                loc = self.location_controller.get_by_id(m.location_id)
                loc_text = loc.name if loc else "-"

            rows.append([m.movement_id[:8], m.date[5:16], m.movement_type.name, p_name[:15],
                         f"{m.quantity} {p_unit}", partner[:15], loc_text])

        print("\n" + format_table(columns, rows))
        input("\nНатиснете Enter за продължение...")

