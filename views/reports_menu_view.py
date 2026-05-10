from datetime import datetime
from views.menu import Menu, MenuItem
from views.password_utils import format_table


class ReportsView:
    def __init__(self, controller):
        self.controller = controller

    def _display_report(self, title, headers, rows):
        """Универсален метод за показване на таблица."""
        if not rows:
            print("\nНяма данни за показване.\n")
            return

        print(f"\n{title}")
        print(format_table(headers, rows))


    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice == "0" or choice is None:
                break
            if menu_obj.execute(choice, user) == "break":
                break

    def _search_flow(self, prompt, controller_fn, format_fn, title, headers):
        """Помощен метод за изпълнение на търсене и показване на резултата."""
        keyword = input(f"Въведете {prompt} (Enter за всички): ").strip()
        result = controller_fn(keyword)

        formatted = format_fn(result.data)
        # Добавяме резюме към заглавието, ако има такова
        full_title = title
        if hasattr(result, 'summary') and 'total_revenue' in result.summary:
            full_title += f" (Общ оборот: {result.summary['total_revenue']:.2f} лв.)"

        self._display_report(full_title, headers, formatted)

    def show_menu(self, user):
        menu = Menu("СПРАВКИ", [
            MenuItem("1", "Обобщена наличност", self.summary_report),
            MenuItem("2", "Наличност по складове", self.inventory_by_warehouse),
            MenuItem("3", "Хронология на движенията", self.report_movements),
            MenuItem("4", "Търсене на доставки", self.search_delivery),
            MenuItem("5", "Всички продажби (активни)", self.report_sales),
            MenuItem("6", "Търсене продажби по клиент", self.search_sales_by_customer),
            MenuItem("7", "Търсене продажби по продукт", self.search_sales_by_product),
            MenuItem("8", "Анализ по FIFO", self.report_fifo_analysis),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)

    def _fmt_delivery(self, data):
        """Форматира данните за доставки."""
        rows = []
        for item in data:
            price_value = float(item["price"])
            quantity_text = f"{item['quantity']} {item['unit']}"
            row = [
                item["date"],
                item["movement_id"],
                item["product"],
                quantity_text,
                f"{price_value:.2f} лв.",
                item["supplier"]
            ]
            rows.append(row)
        return rows

    def _fmt_sales(self, data):
        """Форматира данните за продажби със статус."""
        rows = []
        for item in data:
            total_value = float(item.get("total_price", 0))
            status = item.get("status", "АКТИВНА")

            row = [
                item["invoice_number"],
                item["date"],
                item["client"],
                item["product"],
                f"{total_value:.2f} лв.",
                status
            ]
            rows.append(row)
        return rows

    def summary_report(self, _):
        """Обобщена справка за наличности."""
        result = self.controller.report_inventory_summary()
        rows = []

        for item in result.data:
            locations = item.get("top_locations", "Няма наличност")
            locations_str = str(locations)
            if len(locations_str) > 40:
                locations_str = locations_str[:37] + "..."

            row = [item["product"], item["available"], item["sold"], locations_str]
            rows.append(row)

        self._display_report("Обобщена справка", ["Продукт", "Налично", "Продадено", "Локации"], rows)

    def inventory_by_warehouse(self, _):
        """Показва наличностите по складове."""
        inv_data = self.controller.inventory_controller.data.get("products", {})
        loc_map = {loc.location_id: loc for loc in self.controller.location_controller.get_all()}

        rows = []
        for pid, pdata in inv_data.items():
            product = self.controller.product_controller.get_by_id(pid)
            p_name = product.name if product else f"Изтрит продукт ({pid[:8]})"
            p_unit = product.unit if product else "бр."

            for loc_id, qty in pdata.get("locations", {}).items():
                qty_value = float(qty)
                if qty_value > 0:
                    loc_obj = loc_map.get(loc_id)
                    loc_name = loc_obj.name if loc_obj else f"Склад {str(loc_id)[:8]}"
                    rows.append([loc_name, p_name, f"{qty_value:.2f} {p_unit}"])

        rows_sorted = sorted(rows, key=lambda x: x[0])
        self._display_report("Наличност по складове", ["Склад", "Продукт", "Количество"], rows_sorted)

    def report_movements(self, _):
        """Хронология на движенията."""
        result = self.controller.report_movements()
        rows = []
        for m in result.data:
            quantity_text = f"{m['quantity']} {m['unit']}"
            row = [m["date"], m["movement_id"], m["type"], m["product"], quantity_text, m["from"], m["to"]]
            rows.append(row)

        self._display_report("Хронология на движенията",
                             ["Дата", "ID", "Тип", "Продукт", "Кол.", "От", "Към"], rows)

    def search_delivery(self, _):
        """Търсене на доставки."""
        headers = ["Дата", "ID", "Продукт", "Кол.", "Цена", "Доставчик"]
        self._search_flow("продукт или доставчик", self.controller.report_deliveries_all,
                          self._fmt_delivery, "Доставки (IN)", headers)

    def report_sales(self, _):
        """Справка за продажби."""
        result = self.controller.report_sales()
        formatted = self._fmt_sales(result.data)

        title = f"Продажби (Активни: {result.summary['total_count']})"
        if 'total_revenue' in result.summary:
            title += f" | Общ оборот: {result.summary['total_revenue']:.2f} лв."

        self._display_report(title, ["Фактура", "Дата", "Клиент", "Продукт", "Общо", "Статус"], formatted)

    def search_sales_by_customer(self, _):
        """Търсене продажби по клиент."""
        headers = ["Фактура", "Дата", "Клиент", "Продукт", "Общо", "Статус"]
        self._search_flow("име на клиент", self.controller.report_sales_by_customer,
                          self._fmt_sales, "Резултати за клиент", headers)

    def search_sales_by_product(self, _):
        """Търсене продажби по продукт."""
        headers = ["Фактура", "Дата", "Клиент", "Продукт", "Общо", "Статус"]
        self._search_flow("име на продукт", self.controller.report_sales_by_product,
                          self._fmt_sales, "Резултати за продукт", headers)

    def report_fifo_analysis(self, _):
        """Интерактивен FIFO анализ."""
        while True:
            name = input("\nВъведете име или ID на продукт (или 'отказ' за изход): ").strip()
            if not name or name.lower() == "отказ":
                break

            data = self.controller.product_lifecycle(name)
            if not data:
                print(f"Продукт '{name}' не е намерен.")
                continue

            print("\n" + "-" * 40)
            print(f" АНАЛИЗ ПО FIFO ЗА: {data['product'].upper()}")
            print(f" Наличност в склада: {data['current_stock']} {data['unit']}")
            print(f" История: Влезли: {data['total_in']} | Продадени: {data['total_out']}")
            print("-" * 40)
            print(f" ПРИХОДИ:       {float(data['revenue']):>10.2f} лв.")
            print(f" СЕБЕСТОЙНОСТ: {float(data['fifo_cost']):>10.2f} лв.")
            print("-" * 40)
            print(f" ЧИСТА ПЕЧАЛБА: {float(data['profit']):>10.2f} лв.")
            break