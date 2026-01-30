from models.stock_log import StockLog
from datetime import datetime

class StockLogController:
    def __init__(self,repo):
        self.repo = repo
        self.logs = [StockLog.from_dict(l) for l in self.repo.load()]

    # Генериране на ID
    def _generate_id(self):
        if not self.logs:
            return 1
        return max(log.log_id for log in self.logs) + 1

    # Връщаме всички логове
    def get_all(self):
        return self.logs

    # Филтър по продукт
    def get_by_product(self,product_id):
        return [log for log in self.logs if log.product_id == product_id]



    # Филтър по локация
    def get_by_location(self,location_id):
        return [log for log in self.logs if log.location_id == location_id]

    # Добавяне на лог
    def add_log(self,product_id,location_id,quantity,action):
        if quantity <= 0:
            raise ValueError("Количеството трябва да е > 0.")
        if action not in ["add","remove","move"]:
            raise ValueError("Невалидно действие.Позволени: add,remove,move.")

        log = StockLog(log_id = self._generate_id(),
                       product_id = product_id,
                       location_id = location_id,
                       quantity = quantity,
                       timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                       action = action)

        self.logs.append(log)
        self._save()
        return log

    # Запис в JSON
    def _save(self):
        self.repo.save([l.to_dict() for l in self.logs])
