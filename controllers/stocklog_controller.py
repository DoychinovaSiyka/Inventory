from models.stock_log import StockLog
from storage.json_repository import JSONRepository
from validators.stock_log_validator import StockLogValidator
from datetime import datetime
from filters.stocklog_filters import (
    filter_by_location, filter_by_product, filter_search
)


class StockLogController:
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        self.logs = [StockLog.from_dict(l) for l in self.repo.load()]

    def add_log(self, product_id, location_id, quantity, unit, action):
        """ Добавя лог запис след валидация и нормализация. """

        #  Валидация и Нормализация (Валидаторът връща чисти данни)
        qty = StockLogValidator.validate_quantity(quantity)
        StockLogValidator.validate_unit(unit)
        StockLogValidator.validate_action(action)

        # Създаване на обекта (Датата се генерира тук и се подава на модела)
        log = StockLog(
            product_id=str(product_id),
            location_id=str(location_id),
            quantity=qty,
            unit=unit,
            action=action,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        self.logs.append(log)
        self.save_changes()
        return log

    # READ операциите ползват филтри
    def get_by_location(self, location_id):
        return filter_by_location(self.logs, str(location_id))

    def get_all(self):
        return self.logs

    def get_by_product(self, product_id):
        return filter_by_product(self.logs, str(product_id))

    def search(self, keyword):
        return filter_search(self.logs, keyword)

    def save_changes(self):
        self.repo.save([l.to_dict() for l in self.logs])
