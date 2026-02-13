from models.stock_log import StockLog
from storage.json_repository import JSONRepository
from datetime import datetime


class StockLogController:
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        self.logs = [StockLog.from_dict(l) for l in self.repo.load()]

    # CREATE
    def add_log(self, product_id, location_id, quantity, unit, action):
        # Количеството трябва да е > 0
        if quantity <= 0:
            raise ValueError("Количеството трябва да е > 0.")

        # Мерната единица е задължителна
        if not unit or not unit.strip():
            raise ValueError("Мерната единица е задължителна.")

        #  Позволени действия
        allowed_actions = ["add", "remove", "move"]

        if action not in allowed_actions:
            raise ValueError("Невалидно действие. Позволени: add, remove, move.")

        # Създаване на лог
        log = StockLog(
            product_id=product_id,
            location_id=location_id,
            quantity=quantity,
            unit=unit,
            action=action,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        self.logs.append(log)
        self.save_changes()
        return log

    # READ
    def get_all(self):
        return self.logs

    def get_by_product(self, product_id):
        return [log for log in self.logs if log.product_id == product_id]

    def get_by_location(self, location_id):
        return [log for log in self.logs if log.location_id == location_id]

    def search(self, keyword):
        keyword = keyword.lower()
        return [
            log for log in self.logs
            if keyword in log.action.lower()
               or keyword in log.timestamp.lower()
        ]

    # DELETE
    def remove(self, log_id):
        original_len = len(self.logs)
        self.logs = [l for l in self.logs if l.log_id != log_id]

        if len(self.logs) < original_len:
            self.save_changes()
            return True
        return False

    # SAVE
    def save_changes(self):
        self.repo.save([l.to_dict() for l in self.logs])
