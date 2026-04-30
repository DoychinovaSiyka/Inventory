from datetime import datetime
from views.menu import Menu, MenuItem
from views.password_utils import format_table


class ReportsView:
    def __init__(self, controller):
        self.controller = controller

    def show_menu(self, user):
        menu = self._build_menu()
        while True:
            choice = menu.show()
            if choice == "0":
                break
            menu.execute(choice, user)

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
            MenuItem("11", "Инвентар – наличност по складове", self.inventory_by_warehouse),
            MenuItem("12", "Жизнен цикъл на продукт", self.report_lifecycle),
            MenuItem("0", "Назад", lambda u: "break")])



    # ОБОБЩЕНА СПРАВКА ЗА НАЛИЧНОСТИ
    def summary_report(self, _):
        res = self.controller.report_inventory_summary()
        if not res.data:
            print("\n[!] Няма данни.\n")
            return

        rows = []
        for item in res.data:
            rows.append([item.get("product", "-"), item.get("available", "-"), item.get("sold", "-"),
                         item.get("top_locations", "-")])

        print(format_table(["Продукт", "Наличност", "Продадено", "Топ локации"], rows))


    # СПРАВКА ЗА ДВИЖЕНИЯ
    def report_movements(self, _):
        res = self.controller.report_movements()
        if not res.data:
            print("\n[!] Няма движения.\n")
            return

        rows = []
        for m in res.data:
            rows.append([m.get("movement_id", "-"), m.get("date", "-"), m.get("type", "-"), m.get("product", "-"),
                         f"{m.get('quantity', 0)} {m.get('unit', '')}", m.get("from", "-"), m.get("to", "-")])

        print(format_table(["ID", "Дата", "Тип", "Продукт", "Кол.", "От", "Към"], rows))


    # ВСИЧКИ ПРОДАЖБИ
    def report_sales(self, _):
        res = self.controller.report_sales()
        if not res.data:
            print("\n[!] Няма продажби.\n")
            return

        rows = []
        for item in res.data:
            rows.append([item["invoice_number"], item["date"], item["client"],
                         item["product"], f"{item['total_price']:.2f} лв."])

        print(format_table(["Фактура", "Дата", "Клиент", "Продукт", "Общо"], rows))



    def report_sales_by_customer(self, _):
        name = input("Клиент: ").strip()
        if not name:
            print("[!] Отказано.\n")
            return

        res = self.controller.report_sales_by_customer(name)
        if not res.data:
            print("\n[!] Няма данни.\n")
            return

        rows = []
        for item in res.data:
            rows.append([item["invoice_number"], item["date"], item["client"], item["product"],
                         f"{item['total_price']:.2f} лв."])

        print(format_table(["Фактура", "Дата", "Клиент", "Продукт", "Общо"], rows))



    def report_sales_by_product(self, _):
        name = input("Продукт: ").strip()
        if not name:
            print("[!] Отказано.\n")
            return

        res = self.controller.report_sales_by_product(name)
        if not res.data:
            print("\n[!] Няма продажби.\n")
            return

        rows = []
        for item in res.data:
            rows.append([item["invoice_number"], item["date"], item["client"],
                         item["product"], f"{item['total_price']:.2f} лв."])

        print(format_table(["Фактура", "Дата", "Клиент", "Продукт", "Общо"], rows))


    # ПРОДАЖБИ ПО ДАТА
    def report_sales_by_date(self, _):
        val = input("Дата (ГГГГ-ММ-ДД): ").strip()
        if not val:
            print("[!] Отказано.\n")
            return

        try:
            d = datetime.strptime(val, "%Y-%m-%d")
        except:
            print("[!] Невалидна дата.\n")
            return

        res = self.controller.report_sales_by_date(d)
        if not res.data:
            print("\n[!] Няма продажби.\n")
            return

        rows = []
        for item in res.data:
            rows.append([item["invoice_number"], item["date"], item["client"],
                         item["product"], f"{item['total_price']:.2f} лв."])

        print(format_table(["Фактура", "Дата", "Клиент", "Продукт", "Общо"], rows))


    # ВСИЧКИ ДОСТАВКИ
    def report_all_deliveries(self, _):
        res = self.controller.report_deliveries_all()
        if not res.data:
            print("\n[!] Няма доставки.\n")
            return

        rows = []
        for item in res.data:
            rows.append([item["date"], item["movement_id"], item["product"],
                         f"{item['quantity']} {item['unit']}", item["supplier"], item["location"]])

        print(format_table(["Дата", "ID", "Продукт", "Кол.", "Доставчик", "Склад"], rows))


    #  ТЪРСЕНЕ НА ДОСТАВКА
    def search_delivery(self, _):
        key = input("Търсене: ").strip()
        if not key:
            print("[!] Отказано.\n")
            return

        res = self.controller.report_deliveries_all(key)
        if not res.data:
            print("\n[!] Няма резултати.\n")
            return

        rows = []
        for item in res.data:
            rows.append([item["date"], item["movement_id"], item["product"],
                         f"{item['quantity']} {item['unit']}", item["supplier"], item["location"]])

        print(format_table(["Дата", "ID", "Продукт", "Кол.", "Доставчик", "Склад"], rows))


    # ОБОРОТ ПО ДНИ
    def report_turnover_by_day(self, _):
        res = self.controller.report_turnover_by_day()
        if not res.data:
            print("\n[!] Няма данни.\n")
            return

        rows = []
        for item in res.data:
            rows.append([item["date"],item["count"],f"{item['total']:.2f} лв."])

        print(format_table(["Дата", "Брой", "Оборот"], rows))


    # НАЙ-ПРОДАВАНИ ПРОДУКТИ
    def report_top_products(self, _):
        res = self.controller.report_top_products()
        if not res.data:
            print("\n[!] Няма продажби.\n")
            return

        rows = []
        for item in res.data:
            rows.append([item["product"], f"{item['quantity']} {item['unit']}", f"{item['total']:.2f} лв."])

        print(format_table(["Продукт", "Количество", "Оборот"], rows))


    # ИНВЕНТАР ПО СКЛАДОВЕ
    def inventory_by_warehouse(self, user):
        inventory_data = self.controller.inventory_controller.data.get("products", {})
        all_products = self.controller.product_controller.get_all()
        locations_map = {loc.location_id: loc for loc in self.controller.location_controller.get_all()}

        rows = []
        for product in all_products:
            pid = product.product_id
            p_inv = inventory_data.get(pid, {})
            locs = p_inv.get("locations", {})

            if not locs:
                total_stock = self.controller.inventory_controller.get_total_stock(pid)
                if total_stock > 0:
                    initial_loc_id = getattr(product, 'location_id', 'W1')
                    loc_obj = locations_map.get(initial_loc_id)
                    loc_name = loc_obj.name if loc_obj else initial_loc_id
                    rows.append([loc_name, product.name, f"{total_stock} {product.unit}"])
            else:
                for loc_id, qty in locs.items():
                    if float(qty) > 0:
                        loc = locations_map.get(loc_id)
                        loc_name = loc.name if loc else loc_id
                        rows.append([loc_name, product.name, f"{qty} {product.unit}"])

        if not rows:
            print("\n[!] Няма налични продукти.\n")
            return

        rows.sort(key=lambda r: (r[0], r[1]))
        columns = ["Склад", "Продукт", "Наличност"]
        print("\n   Инвентар – наличност по складове\n")
        print(format_table(columns, rows))



    # ЖИЗНЕН ЦИКЪЛ
    def report_lifecycle(self, _):
        name = input("Продукт: ").strip()
        if not name:
            return

        data = self.controller.product_lifecycle(name)
        if not data:
            print("\n[!] Продуктът не е намерен.\n")
            return

        revenue = data.get("revenue", 0.0)
        cost_of_goods = data.get("fifo_cost", 0.0)  # Себестойност на продаденото
        profit = data.get("profit", 0.0)

        total_invested = data.get("expense", 0.0)  # Всички покупки
        total_in = data.get("total_in", 0.0)
        current_stock = data.get("current_stock", 0.0)

        # Средна покупна цена (ако има покупки)
        if total_in > 0:
            avg_purchase_price = total_invested / total_in
        else:
            avg_purchase_price = 0.0

        # Реална стойност на стоката в склада
        in_stock_value = current_stock * avg_purchase_price
        print("\n" + "═" * 45)
        print(f"   ФИНАНСОВ ОТЧЕТ: {data['product'].upper()}")
        print("═" * 45)
        print(f"  Наличност в склада: {current_stock} {data.get('unit', '')}")
        print(f"  Продадени бройки:   {data['total_out']} {data.get('unit', '')}")
        print("-" * 45)
        print(f"  ОБОРОТ (Продажби):        {revenue:>10.2f} лв.")
        print(f"  СЕБЕСТОЙНОСТ (Разход):    {cost_of_goods:>10.2f} лв.")
        print("-" * 45)
        print(f"  ЧИСТА ПЕЧАЛБА:            {profit:>10.2f} лв.")
        print("═" * 45)
        print(f"  * Стойност на стоката в склада: {in_stock_value:.2f} лв.")
        print("═" * 45)
        input("\nНатиснете Enter за продължение...")
