from datetime import datetime
from views.menu import Menu, MenuItem
from views.password_utils import format_table


class ReportsView:
    def __init__(self, controller):
        self.controller = controller

    # ---------------------------------------------------------
    # Помощни методи
    # ---------------------------------------------------------

    def _display_report(self, title, headers, rows):
        """Показва таблица със заглавие и данни."""
        if not rows:
            print("\nНяма данни за показване.\n")
            return

        print(f"\n{title}")
        print(format_table(headers, rows))
        input("\nНатиснете Enter за връщане...")

    def _run_menu(self, menu_obj, user):
        """Общ механизъм за изпълнение на менюта."""
        while True:
            choice = menu_obj.show()
            if choice == "0" or choice is None:
                break
            menu_obj.execute(choice, user)

    def _search_flow(self, prompt, controller_fn, format_fn, title, headers):
        """Общ механизъм за справки с търсене."""
        keyword = input(f"Въведете {prompt} (Enter за всички): ").strip()

        # ПОПРАВКА: Винаги подаваме keyword, дори да е празен
        # Така контролерът ще получи аргумента, който очаква
        result = controller_fn(keyword)

        formatted = format_fn(result.data)
        self._display_report(title, headers, formatted)
    # ---------------------------------------------------------
    # ОПТИМИЗИРАНО ГЛАВНО МЕНЮ НА СПРАВКИ
    # ---------------------------------------------------------

    def show_menu(self, user):
        menu = Menu("СПРАВКИ", [
            MenuItem("1", "Обобщена наличност", self.summary_report),
            MenuItem("2", "Наличност по складове", self.inventory_by_warehouse),

            MenuItem("3", "Хронология на движенията", self.report_movements),
            MenuItem("4", "Търсене на доставки", self.search_delivery),

            MenuItem("5", "Всички продажби", self.report_sales),
            MenuItem("6", "Търсене продажби по клиент", self.search_sales_by_customer),
            MenuItem("7", "Търсене продажби по продукт", self.search_sales_by_product),

            MenuItem("8", "Анализ по FIFO", self.report_fifo_analysis),

            MenuItem("0", "Назад", lambda u: "break")
        ])
        self._run_menu(menu, user)

    # ---------------------------------------------------------
    # Форматиращи функции
    # ---------------------------------------------------------

    def _fmt_delivery(self, data):
        rows = []
        for item in data:
            price_value = float(item["price"])
            quantity_text = str(item["quantity"]) + " " + str(item["unit"])

            row = [
                item["date"],
                item["movement_id"],
                item["product"],
                quantity_text,
                f"{price_value:.2f}",
                item["supplier"]
            ]
            rows.append(row)

        return rows

    def _fmt_sales(self, data):
        rows = []
        for item in data:
            total_value = float(item.get("total_price", 0))

            row = [
                item["invoice_number"],
                item["date"],
                item["client"],
                item["product"],
                f"{total_value:.2f}"
            ]
            rows.append(row)

        return rows

    # ---------------------------------------------------------
    # Справки: Наличности
    # ---------------------------------------------------------

    def summary_report(self, _):
        """Обобщена справка за наличности."""
        result = self.controller.report_inventory_summary()
        rows = []

        for item in result.data:
            locations = item.get("top_locations", "Няма наличност")

            locations_str = str(locations)
            if len(locations_str) > 40:
                locations_str = locations_str[:37] + "..."

            row = [
                item["product"],
                item["available"],
                item["sold"],
                locations_str
            ]
            rows.append(row)

        self._display_report(
            "Обобщена справка",
            ["Продукт", "Налично", "Продадено", "Локации"],
            rows
        )

    def inventory_by_warehouse(self, _):
        """Показва наличностите по складове."""
        inv_data = self.controller.inventory_controller.data.get("products", {})
        loc_map = {loc.location_id: loc for loc in self.controller.location_controller.get_all()}

        rows = []

        for pid, pdata in inv_data.items():
            product = self.controller.product_controller.get_by_id(pid)

            if product:
                p_name = product.name
                p_unit = product.unit
            else:
                p_name = f"Изтрит продукт ({pid[:8]})"
                p_unit = "бр."

            for loc_id, qty in pdata.get("locations", {}).items():
                qty_value = float(qty)

                if qty_value > 0:
                    loc_obj = loc_map.get(loc_id)
                    loc_name = loc_obj.name if loc_obj else f"Склад {str(loc_id)[:8]}"

                    rows.append([
                        loc_name,
                        p_name,
                        f"{qty_value:.2f} {p_unit}"
                    ])

        rows_sorted = sorted(rows, key=lambda x: x[0])

        self._display_report(
            "Наличност по складове",
            ["Склад", "Продукт", "Количество"],
            rows_sorted
        )

    # ---------------------------------------------------------
    # Справки: Логистика
    # ---------------------------------------------------------

    def report_movements(self, _):
        result = self.controller.report_movements()
        rows = []

        for m in result.data:
            quantity_text = str(m["quantity"]) + " " + str(m["unit"])

            row = [
                m["date"],
                m["movement_id"],
                m["type"],
                m["product"],
                quantity_text,
                m["from"],
                m["to"]
            ]
            rows.append(row)

        self._display_report(
            "Хронология на движенията",
            ["Дата", "ID", "Тип", "Продукт", "Кол.", "От", "Към"],
            rows
        )

    def search_delivery(self, _):
        headers = ["Дата", "ID", "Продукт", "Кол.", "Цена", "Доставчик"]

        self._search_flow(
            "продукт или доставчик",
            self.controller.report_deliveries_all,
            self._fmt_delivery,
            "Доставки",
            headers
        )

    # ---------------------------------------------------------
    # Справки: Продажби
    # ---------------------------------------------------------

    def report_sales(self, _):
        result = self.controller.report_sales()
        formatted = self._fmt_sales(result.data)

        self._display_report(
            "Продажби",
            ["Фактура", "Дата", "Клиент", "Продукт", "Общо"],
            formatted
        )

    def search_sales_by_customer(self, _):
        headers = ["Фактура", "Дата", "Клиент", "Продукт", "Общо"]

        self._search_flow(
            "име на клиент",
            self.controller.report_sales_by_customer,
            self._fmt_sales,
            "Продажби",
            headers
        )

    def search_sales_by_product(self, _):
        headers = ["Фактура", "Дата", "Клиент", "Продукт", "Общо"]

        self._search_flow(
            "име на продукт",
            self.controller.report_sales_by_product,
            self._fmt_sales,
            "Продажби",
            headers
        )

    # ---------------------------------------------------------
    # FIFO Анализ
    # ---------------------------------------------------------

    def report_fifo_analysis(self, _):
        """Интерактивен FIFO анализ за конкретен продукт."""

        while True:
            name = input("\nВъведете име или ID на продукт (или 'отказ' за изход): ").strip()

            if not name or name.lower() == "отказ":
                break

            data = self.controller.product_lifecycle(name)

            if not data:
                print(f"Продукт '{name}' не е намерен.")
                continue

            print("\nАнализ по FIFO")
            print("-" * 30)
            print(f"Продукт: {data['product']}")
            print(f"Текуща наличност: {data['current_stock']} {data['unit']}")
            print(f"Общо движение: Вход: {data['total_in']} | Изход: {data['total_out']}")
            print("-" * 30)
            print(f"Приходи: {float(data['revenue']):.2f} лв.")
            print(f"Себестойност: {float(data['fifo_cost']):.2f} лв.")
            print(f"Печалба: {float(data['profit']):.2f} лв.")
            print("-" * 30)

            input("\nНатиснете Enter за връщане...")
            break
