from reports.report import Report
from stock_reports.stock_report import StockReport
from movements_report.movement_report import MovementReport

# Логика на справки


class ReportController:
    def __init__(self,product_controller,movement_controller):
        self.product_controller = product_controller
        self.movement_controller = movement_controller

    # Ниски наличности
    def low_stock(self):
        data = StockReport.low_stock(self.product_controller)
        return Report(report_type = "low_stock", result = data)


    # Изчерпани продукти
    def out_of_stock(self):
        data = StockReport.out_of_stock(self.product_controller)
        return Report(report_type="inventory_value",result = data)

    # Движения по период
    def movement_by_period(self,start_date,end_date):
        data = MovementReport.by_period(self.movement_controller,start_date, end_date)
        return Report(report_type = "movements_by_period",params = {"start":start_date,"end":end_date},result = date)

    # Продукти по Категория
    def products_by_category(self,category_id):
        products = self.product_controller.get_by_category(category_id)
        return Report(report_type = "products_by_category",params = {"category_id":category_id},result =[p.to_dict() for p in products])


