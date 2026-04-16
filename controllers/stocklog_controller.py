from datetime import datetime
from models.stock_log import StockLog
from storage.json_repository import JSONRepository
from validators.stock_log_validator import StockLogValidator
from datetime import datetime
from filters.stocklog_filters import (filter_by_location, filter_by_product, filter_search)



class StockLogController:
    """ Контролер за логове на складови операции. Координира валидатор, модел, филтри и хранилище. Не съдържа бизнес логика."""

    def __init__(self, repo: JSONRepository):
        self.repo = repo
        raw = self.repo.load() or []
        self.logs = [StockLog.from_dict(l) for l in raw]

    # INTERNAL HELPERS
    @staticmethod
    def _now() -> str:
        """Връща текущата дата и час в стандартен формат."""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # CREATE
    def add_log(self, product_id, location_id, quantity, unit, action):
        """ Добавя нов лог запис след валидация. Контролерът не съдържа бизнес логика – само координира."""
        qty = StockLogValidator.validate_quantity(quantity)
        StockLogValidator.validate_unit(unit)
        StockLogValidator.validate_action(action)
        # Създаване на обекта - Датата се генерира тук и се подава на модела
        log = StockLog(product_id=str(product_id), location_id=str(location_id),
                       quantity=qty, unit=unit, action=action, timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.logs.append(log)
        self.save_changes()
        return log

    # READ
    def get_all(self):
        """Връща всички логове."""
        return self.logs

    def get_by_location(self, location_id):
        """Филтрира логове по локация."""
        return filter_by_location(self.logs, str(location_id))

    def get_by_product(self, product_id):
        """Филтрира логове по продукт."""
        return filter_by_product(self.logs, str(product_id))

    def search_logs(self, keyword):
        """Търсене в логовете по ключова дума."""
        return filter_search(self.logs, keyword)

    # SAVE
    def save_changes(self):
        """Записва логовете в JSON хранилището."""
        self.repo.save([l.to_dict() for l in self.logs])
