from datetime import datetime
from views.menu import Menu, MenuItem
from views.password_utils import format_table

from controllers.report_controller import ReportController
from controllers.inventory_controller import InventoryController






class ReportsView:
    def __init__(self, report_controller: ReportController):
        self.report_controller = report_controller
        self.inventory_controller: InventoryController = report_controller.inventory_controller


    def _display(self, title, headers, rows):
        print(f"\n{title}")
        if not rows:
            print("Няма данни.")
            return
        print(format_table(headers, rows))


    def _menu(self, title, items, user):
        menu = Menu(title, items)
        while True:
            choice = menu.show()
            if choice in ("0", None):
                break
            if menu.execute(choice, user) == "break":
                break


    def show_menu(self, user):
        items = [
            MenuItem("1", "Обединен отчет за наличностите", self.inventory_full_report),
            MenuItem("2", "Хронология на всички движения", self.report_movements),
            MenuItem("3", "Операции по тип (IN / OUT / MOVE)", self.operations_by_type_menu),
            MenuItem("4", "Сортиране по количество", self.sort_menu),
            MenuItem("5", "Филтриране на движения", self.movements_filter_menu),
            MenuItem("6", "Критично изчерпани артикули", self.report_critical_items),
            MenuItem("7", "Излишества (над 130 бр.)", self.report_overstock_items),
            MenuItem("0", "Назад", lambda u: "break")]
        self._menu("Отчети", items, user)






    def inventory_full_report(self, _):
        result = self.report_controller.report_inventory_full()

        print("\n" + "=" * 20)
        print(" ОБЕДИНЕН ОТЧЕТ ЗА НАЛИЧНОСТИТЕ ")
        print(f"Генериран на: {result.generated_on}")
        print("=" * 20)

        for item in result.data:
            if "product_id" not in item:
                continue
            print(self._format_card(item))

        for item in result.data:
            if "total_products" in item:
                print(f"\nОбщо продукти: {item['total_products']}")
                break


    def _format_card(self, item):
        name = item.get("product_name", "НЕИЗВЕСТЕН").upper()
        unit = item.get("unit", "бр.")
        total = item.get("total", 0)

        lines = ["─" * 45, f"ПРОДУКТ:          {name}",
                 f"Общо количество:  {total} {unit}", "", "РАЗПРЕДЕЛЕНИЕ ПО СКЛАДОВЕ:"]

        warehouses = item.get("warehouses", {})
        if warehouses:
            for wh, qty in warehouses.items():
                lines.append(f"   {wh}: {qty} {unit}")
        else:
            lines.append("   (Няма данни)")

        lines.extend(["", f"Доставено количество: {item.get('delivered', 0)}",
                      f"Продадено количество: {item.get('sold', 0)}",
                      f"Средна входна цена:   {item.get('avg_in_price', '-')}",
                      f"Средна изходна цена:  {item.get('avg_out_price', '-')}",
                      f"ОБЩО РАЗХОДИ:         {item.get('expense', '-')}",
                      f"ОБЩО ПРИХОДИ:         {item.get('revenue', '-')}",
                      f"Последно движение:    {item.get('last_movement', 'Няма данни')}", "─" * 45])
        return "\n".join(lines)


    def report_movements(self, _):
        result = self.report_controller.report_movements()
        rows = [
            [m.get("date", "-"), m.get("movement_id", "-"), m.get("type", "-"), m.get("product_name", "-"),
             f"{m.get('quantity', 0)} {m.get('unit', '')}", m.get("from", "-"), m.get("to", "-")] for m in result.data]
        headers = ["Дата", "ID", "Тип", "Продукт", "Кол.", "От", "Към"]
        self._display("ХРОНОЛОГИЯ НА ДВИЖЕНИЯТА", headers, rows)


    def operations_by_type_menu(self, user):
        items = [
            MenuItem("1", "Всички доставки (IN)", lambda u: self._ops_type("IN")),
            MenuItem("2", "Всички продажби (OUT)", lambda u: self._ops_type("OUT")),
            MenuItem("3", "Всички премествания (MOVE)", lambda u: self._ops_type("MOVE")),
            MenuItem("0", "Назад", lambda u: "break")]
        self._menu("Операции по тип", items, user)





    def _ops_type(self, type_name):
        result = self.report_controller.filter_movements(type=type_name)
        self._filtered(result)


    def sort_menu(self, user):
        items = [
            MenuItem("1", "Merge Sort", lambda u: self._sort("merge")),
            MenuItem("2", "Quick Sort", lambda u: self._sort("quick")),
            MenuItem("0", "Назад", lambda u: "break")]
        self._menu("Сортиране по количество", items, user)


    def _sort(self, algorithm):
        result = self.report_controller.sort_inventory_by_quantity(algorithm=algorithm, reverse=True)
        groups = {}

        for item in result.data:
            if "product_id" not in item:
                continue
            unit = item.get("unit", "")
            groups.setdefault(unit, []).append(item)

        print("\nСОРТИРАНЕ ПО КОЛИЧЕСТВО")
        for unit, items in groups.items():
            print(f"\nМерна единица: {unit}")
            rows = [[i.get("product_name", "-"), f"{i.get('total', 0)} {i.get('unit', '')}"] for i in items]
            headers = ["Продукт", "Наличност"]
            print(format_table(headers, rows))


    def movements_filter_menu(self, user):
        items = [
            MenuItem("1", "По продукт", lambda u: self._filter("product")),
            MenuItem("2", "По доставчик", lambda u: self._filter("supplier")),
            MenuItem("3", "По клиент", lambda u: self._filter("client")),
            MenuItem("4", "По склад", lambda u: self._filter("warehouse")),
            MenuItem("0", "Назад", lambda u: "break")]
        self._menu("Филтриране на движения", items, user)





    def _filter(self, mode):
        key = input("Въведете стойност: ").strip()

        if mode == "product":
            result = self.report_controller.filter_movements(product=key)
            self._filtered(result)

        elif mode == "supplier":
            result = self.report_controller.report_deliveries_all("")
            rows = [[m.get("date", "-"), m.get("movement_id", "-"), m.get("product", "-"),
                     f"{m.get('quantity', 0)} {m.get('unit', '')}",
                     m.get("price", "-"), m.get("supplier", "-"), m.get("to", "-")]
                    for m in result.data if not key or m.get("supplier") == key]
            headers = ["Дата", "ID", "Продукт", "Кол.", "Цена", "Доставчик", "Склад"]
            self._display("ДОСТАВКИ ПО ДОСТАВЧИК", headers, rows)

        elif mode == "client":
            result = self.report_controller.report_sales()
            rows = [
                [m.get("invoice_number", "-"), m.get("date", "-"), m.get("client", "-"), m.get("product", "-"),
                 f"{m.get('quantity', 0)} {m.get('unit', '')}", m.get("total_price", "-"), m.get("status", "АКТИВНА")]
                for m in result.data if not key or m.get("client") == key]
            headers = ["Фактура", "Дата", "Клиент", "Продукт", "Кол.", "Общо", "Статус"]
            self._display("ПРОДАЖБИ ПО КЛИЕНТ", headers, rows)

        elif mode == "warehouse":
            result = self.report_controller.report_inventory_full()
            rows = []
            for item in result.data:
                if "product_id" not in item:
                    continue
                for wh, qty in item.get("warehouses", {}).items():
                    if not key or wh == key:
                        rows.append([item.get("product_name", "-"), wh, f"{qty} {item.get('unit', '')}"])
            headers = ["Продукт", "Склад", "Наличност"]
            self._display("НАЛИЧНОСТИ ПО СКЛАДОВЕ", headers, rows)






    def _filtered(self, result):
        rows = [
            [m.get("date", "-"), m.get("movement_id", "-"), m.get("type", "-"), m.get("product_name", "-"),
             f"{m.get('quantity', 0)} {m.get('unit', '')}", m.get("from", "-"), m.get("to", "-")] for m in result.data]
        headers = ["Дата", "ID", "Тип", "Продукт", "Кол.", "От", "Към"]
        self._display("ФИЛТРИРАНИ ДВИЖЕНИЯ", headers, rows)






    def report_critical_items(self, _):
        items = self.inventory_controller.get_critical_items(threshold=5)
        rows = [
            [item.get("product_name", "-"),
             f"{item.get('total', 0)} {item.get('unit', '')}",
             ", ".join([f"{wh}: {qty}" for wh, qty in item.get("warehouses", {}).items()])] for item in items]
        headers = ["Продукт", "Общо количество", "По складове"]
        self._display("КРИТИЧНО ИЗЧЕРПАНИ АРТИКУЛИ", headers, rows)





    def report_overstock_items(self, _):
        items = self.inventory_controller.get_overstocked_items(threshold=130)
        rows = [
            [item.get("product_name", "-"), f"{item.get('total', 0)} {item.get('unit', '')}",
             ", ".join([f"{wh}: {qty}" for wh, qty in item.get("warehouses", {}).items()])] for item in items]

        headers = ["Продукт", "Общо количество", "По складове"]
        self._display("ИЗЛИШЕСТВА (над 130 бр.)", headers, rows)
