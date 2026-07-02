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

    def show_menu(self, user):
        menu = Menu("Отчети", [
            MenuItem("1", "Обединен отчет за наличностите", self.inventory_full_report),
            MenuItem("2", "Хронология на движенията", self.report_movements),
            MenuItem("3", "Всички доставки", self.report_deliveries_all),
            MenuItem("4", "Всички продажби", self.report_sales_all),
            MenuItem("5", "Сортиране по количество (Merge Sort)", self.sort_qty_merge),
            MenuItem("6", "Сортиране по количество (Quick Sort)", self.sort_qty_quick),
            MenuItem("7", "Филтриране на движения", self.movements_filter_menu),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)





    def format_card(self, item):
        try:
            lines = []
            lines.append("─" * 45)

            product_name = str(item.get('product_name', 'НЕИЗВЕСТЕН ПРОДУКТ')).upper()
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
            quantity_text = f"{m['quantity']} {m['unit']}"
            rows.append([m["date"], m["movement_id"], m["type"], m["product"], quantity_text, m["from"], m["to"]])

        headers = ["Дата", "ID", "Тип", "Продукт", "Кол.", "От склад", "Към склад"]
        self._display_report("ХРОНОЛОГИЯ НА ДВИЖЕНИЯТА", headers, rows)




    def report_deliveries_all(self, _):
        result = self.controller.report_deliveries_all("")
        rows = []

        for item in result.data:
            rows.append([item["date"], item["movement_id"], item["product"],
                         f"{item['quantity']} {item['unit']}", item["price"], item["supplier"]])

        headers = ["Дата", "ID", "Продукт", "Кол.", "Цена", "Доставчик"]
        self._display_report("ВСИЧКИ ДОСТАВКИ (IN)", headers, rows)



    def report_sales_all(self, _):
        result = self.controller.report_sales()
        rows = []

        for item in result.data:
            rows.append([item["invoice_number"], item["date"], item["client"],
                         item["product"], item["total_price"], item.get("status", "АКТИВНА")])

        headers = ["Фактура", "Дата", "Клиент", "Продукт", "Общо", "Статус"]
        self._display_report("ВСИЧКИ ПРОДАЖБИ", headers, rows)




    def sort_qty_merge(self, _):
        result = self.controller.sort_inventory_by_quantity(algorithm="merge", reverse=True)

        groups = {}
        for item in result.data:
            unit = item["unit"]
            groups.setdefault(unit, []).append(item)

        print("\nСОРТИРАНЕ ПО КОЛИЧЕСТВО (MERGE SORT)")

        for unit, items in groups.items():
            print(f"\nМерна единица: {unit}")
            rows = [[i["product_name"], f"{i['total']} {i['unit']}"] for i in items]
            headers = ["Продукт", "Наличност"]
            print(format_table(headers, rows))

    def sort_qty_quick(self, _):
        result = self.controller.sort_inventory_by_quantity(algorithm="quick", reverse=True)

        groups = {}
        for item in result.data:
            unit = item["unit"]
            groups.setdefault(unit, []).append(item)

        print("\nСОРТИРАНЕ ПО КОЛИЧЕСТВО (QUICK SORT)")
        for unit, items in groups.items():
            print(f"\nМерна единица: {unit}")
            rows = [[i["product_name"], f"{i['total']} {i['unit']}"] for i in items]
            headers = ["Продукт", "Наличност"]
            print(format_table(headers, rows))




    def movements_filter_menu(self, user):
        menu = Menu("Филтриране на движения", [
            MenuItem("1", "По тип (IN / OUT / MOVE)", self.filter_movements_by_type),
            MenuItem("2", "По продукт", self.filter_movements_by_product),
            MenuItem("3", "По доставчик", self.filter_movements_by_supplier),
            MenuItem("4", "По клиент", self.filter_movements_by_client),
            MenuItem("5", "По склад", self.filter_movements_by_warehouse),
            MenuItem("6", "По дата или период", self.filter_movements_by_date),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)

    def filter_movements_by_type(self, _):
        mtype = input("Въведете тип (IN / OUT / MOVE): ").strip().upper()
        result = self.controller.filter_movements(type=mtype)
        self._render_filtered_movements(result)

    def filter_movements_by_product(self, _):
        product = input("Въведете име на продукт: ").strip()
        result = self.controller.filter_movements(product=product)
        self._render_filtered_movements(result)

    def filter_movements_by_supplier(self, _):
        supplier = input("Въведете доставчик: ").strip()
        result = self.controller.filter_movements(supplier=supplier)
        self._render_filtered_movements(result)

    def filter_movements_by_client(self, _):
        client = input("Въведете клиент: ").strip()
        result = self.controller.filter_movements(client=client)
        self._render_filtered_movements(result)



    def filter_movements_by_warehouse(self, _):
        wh = input("Въведете склад: ").strip()
        result = self.controller.filter_movements(warehouse=wh)
        self._render_filtered_movements(result)



    def filter_movements_by_date(self, _):
        start = input("От дата (YYYY-MM-DD): ").strip()
        end = input("До дата (YYYY-MM-DD): ").strip()
        result = self.controller.filter_movements(date_from=start, date_to=end)
        self._render_filtered_movements(result)




    def _render_filtered_movements(self, result):
        rows = []
        for m in result.data:
            rows.append([m["date"], m["movement_id"], m["type"], m["product"],
                         f"{m['quantity']} {m['unit']}", m["from"], m["to"]])

        headers = ["Дата", "ID", "Тип", "Продукт", "Кол.", "От склад", "Към склад"]
        self._display_report("ФИЛТРИРАНИ ДВИЖЕНИЯ", headers, rows)
