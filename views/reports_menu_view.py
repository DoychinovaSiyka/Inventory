from typing import List, Dict, Any
from datetime import datetime
from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.report_controller import ReportController
from models.user import User
from models.movement import MovementType  # Критично важен импорт
from validators.movement_validator import MovementValidator
from validators.product_validator import ProductValidator


class ReportsView:
    """
    View клас за визуализация на справки и отчети.
    Следва стриктно MVC архитектурата - не променя данни, само ги показва.
    """

    def __init__(self, controller: ReportController):
        self.controller = controller
        # Безопасно извличане на вложени контролери
        self.location_controller = getattr(controller, 'location_controller', None)
        self.inventory_controller = getattr(controller, 'inventory_controller', None)
        self.movement_controller = getattr(controller, 'movement_controller', None)
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

    # --- ЗАЩИТЕНИ ХЕЛПЪРИ (БРОНИРАНИ СРЕЩУ NONE И ТИПОВИ ГРЕШКИ) ---
    @staticmethod
    def _truncate(text, length=20):
        t = str(text) if text is not None else "N/A"
        return t[:length - 3] + "..." if len(t) > length else t

    @staticmethod
    def _format_lv(value):
        try:
            if value is None or str(value).strip() in ["", "-", "None"]:
                return "-"
            val = float(value)
            return f"{val:.2f} лв." if val != 0 else "-"
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

            u = str(unit) if unit else ""
            q = int(val) if val.is_integer() else round(val, 2)
            return f"{q} {u}".strip()
        except (ValueError, TypeError):
            return "-"

    # --- ВХОДНИ ВАЛИДАТОРИ ---
    def _input_valid_date(self, prompt="Дата (YYYY-MM-DD): "):
        while True:
            d = input(prompt).strip()
            if not d: return None
            try:
                MovementValidator.validate_date(d)
                return d
            except ValueError as e:
                print(f"[!] {e}")

    def _input_nonempty(self, prompt="Въведете стойност: "):
        while True:
            v = input(prompt).strip()
            if v: return v
            print("[!] Полето не може да бъде празно.")

    def _input_product_search(self):
        while True:
            raw = input("Продукт (име или ID): ").strip()
            if raw: return raw
            print("[!] Моля, въведете стойност.")

    # --- СПРАВКИ (РЕАЛИЗАЦИЯ) ---

    def summary_report(self, _):
        """ Обобщена справка: Налично vs Продадено """
        if not self.inventory_controller or not self.inventory_controller.data.get("products"):
            print("\n[!] Системата е празна. Няма наличности.\n")
            return

        inventory = self.inventory_controller.data["products"]
        data = {}

        for pid, pdata in inventory.items():
            data[pid] = {
                "name": pdata.get("name", "N/A"),
                "total": pdata.get("total_stock", 0.0),
                "sold": 0.0,
                "unit": pdata.get("unit", ""),
                "whs": pdata.get("locations", {})
            }

        # Извличане на продажбите директно от движенията (Source of Truth)
        if self.movement_controller:
            for m in self.movement_controller.movements:
                if m.movement_type == MovementType.OUT and m.product_id in data:
                    data[m.product_id]["sold"] += float(m.quantity)

        rows = []
        for pid, info in data.items():
            wh_list = [f"{w}:{self._format_qty_unit(q, '')}" for w, q in info["whs"].items()]
            wh_display = ", ".join(wh_list[:2]) + ("..." if len(wh_list) > 2 else "")

            rows.append([
                self._truncate(info["name"], 25),
                self._format_qty_unit(info["total"], info["unit"]),
                self._format_qty_unit(info["sold"], info["unit"], dash_on_zero=True),
                wh_display if wh_display else "-"
            ])

        rows.sort(key=lambda r: r[0])
        print(format_table(["Продукт", "Налично", "Продадено", "Складове"], rows))

    def report_movements(self, _):
        result = self.controller.report_movements()
        if not result.data:
            print("\n[!] Няма история на движенията.\n")
            return

        rows = []
        for item in result.data:
            m_type = str(item.get("type", "N/A")).upper()
            loc_display = item.get("location_name", "N/A")

            if m_type == "MOVE":
                from_loc = item.get("from_location_name", "N/A")
                loc_display = f"{from_loc} -> {loc_display}"

            rows.append([
                str(item.get("date", ""))[:16],
                m_type,
                self._truncate(item.get("product_name", "N/A"), 20),
                self._format_qty_unit(item.get("quantity", 0), item.get("unit")),
                self._format_lv(item.get("price")) if m_type != "MOVE" else "-",
                self._truncate(loc_display, 25)
            ])

        print(format_table(["Дата/Час", "Тип", "Продукт", "Кол.", "Цена", "Локация"], rows))

    def report_inventory(self, _):
        """ Наличност по конкретни складове """
        if not self.inventory_controller or not self.inventory_controller.data.get("products"):
            print("\n[!] Складовете са празни.\n")
            return

        rows = []
        for pid, pdata in self.inventory_controller.data["products"].items():
            name = pdata.get("name", "N/A")
            unit = pdata.get("unit", "")
            for wh, qty in pdata.get("locations", {}).items():
                rows.append([
                    self._truncate(name, 25),
                    self._truncate(wh, 15),
                    self._format_qty_unit(qty, unit)
                ])

        rows.sort(key=lambda x: (x[0], x[1]))
        print(format_table(["Продукт", "Склад", "Наличност"], rows))

    def report_sales(self, _):
        result = self.controller.report_sales()
        if not result.data:
            print("\n[!] Няма намерени продажби.\n")
            return
        self._print_sales_table(result.data)

    def report_sales_by_customer(self, _):
        c = self._input_nonempty("Клиент (име): ")
        res = self.controller.report_sales_by_customer(c)
        if not res.data:
            print("\n[!] Няма продажби за този клиент.\n")
            return
        self._print_sales_table(res.data)

    def report_sales_by_product(self, _):
        p = self._input_product_search()
        res = self.controller.report_sales_by_product(p)
        if not res.data:
            print("\n[!] Няма продажби за този продукт.\n")
            return
        self._print_sales_table(res.data)

    def report_sales_by_date(self, _):
        d = self._input_valid_date()
        if not d: return
        res = self.controller.report_sales_by_date(d)
        if not res.data:
            print("\n[!] Няма продажби на тази дата.\n")
            return
        self._print_sales_table(res.data)

    def _print_sales_table(self, data):
        rows = []
        for i in data:
            rows.append([
                str(i.get("invoice_number", i.get("movement_id", "")))[:10],
                str(i.get("date", ""))[:10],
                self._truncate(i.get("client") or i.get("customer", "N/A"), 20),
                self._truncate(i.get("product", "N/A"), 25),
                self._format_lv(i.get("total_price", 0))
            ])
        print(format_table(["Фактура", "Дата", "Клиент", "Продукт", "Общо"], rows))

    def report_all_deliveries(self, _):
        res = self.controller.report_deliveries_all()
        if not res.data:
            print("\n[!] Няма регистрирани доставки.\n")
            return
        self._print_delivery_table(res.data)

    def search_delivery(self, _):
        k = self._input_nonempty("Търсене (Продукт/Доставчик/Склад): ")
        res = self.controller.search_deliveries_all(k)
        if not res.data:
            print("\n[!] Няма доставки по тези критерии.\n")
            return
        self._print_delivery_table(res.data)

    def _print_delivery_table(self, data):
        rows = [[
            str(i.get("date", ""))[:10],
            str(i.get("movement_id", ""))[:12],
            self._truncate(i.get("product", "N/A"), 20),
            self._format_qty_unit(i.get("quantity", 0), i.get("unit")),
            self._truncate(i.get("supplier", "N/A"), 15),
            self._truncate(i.get("location_name", "N/A"), 15)
        ] for i in data]
        print(format_table(["Дата", "ID", "Продукт", "Кол.", "Доставчик", "Склад"], rows))

    def report_turnover_by_day(self, _):
        res = self.controller.report_turnover_by_day()
        if not res.data:
            print("\n[!] Няма данни за оборот.\n")
            return
        rows = [[i["date"], i["count"], self._format_lv(i["total"])] for i in res.data]
        print(format_table(["Дата", "Брой", "Оборот"], rows))

    def report_top_products(self, _):
        res = self.controller.report_top_products()
        if not res.data:
            print("\n[!] Няма данни за продажби.\n")
            return
        rows = [[
            self._truncate(i["product"], 25),
            self._format_qty_unit(i["quantity"], i.get("unit")),
            self._format_lv(i["total"])
        ] for i in res.data]
        print(format_table(["Продукт", "Кол.", "Оборот"], rows))

    def report_lifecycle(self, _):
        """ Пълен анализ на жизнения цикъл на продукта """
        name = self._input_nonempty("Въведете име на продукт: ")
        data = self.controller.product_lifecycle(name)

        if not data or "product" not in data:
            print("\n[!] Продуктът не е намерен или няма движения.\n")
            return

        print(f"\nАНАЛИЗ НА ЖИЗНЕНИЯ ЦИКЪЛ: {data.get('product', 'N/A')}")
        print("-" * 45)
        u = data.get('unit', '')
        # Използване на .get() с fallback към 0.0 за всички числови стойности
        print(f"[+] Начално количество:      {float(data.get('initial_stock', 0)):.2f} {u}")
        print(f"[+] Общо заредено (IN):      {float(data.get('total_in', 0)):.2f} {u}")
        print(f"[-] Общо продадено (OUT):    {float(data.get('total_out', 0)):.2f} {u}")
        print(f"[=] Очаквана наличност:      {float(data.get('expected_stock', 0)):.2f} {u}")
        print(f"[=] Текуща наличност:        {float(data.get('current_stock', 0)):.2f} {u}")
        print("-" * 45)
        print(f"Оборот от този продукт:      {self._format_lv(data.get('revenue', 0))}\n")

        input("Натиснете Enter за връщане назад...")