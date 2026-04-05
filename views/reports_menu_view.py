from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.report_controller import ReportController
from models.user import User



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
        return Menu("Справки и Отчети", [MenuItem("1", "Справка за наличности", self.report_stock),
                                         MenuItem("2", "Справка за движения", self.report_movements),
                                         MenuItem("3", "Всички фактури/продажби", self.report_sales),
                                         MenuItem("4", "Търсене по клиент", self.report_sales_by_customer),
                                         MenuItem("5", "Търсене по продукт", self.report_sales_by_product),
                                         MenuItem("6", "Търсене по дата", self.report_sales_by_date),
                                         MenuItem("0", "Назад", lambda u: "break")])

    @staticmethod
    def _clean_none(value, replacement="—"):
        return replacement if value is None else str(value)

    @staticmethod
    def _format_lv(value):
        try:
            val = round(float(value), 2)
            return f"{val:.2f} лв."
        except:
            return "0.00 лв."

    @staticmethod
    def _format_qty(value, product_name=""):
        try:
            if value is None:
                return "0 бр."
            val = float(value)
            display_val = int(val) if val.is_integer() else round(val, 2)
            name = str(product_name).lower()
            unit = "кг" if any(x in name for x in ["брашно", "захар", "домати", "кг"]) else "бр."
            return f"{display_val} {unit}"
        except:
            return str(value)

    # ПРОДАЖБИ
    def _process_data(self, data):
        rows = []
        has_id = False
        for item in data:
            row_id = item.get('invoice_id')
            if row_id:
                has_id = True
            p_name = item.get('product', '—')
            qty = float(item.get('quantity', 0) or 0)

            raw_total = item.get('total_price', item.get('total', 0))
            total = float(raw_total or 0)
            raw_price = item.get('price')
            if raw_price is None or raw_price == 0:
                price = round(total / qty, 2) if qty > 0 else 0
            else:
                price = round(float(raw_price), 2)

            rows.append([row_id, p_name, self._format_qty(qty, p_name), self._format_lv(price), self._format_lv(total),
                         self._clean_none(item.get('customer')), self._clean_none(item.get('date'))])
        return rows, has_id

    # СПРАВКИ
    # ПРОДАЖБИ → ИМАТ ID (ако JSON съдържа ID)
    def _print_sales(self, data):
        rows, has_id = self._process_data(data)
        columns = ["ID", "Продукт", "Количество", "Ед. Цена", "Общо", "Клиент", "Дата"]
        #  Ако НЯМА ID → махаме колоната
        if not has_id:
            columns = columns[1:]  # махаме ID
            rows = [row[1:] for row in rows]
        print(format_table(columns, rows))

    def report_sales(self, _):
        data = self.controller.report_sales().data
        if not data:
            print("\nНяма налични фактури или продажби.\n")
            return
        self._print_sales(data)

    def report_sales_by_customer(self, _):
        customer = input("Клиент: ")
        data = self.controller.report_sales_by_customer(customer).data
        if not data:
            print(f"\nНяма резултати за клиент: {customer}\n")
            return
        self._print_sales(data)

    def report_sales_by_product(self, _):
        product = input("Продукт: ")
        data = self.controller.report_sales_by_product(product).data
        if not data:
            print(f"\nНяма резултати за продукт: {product}\n")
            return
        self._print_sales(data)

    def report_sales_by_date(self, _):
        date = input("Дата: ")
        data = self.controller.report_sales_by_date(date).data
        if not data:
            print(f"\nНяма резултати за дата: {date}\n")
            return
        self._print_sales(data)

    # НАЛИЧНОСТИ → БЕЗ ID
    def report_stock(self, _):
        data = self.controller.report_stock().data
        if not data:
            print("\nНяма налични продукти.\n")
            return
        rows = [[i['product'], self._format_qty(i['quantity'], i['product']), self._format_lv(i['price'])]
                for i in data]
        print(format_table(["Продукт", "Количество", "Цена"], rows))

    # ДВИЖЕНИЯ → ИМАТ ID (movement_id)
    def report_movements(self, _):
        data = self.controller.report_movements().data

        if not data:
            print("\nНяма налични движения.\n")
            return

        rows = []
        for i in data:
            # устойчиво извличане на ID на локацията
            loc_id = ( i.get('location_id') or i.get('location') or i.get('loc')
                       or i.get('warehouse') or i.get('warehouse_id'))

            # Намиране на склада
            location = self.location_controller.get_by_id(loc_id) if loc_id else None
            location_name = location.name if location else "Няма склад"

            rows.append([self._clean_none(i.get('date')), self._clean_none(i.get('type')), i.get('movement_id'),
                         self._format_qty(i.get('quantity', 0), i.get('product_name', 'Продукт')), self._format_lv(i.get('price', 0)),
                         location_name])
        print(format_table(["Дата", "Тип", "ID", "Кол.", "Цена", "Склад"], rows))
