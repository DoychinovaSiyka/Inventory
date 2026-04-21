from datetime import datetime
from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.report_controller import ReportController
from models.user import User
from models.movement import MovementType


class ReportsView:
    """ Клас за справки – тук четем и показваме данни."""
    def __init__(self, controller: ReportController):
        # Запазваме контролера за справки
        self.controller = controller

        # Контролерите са налични в ReportController
        self.location_controller = controller.location_controller
        self.inventory_controller = controller.inventory_controller
        self.movement_controller = controller.movement_controller

        # Създаваме менюто за справки
        self.menu = self._build_menu()

    def show_menu(self, user: User):
        while True:
            choice = self.menu.show()
            if choice == "0":
                break
            result = self.menu.execute(choice, user)
            if result == "break":
                break

    def _build_menu(self):
        return Menu("Справки и Отчети", [
            MenuItem("1", "Обобщена справка за наличности", self.summary_report),
            MenuItem("2", "Справка за движения", self.report_movements),
            MenuItem("3", "Всички фактури/продажби", self.report_sales),
            MenuItem("4", "Търсене по клиент", self.report_sales_by_customer),
            MenuItem("5", "Търсене по продукт", self.report_sales_by_product),
            MenuItem("6", "Търсене по дата", self.report_sales_by_date),
            MenuItem("7", "Справка за всички доставки", self.report_all_deliveries),
            MenuItem("8", "Търсене на доставка", self.search_delivery),
            MenuItem("9", "Оборот по дни", self.report_turnover_by_day),
            MenuItem("10", "Най-продавани продукти", self.report_top_products),
            MenuItem("11", "Инвентар – наличност по складове", self.report_inventory),
            MenuItem("12", "Жизнен цикъл на продукт", self.report_lifecycle),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    # Помощни функции за форматиране
    @staticmethod
    def _truncate(text, length=20):
        if text is None:
            t = "N/A"
        else:
            t = str(text)
        if len(t) > length:
            return t[:length - 3] + "..."
        return t

    @staticmethod
    def _format_lv(value):
        try:
            if value is None:
                return "-"
            s = str(value).strip()
            if s in ["", "-", "None"]:
                return "-"
            val = float(s)
            if val == 0:
                return "-"
            return f"{val:.2f} лв."
        except (ValueError, TypeError):
            return "-"

    @staticmethod
    def _format_qty_unit(quantity, unit, dash_on_zero=False):
        try:
            if quantity is None:
                return "-" if dash_on_zero else "0"
            val = float(quantity)
            if val == 0 and dash_on_zero:
                return "-"
            unit_str = "" if unit is None else str(unit)
            q = int(val) if val.is_integer() else round(val, 2)
            return f"{q} {unit_str}".strip()
        except (ValueError, TypeError):
            return "-"

    # Въвеждане на непразен текст – празно => прекъсва
    def _input_nonempty(self, prompt):
        value = input(prompt).strip()
        if not value:
            print("[!] Прекъснато – празен вход.\n")
            return None
        return value

    # Въвеждане на продукт за търсене – празно => прекъсва
    def _input_product_search(self):
        value = input("Продукт (име или част от име): ").strip()
        if not value:
            print("[!] Прекъснато – празен вход.\n")
            return None
        return value

    # Въвеждане и валидиране на дата – празно => прекъсва, грешно => пита пак
    def _input_valid_date(self):
        while True:
            value = input("Въведете дата (ГГГГ-ММ-ДД): ").strip()

            if not value:
                print("[!] Прекъснато – празен вход.\n")
                return None

            try:
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                print("[!] Невалидна дата. Използвайте YYYY-MM-DD.")

    # Справка за всички движения
    def report_movements(self, _):
        result = self.controller.report_movements()
        if not result.data:
            print("\n[!] Няма история на движенията.\n")
            return

        if result.summary:
            print("\nОБОБЩЕНИЕ:")
            print(f" - Общо записи: {result.summary.get('total_records', 0)}")
            print(f" - Общо количество: {result.summary.get('total_quantity', 0)}")
            print(f" - Обща стойност: {self._format_lv(result.summary.get('total_value', 0))}\n")

        rows = []
        for item in result.data:
            movement_id = item.get("movement_id", "-")
            m_type = str(item.get("type", "N/A")).upper()
            date_str = str(item.get("date", ""))[:10]
            product_name = self._truncate(item.get("product", "N/A"), 20)
            qty = self._format_qty_unit(item.get("quantity", 0), item.get("unit"))
            price_str = "-" if m_type == "MOVE" else self._format_lv(item.get("price"))
            location = self._truncate(item.get("location", "N/A"), 25)

            rows.append([
                movement_id,
                date_str,
                m_type,
                product_name,
                qty,
                price_str,
                location
            ])

        print(format_table(["ID", "Дата", "Тип", "Продукт", "Кол.", "Цена", "Локация"], rows))

    # Наличност по складове
    def report_inventory(self, _):
        if not self.inventory_controller or "products" not in self.inventory_controller.data:
            print("\n[!] Складовете са празни.\n")
            return

        rows = []
        products = self.inventory_controller.data["products"]

        for pid, pdata in products.items():
            name = pdata.get("name", "N/A")
            unit = pdata.get("unit", "")
            locations = pdata.get("locations", {})

            for wh, qty in locations.items():
                rows.append([
                    self._truncate(name, 25),
                    self._truncate(wh, 15),
                    self._format_qty_unit(qty, unit)
                ])

        rows.sort(key=lambda x: (x[0], x[1]))
        print(format_table(["Продукт", "Склад", "Наличност"], rows))

    # Всички продажби
    def report_sales(self, _):
        result = self.controller.report_sales()
        if not result.data:
            print("\n[!] Няма намерени продажби.\n")
            return

        if result.summary:
            print("\nОБОБЩЕНИЕ:")
            print(f" - Брой продажби: {result.summary.get('total_sales', 0)}")
            print(f" - Общо приходи: {self._format_lv(result.summary.get('total_revenue', 0))}\n")

        self._print_sales_table(result.data)

    def summary_report(self, _):
        result = self.controller.report_inventory_summary()
        if not result.data:
            print("\n[!] Няма налични продукти.\n")
            return

        rows = []
        for item in result.data:
            rows.append([
                self._truncate(item["product"], 25),
                item["available"],
                item["sold"],
                item["top_locations"]
            ])

        print(format_table(
            ["Продукт", "Наличност", "Продадено", "Топ локации"],
            rows
        ))

    def report_sales_by_customer(self, _):
        customer_name = self._input_nonempty("Клиент (име): ")
        if customer_name is None:
            return

        res = self.controller.report_sales_by_customer(customer_name)
        if not res.data:
            print("\n[!] Няма продажби за този клиент.\n")
            return
        self._print_sales_table(res.data)

    def report_sales_by_product(self, _):
        product_search = self._input_product_search()
        if product_search is None:
            return

        res = self.controller.report_sales_by_product(product_search)
        if not res.data:
            print("\n[!] Няма продажби за този продукт.\n")
            return
        self._print_sales_table(res.data)

    # Търсене по дата
    def report_sales_by_date(self, _):
        d = self._input_valid_date()
        if d is None:
            return

        res = self.controller.report_sales_by_date(d)
        if not res.data:
            print("\n[!] Няма продажби на тази дата.\n")
            return

        self._print_sales_table(res.data)

    # Таблица за продажби
    def _print_sales_table(self, data):
        rows = []
        for item in data:
            invoice_number = item.get("invoice_number", "-")
            date_str = str(item.get("date", ""))[:10]
            client_name = self._truncate(item.get("client", "N/A"), 20)
            product_name = self._truncate(item.get("product", "N/A"), 25)
            total_price = self._format_lv(item.get("total_price", 0))

            rows.append([
                invoice_number,
                date_str,
                client_name,
                product_name,
                total_price
            ])

        print(format_table(["Фактура", "Дата", "Клиент", "Продукт", "Общо"], rows))

    # Всички доставки
    def report_all_deliveries(self, _):
        res = self.controller.report_deliveries_all()
        if not res.data:
            print("\n[!] Няма регистрирани доставки.\n")
            return
        self._print_delivery_table(res.data)

    def search_delivery(self, _):
        keyword = self._input_nonempty("Търсене (Продукт/Доставчик/Склад): ")
        if keyword is None:
            return

        res = self.controller.report_deliveries_all(keyword)
        if not res.data:
            print("\n[!] Няма доставки по тези критерии.\n")
            return
        self._print_delivery_table(res.data)

    # Таблица за доставки
    def _print_delivery_table(self, data):
        rows = []
        for item in data:
            date_str = str(item.get("date", ""))[:10]
            movement_id = item.get("movement_id", "-")
            product_name = self._truncate(item.get("product", "N/A"), 20)
            qty = self._format_qty_unit(item.get("quantity", 0), item.get("unit"))
            supplier_name = self._truncate(item.get("supplier", "N/A"), 15)
            location_name = self._truncate(item.get("location", "N/A"), 15)

            rows.append([
                date_str,
                movement_id,
                product_name,
                qty,
                supplier_name,
                location_name
            ])

        print(format_table(["Дата", "ID", "Продукт", "Кол.", "Доставчик", "Склад"], rows))

    # Оборот по дни
    def report_turnover_by_day(self, _):
        res = self.controller.report_turnover_by_day()
        if not res.data:
            print("\n[!] Няма данни за оборот.\n")
            return

        rows = []
        for item in res.data:
            date_str = item.get("date", "N/A")
            count = item.get("count", 0)
            total = self._format_lv(item.get("total", 0))

            rows.append([date_str, count, total])

        print(format_table(["Дата", "Брой продажби", "Оборот"], rows))

    # Най-продавани продукти
    def report_top_products(self, _):
        res = self.controller.report_top_products()
        if not res.data:
            print("\n[!] Няма данни за продажби.\n")
            return

        rows = []
        for item in res.data:
            product_name = self._truncate(item.get("product", "N/A"), 25)
            qty = self._format_qty_unit(item.get("quantity", 0), item.get("unit"))
            total = self._format_lv(item.get("total", 0))

            rows.append([product_name, qty, total])

        print(format_table(["Продукт", "Количество", "Оборот"], rows))

    # Жизнен цикъл на продукт
    def report_lifecycle(self, _):
        name = self._input_nonempty("Въведете име на продукт: ")
        if name is None:
            return

        data = self.controller.product_lifecycle(name)

        if not data or "product" not in data:
            print("\n[!] Продуктът не е намерен или няма движения.\n")
            return

        product_name = data.get("product", "N/A")
        unit = data.get("unit", "")

        initial_stock = float(data.get("initial_stock", 0))
        total_in = float(data.get("total_in", 0))
        total_out = float(data.get("total_out", 0))
        expected_stock = float(data.get("expected_stock", 0))
        current_stock = float(data.get("current_stock", 0))
        revenue = data.get("revenue", 0)

        print(f"\nАНАЛИЗ НА ЖИЗНЕНИЯ ЦИКЪЛ: {product_name}")
        print(f"[+] Начално количество:      {initial_stock:.2f} {unit}")
        print(f"[+] Общо заредено (IN):      {total_in:.2f} {unit}")
        print(f"[-] Общо продадено (OUT):    {total_out:.2f} {unit}")
        print(f"[=] Очаквана наличност:      {expected_stock:.2f} {unit}")
        print(f"[=] Текуща наличност:        {current_stock:.2f} {unit}")
        print(f"Оборот от този продукт:      {self._format_lv(revenue)}\n")

        input("Натиснете Enter за връщане назад...")
