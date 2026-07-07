from datetime import datetime
from views.menu import Menu, MenuItem
from views.password_utils import format_table




class ReportsView:
    def __init__(self, controller):
        self.controller = controller

    def _display_report(self, title, headers, rows):
        if not rows:
            print("\nНяма данни за показване.\n")
            return
        print(f"\n{title}")
        print(format_table(headers, rows))

    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice in ("0", None):
                break
            if menu_obj.execute(choice, user) == "break":
                break

        menu = Menu("Отчети", [
            MenuItem("1", "Обединен отчет за наличностите", self.inventory_full_report),
            MenuItem("2", "Хронология на всички движения", self.report_movements),
            MenuItem("3", "Операции по тип (IN / OUT / MOVE)", self.operations_by_type_menu),
            MenuItem("4", "Сортиране по количество", self.sort_menu),
            MenuItem("5", "Филтриране на движения", self.movements_filter_menu),
            MenuItem("6", "Критично изчерпани артикули", self.report_critical_items),
            MenuItem("7", "Излишества (над 130 бр.)", self.report_overstock_items),
            MenuItem("0", "Назад", lambda u: "break")])

        self._run_menu(menu, user)


    def format_card(self, item):
        try:
            lines = []
            lines.append("─" * 45)
            product_name = str(item.get('product_name', 'НЕИЗВЕСТЕН')).upper()
            lines.append(f"ПРОДУКТ:          {product_name}")

            unit = item.get('unit', 'бр.')
            total_qty = item.get('total', 0)
            lines.append(f"Общо количество:  {total_qty} {unit}")
            lines.append("")

            lines.append("РАЗПРЕДЕЛЕНИЕ ПО СКЛАДОВЕ:")
            warehouses = item.get("warehouses", {})
            if isinstance(warehouses, dict) and warehouses:
                for wh, qty in warehouses.items():
                    lines.append(f"   {wh}: {qty} {unit}")
            else:
                lines.append("   (Няма налични данни за локации)")

            lines.append("")
            lines.append(f"Доставено количество: {item.get('delivered', 0)}")
            lines.append(f"Продадено количество: {item.get('sold', 0)}")
            lines.append(f"Средна входна цена:   {item.get('avg_in_price', '-')}")
            lines.append(f"Средна изходна цена:  {item.get('avg_out_price', '-')}")
            lines.append(f"ОБЩО РАЗХОДИ:         {item.get('expense', '-')}")
            lines.append(f"ОБЩО ПРИХОДИ:         {item.get('revenue', '-')}")
            lines.append(f"Последно движение:    {item.get('last_movement', 'Няма данни')}")
            lines.append("─" * 45)
            return "\n".join(lines)

        except Exception as e:
            return f"\nГрешка при визуализация на продукт: {str(e)}\n"


    def inventory_full_report(self, _):
        result = self.controller.report_inventory_full()
        print("\n" + "=" * 20)
        print(" ОБЕДИНЕН ОТЧЕТ ЗА НАЛИЧНОСТИТЕ ")
        print(f"Генериран на: {result.generated_on}")
        print("=" * 20)

        for item in result.data:
            print(self.format_card(item))




    def report_movements(self, _):
        result = self.controller.report_movements()
        rows = []

        for m in result.data:
            rows.append([m.get("date", "-"), m.get("movement_id", "-"), m.get("type", "-"),
                         m.get("product_name", "-"),
                         f"{m.get('quantity', 0)} {m.get('unit', '')}", m.get("from", "-"), m.get("to", "-")])

        headers = ["Дата", "ID", "Тип", "Продукт", "Кол.", "От", "Към"]
        self._display_report("ХРОНОЛОГИЯ НА ДВИЖЕНИЯТА", headers, rows)




    def operations_by_type_menu(self, user):
        menu = Menu("Операции по тип", [
            MenuItem("1", "Всички доставки (IN)", self.report_deliveries_all),
            MenuItem("2", "Всички продажби (OUT)", self.report_sales_all),
            MenuItem("3", "Всички премествания (MOVE)", self.report_moves_all),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)


    def report_moves_all(self, _):
        result = self.controller.filter_movements(type="MOVE")
        self._render_filtered_movements(result)


    def report_deliveries_all(self, _):
        result = self.controller.report_deliveries_all("")
        rows = []

        for item in result.data:
            rows.append([item.get("date", "-"), item.get("movement_id", "-"), item.get("product", "-"),
                         f"{item.get('quantity', 0)} {item.get('unit', '')}",
                         item.get("price", "-"), item.get("supplier", "-"), item.get("to", "-")])

        headers = ["Дата", "ID", "Продукт", "Кол.", "Цена", "Доставчик", "Склад"]
        self._display_report("ВСИЧКИ ДОСТАВКИ (IN)", headers, rows)


    def report_sales_all(self, _):
        result = self.controller.report_sales()
        rows = []

        for item in result.data:
            qty = item.get("quantity")
            unit = item.get("unit")
            qty_display = f"{qty} {unit}" if qty and unit else "—"
            rows.append([item.get("invoice_number", "-"), item.get("date", "-"),
                         item.get("client", "Неизвестен"), item.get("product", "-"), qty_display,
                         item.get("total_price", "-"), item.get("status", "АКТИВНА")])

        headers = ["Фактура", "Дата", "Клиент", "Продукт", "Кол.", "Общо", "Статус"]
        self._display_report("ВСИЧКИ ПРОДАЖБИ (OUT)", headers, rows)




    def sort_menu(self, user):
        menu = Menu("Сортиране по количество", [
            MenuItem("1", "Merge Sort", self.sort_qty_merge),
            MenuItem("2", "Quick Sort", self.sort_qty_quick),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)

    def sort_qty_merge(self, _):
        result = self.controller.sort_inventory_by_quantity(algorithm="merge", reverse=True)
        self._render_sorted(result)

    def sort_qty_quick(self, _):
        result = self.controller.sort_inventory_by_quantity(algorithm="quick", reverse=True)
        self._render_sorted(result)

    def _render_sorted(self, result):
        groups = {}
        for item in result.data:
            unit = item.get("unit", "")
            groups.setdefault(unit, []).append(item)

        print("\nСОРТИРАНЕ ПО КОЛИЧЕСТВО")
        for unit, items in groups.items():
            print(f"\nМерна единица: {unit}")
            rows = [[item.get("product_name", "-"), f"{item.get('total', 0)} {item.get('unit', '')}"] for item in items]
            headers = ["Продукт", "Наличност"]
            print(format_table(headers, rows))


    def movements_filter_menu(self, user):
        menu = Menu("Филтриране на движения", [
            MenuItem("1", "По продукт", self.filter_movements_by_product),
            MenuItem("2", "По доставчик", self.filter_movements_by_supplier),
            MenuItem("3", "По клиент", self.filter_movements_by_client),
            MenuItem("4", "По склад", self.filter_movements_by_warehouse),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)



    def filter_movements_by_product(self, _):
        product = input("Въведете продукт: ").strip()
        result = self.controller.filter_movements(product=product if product else None)
        self._render_filtered_movements(result)



    def filter_movements_by_supplier(self, _):
        supplier = input("Въведете доставчик: ").strip()
        result = self.controller.report_deliveries_all("")

        rows = []
        for m in result.data:
            if supplier and m.get("supplier") != supplier:
                continue

            rows.append([m.get("date", "-"), m.get("movement_id", "-"), m.get("product", "-"),
                         f"{m.get('quantity', 0)} {m.get('unit', '')}", m.get("price", "-"),
                         m.get("supplier", "Неизвестен"), m.get("to", "Няма")])

        headers = ["Дата", "ID", "Продукт", "Кол.", "Цена", "Доставчик", "Склад"]
        self._display_report("ДОСТАВКИ ПО ДОСТАВЧИК", headers, rows)



    def filter_movements_by_client(self, _):
        client = input("Въведете клиент: ").strip()
        result = self.controller.report_sales()

        rows = []
        for m in result.data:
            if client and m.get("client") != client:
                continue

            qty = m.get("quantity")
            unit = m.get("unit")
            qty_display = f"{qty} {unit}" if qty and unit else "—"

            rows.append([m.get("invoice_number", "-"), m.get("date", "-"), m.get("client", "Неизвестен"),
                         m.get("product", "-"), qty_display, m.get("total_price", "-"), m.get("status", "АКТИВНА")])

        headers = ["Фактура", "Дата", "Клиент", "Продукт", "Кол.", "Общо", "Статус"]
        self._display_report("ПРОДАЖБИ ПО КЛИЕНТ", headers, rows)



    def filter_movements_by_warehouse(self, _):
        wh = input("Въведете склад: ").strip()
        result = self.controller.report_inventory_full()

        rows = []
        for item in result.data:
            warehouses = item.get("warehouses", {})
            if not wh:
                for wname, qty in warehouses.items():
                    rows.append([item.get("product_name", "-"), wname, f"{qty} {item.get('unit', '')}"])
            else:
                qty = warehouses.get(wh, None)
                if qty is not None:
                    rows.append([item.get("product_name", "-"), wh, f"{qty} {item.get('unit', '')}"])

        headers = ["Продукт", "Склад", "Наличност"]
        self._display_report("НАЛИЧНОСТИ ПО СКЛАДОВЕ", headers, rows)




    def _render_filtered_movements(self, result):
        rows = []
        for m in result.data:
            rows.append([m.get("date", "-"), m.get("movement_id", "-"), m.get("type", "-"),
                         m.get("product_name", "-"), f"{m.get('quantity', 0)} {m.get('unit', '')}",
                         m.get("from", "-"), m.get("to", "-")])

        headers = ["Дата", "ID", "Тип", "Продукт", "Кол.", "От", "Към"]
        self._display_report("ФИЛТРИРАНИ ДВИЖЕНИЯ", headers, rows)


    def report_critical_items(self, _):
        items = self.controller.inventory_controller.get_critical_items(threshold=5)

        rows = []
        for item in items:
            warehouses = ", ".join([f"{wh}: {qty}" for wh, qty in item.get("warehouses", {}).items()])
            rows.append([item.get("product_name", "-"), f"{item.get('total', 0)} {item.get('unit', '')}", warehouses])

        headers = ["Продукт", "Общо количество", "По складове"]
        self._display_report("КРИТИЧНО ИЗЧЕРПАНИ АРТИКУЛИ", headers, rows)




    def report_overstock_items(self, _):
        items = self.controller.inventory_controller.get_overstocked_items(threshold=130)

        rows = []
        for item in items:
            warehouses = ", ".join([f"{wh}: {qty}" for wh, qty in item.get("warehouses", {}).items()])
            rows.append([
                item.get("product_name", "-"),
                f"{item.get('total', 0)} {item.get('unit', '')}",
                warehouses
            ])

        headers = ["Продукт", "Общо количество", "По складове"]
        self._display_report("ИЗЛИШЕСТВА (над 130 бр.)", headers, rows)
