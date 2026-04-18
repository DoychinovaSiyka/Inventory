from typing import List
from datetime import datetime
from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.report_controller import ReportController
from models.user import User
from validators.movement_validator import MovementValidator
from validators.product_validator import ProductValidator


class ReportsView:
    def __init__(self, controller: ReportController):
        self.controller = controller
        self.location_controller = controller.location_controller
        self.menu = self._build_menu()

    def show_menu(self, user: User):
        while True:
            choice = self.menu.show()
            if self.menu.execute(choice, user) == "break":
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
            MenuItem("8", "Търсене на доставка (по продукт, доставчик, описание или склад)", self.search_delivery),
            MenuItem("9", "Оборот по дни", self.report_turnover_by_day),
            MenuItem("10", "Най-продавани продукти", self.report_top_products),
            MenuItem("11", "Инвентар – наличност по складове", self.report_inventory),
            MenuItem("12", "Жизнен цикъл на продукт", self.report_lifecycle),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    # HELPERS

    @staticmethod
    def _truncate(text, length=20):
        t = str(text)
        return t[:length - 3] + "..." if len(t) > length else t

    @staticmethod
    def _format_lv(value):
        try:
            if value is None or value == "" or value == "-":
                return "-"
            val = float(value)
            return f"{val:.2f} лв." if val != 0 else "-"
        except:
            return "-"

    @staticmethod
    def _format_qty_unit(quantity, unit, dash_on_zero=False):
        if quantity is None or float(quantity) == 0:
            return "-" if dash_on_zero else "0"
        u = unit if unit else ""
        q = int(quantity) if float(quantity).is_integer() else round(float(quantity), 2)
        return f"{q} {u}".strip()

    # VALIDATED INPUT HELPERS

    def _input_valid_date(self, prompt="Дата (YYYY-MM-DD): "):
        while True:
            d = input(prompt).strip()
            try:
                MovementValidator.validate_date(d)
                return d
            except ValueError as e:
                print(f"[!] {e}")

    def _input_nonempty(self, prompt="Въведете стойност: "):
        while True:
            v = input(prompt).strip()
            if v:
                return v
            print("[!] Полето не може да бъде празно.")

    def _input_product_search(self):
        """Позволява: част от име, ID, номер."""
        while True:
            raw = input("Продукт (име, част от име или ID): ").strip()
            if not raw:
                print("[!] Моля, въведете стойност.")
                continue

            # 1) Ако е UUID → валидираме
            try:
                ProductValidator.validate_uuid(raw)
                return raw
            except:
                pass

            # 2) Ако е част от име → връщаме директно
            return raw

    def _input_location_search(self):
        """Позволява: номер (1→W1), W1–W9, част от име."""
        while True:
            raw = input("Склад (номер, ID или част от име): ").strip()
            if not raw:
                print("[!] Моля, въведете стойност.")
                continue

            # Опит за нормализиране чрез валидатора
            try:
                loc_id = MovementValidator.validate_location_id(raw, self.location_controller)
                return loc_id
            except:
                # Ако не е валидно ID → връщаме като текст за търсене по име
                return raw

    # REPORTS

    def report_movements(self, _):
        result = self.controller.report_movements()
        if not result.data:
            print("\n[!] Няма налични движения.\n")
            return

        rows = []
        for item in result.data:
            m_type = item["type"].upper()

            price_val = item.get("price")
            formatted_price = self._format_lv(price_val) if m_type != "MOVE" else "-"

            if m_type == "MOVE":
                from_loc = item.get("from_location_name", "N/A")
                to_loc = item.get("location_name", "N/A")
                loc_display = f"{from_loc} → {to_loc}"
            else:
                loc_display = item.get("location_name", "N/A")

            rows.append([
                item["date"][:16],
                m_type,
                self._truncate(item.get("product_name", "N/A"), 20),
                item["movement_id"],
                self._format_qty_unit(item["quantity"], item.get("unit")),
                formatted_price,
                self._truncate(loc_display, 25)
            ])

        rows.sort(key=lambda x: x[0], reverse=True)
        print(format_table(
            ["Дата/Час", "Тип", "Продукт", "ID", "Кол.", "Цена", "Локация"],
            rows
        ))

    def report_inventory(self, _):
        inventory = self.controller.inventory_controller.data["products"]

        if not inventory:
            print("\n[!] Складът е празен.\n")
            return

        rows = []
        for pid, pdata in inventory.items():
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

    def summary_report(self, _):
        inventory = self.controller.inventory_controller.data["products"]

        if not inventory:
            print("\nНяма наличности.\n")
            return

        data = {}

        from models.movement import MovementType
        for pid, pdata in inventory.items():
            data[pid] = {
                "name": pdata.get("name", "N/A"),
                "total": pdata.get("total_stock", 0.0),
                "sold": 0.0,
                "unit": pdata.get("unit", ""),
                "whs": pdata.get("locations", {})
            }

        for m in self.controller.movement_controller.movements:
            if m.movement_type == MovementType.OUT and m.product_id in data:
                data[m.product_id]["sold"] += float(m.quantity)

        rows = []
        for pid, info in data.items():
            wh_list = [f"{w}:{self._format_qty_unit(q, '')}" for w, q in info["whs"].items()]
            wh_display = ", ".join(wh_list[:3])
            if len(wh_list) > 3:
                wh_display += "..."

            rows.append([
                self._truncate(info["name"], 25),
                self._format_qty_unit(info["total"], info["unit"]),
                self._format_qty_unit(info["sold"], info["unit"], dash_on_zero=True),
                wh_display
            ])

        rows.sort(key=lambda r: r[0])
        print(format_table(["Продукт", "Налично", "Продадено", "Складове"], rows))

    def report_sales(self, _):
        result = self.controller.report_sales()
        if not result.data:
            print("\n[!] Няма намерени фактури.\n")
            return

        rows = [
            [
                i["invoice_number"][:10],
                i["date"][:10],
                self._truncate(i["client"], 22),
                self._truncate(i["product"], 30),
                self._format_lv(i["total_price"])
            ]
            for i in result.data
        ]

        print(format_table(
            ["Фактура", "Дата", "Клиент", "Продукт", "Общо"],
            rows
        ))

    def report_sales_by_customer(self, _):
        c = self._input_nonempty("Клиент (име или част от име): ")
        res = self.controller.report_sales_by_customer(c)
        if not res.data:
            print("\n[!] Няма такъв клиент или няма продажби.\n")
            return
        self._print_sales_table(res.data)

    def report_sales_by_product(self, _):
        p = self._input_product_search()
        res = self.controller.report_sales_by_product(p)
        if not res.data:
            print("\n[!] Няма такъв продукт или няма продажби.\n")
            return
        self._print_sales_table(res.data)

    def report_sales_by_date(self, _):
        d = self._input_valid_date()
        res = self.controller.report_sales_by_date(d)
        if not res.data:
            print("\n[!] Няма продажби за тази дата.\n")
            return
        self._print_sales_table(res.data)

    def _print_sales_table(self, data):
        rows = [
            [
                i.get("invoice_id", i.get("invoice_number", ""))[:10],
                i["date"][:10],
                self._truncate(i.get("customer") or i.get("client", ""), 22),
                self._truncate(i["product"], 30),
                self._format_lv(i["total_price"])
            ]
            for i in data
        ]

        print(format_table(
            ["Фактура", "Дата", "Клиент", "Продукт", "Общо"],
            rows
        ))

    def report_all_deliveries(self, _):
        res = self.controller.report_deliveries_all()
        if not res.data:
            print("\n[!] Няма доставки.\n")
            return

        rows = [
            [
                i["date"][:10],
                i["movement_id"][:12],
                self._truncate(i["product"], 20),
                self._format_qty_unit(i["quantity"], i.get("unit")),
                self._truncate(i["supplier"], 15),
                self._truncate(i["location_name"], 15)
            ]
            for i in res.data
        ]

        print(format_table(["Дата", "ID", "Продукт", "Кол.", "Доставчик", "Склад"], rows))

    def search_delivery(self, _):
        k = self._input_nonempty("Търсене (име, ID, склад или част от описание): ")

        # Ако е локация → нормализираме
        try:
            k = MovementValidator.validate_location_id(k, self.location_controller)
        except:
            pass

        res = self.controller.search_deliveries_all(k)
        if not res.data:
            print("\n[!] Няма доставки по тези критерии.\n")
            return

        rows = [
            [
                i["date"][:10],
                i["movement_id"][:12],
                self._truncate(i["product"], 20),
                self._format_qty_unit(i["quantity"], i.get("unit")),
                self._truncate(i["supplier"], 15),
                self._truncate(i["location_name"], 15)
            ]
            for i in res.data
        ]

        print(format_table(["Дата", "ID", "Продукт", "Кол.", "Доставчик", "Склад"], rows))

    def report_turnover_by_day(self, _):
        res = self.controller.report_turnover_by_day()
        if not res.data:
            print("\n[!] Няма данни за оборот.\n")
            return

        rows = [
            [i["date"], i["count"], self._format_lv(i["total"])]
            for i in res.data
        ]

        print(format_table(["Дата", "Брой", "Оборот"], rows))

    def report_top_products(self, _):
        res = self.controller.report_top_products()
        if not res.data:
            print("\n[!] Няма данни за продажби.\n")
            return

        rows = [
            [
                self._truncate(i["product"], 25),
                self._format_qty_unit(i["quantity"], i.get("unit")),
                self._format_lv(i["total"])
            ]
            for i in res.data
        ]

        print(format_table(["Продукт", "Кол.", "Оборот"], rows))

    def report_lifecycle(self, _):
        name = self._input_nonempty("Въведете име на продукт: ")
        data = self.controller.product_lifecycle(name)

        if not data:
            print("\n[!] Продуктът не е намерен или няма движения.\n")
            return

        print(f"\nАНАЛИЗ НА ЖИЗНЕНИЯ ЦИКЪЛ: {data['product']}")
        print("--------------------------------------")
        print(f"[+] Начално количество:      {data['initial_stock']:.2f} {data['unit']}")
        print(f"[+] Общо заредено (IN):      {data['total_in']:.2f} {data['unit']}")
        print(f"[-] Общо продадено (OUT):    {data['total_out']:.2f} {data['unit']}")
        print(f"[=] Очаквана наличност:      {data['expected_stock']:.2f} {data['unit']}")
        print(f"[=] Текуща наличност:        {data['current_stock']:.2f} {data['unit']}")
        print("--------------------------------------")
        print(f"Оборот от този продукт:      {data['revenue']:.2f} лв.\n")

        input("Натиснете Enter за връщане назад...")
