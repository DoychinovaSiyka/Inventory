from models.stock_log import StockLog
from datetime import datetime


class StockLogController:
    def __init__(self, repo):
        self.repo = repo
        self.logs = [StockLog.from_dict(l) for l in self.repo.load()]

    # ID GENERATOR
    def _generate_id(self):
        if not self.logs:
            return 1
        return max(log.log_id for log in self.logs) + 1

    # CREATE
    def add_log(self, product_id, location_id, quantity, unit, action):
        # quantity вече е float
        if quantity <= 0:
            raise ValueError("Количеството трябва да е > 0.")

        if not unit or not unit.strip():
            raise ValueError("Мерната единица е задължителна.")

        if action not in ["add", "remove", "move"]:
            raise ValueError("Невалидно действие. Позволени: add, remove, move.")

        log = StockLog(
            log_id=self._generate_id(),
            product_id=product_id,
            location_id=location_id,
            quantity=quantity,
            unit=unit,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            action=action
        )

        self.logs.append(log)
        self._save()
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

    # DELETE (optional)
    def remove(self, log_id):
        original_len = len(self.logs)
        self.logs = [l for l in self.logs if l.log_id != log_id]

        if len(self.logs) < original_len:
            self._save()
            return True
        return False

    # SAVE
    def _save(self):
        self.repo.save([l.to_dict() for l in self.logs])
