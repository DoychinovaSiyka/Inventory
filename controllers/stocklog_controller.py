from models.stock_log import StockLog
from storage.json_repository import JSONRepository
from datetime import datetime


class StockLogController:
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        # Зареждаме съществуващите логове
        self.logs = [StockLog.from_dict(l) for l in self.repo.load()]

    # Помощни методи (валидации)
    @staticmethod
    def _validate_quantity(quantity):
        # Валидация на количеството
        if quantity <= 0:
            raise ValueError("Количеството трябва да е по-голямо от 0.")

    @staticmethod
    def _validate_unit(unit):
        if not unit or not unit.strip():
            raise ValueError("Мерната единица е задължителна.")

    @staticmethod
    def _validate_action(action):
        # РАЗШИРЕНИ позволени действия за по-добра отчетност
        # Добавяме move_in и move_out за нуждите на логистиката
        allowed_actions = ["add", "remove", "move", "move_in", "move_out"]
        if action not in allowed_actions:
            raise ValueError(f"Невалидно действие '{action}'. Позволени: {allowed_actions}")

    # CREATE
    def add_log(self, product_id, location_id, quantity, unit, action):
        self._validate_quantity(quantity)
        self._validate_unit(unit)
        self._validate_action(action)

        # Генериране на уникално ID за лога (ако моделът ти го изисква)
        # Ако StockLog няма автоматично ID, можеш да добавиш логика тук

        # Създаване на лог запис
        # Уверяваме се, че location_id се записва точно (напр. "W1")
        log = StockLog(product_id=str(product_id), location_id=str(location_id), quantity=float(quantity),
                       unit=unit, action=action, timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        self.logs.append(log)
        self.save_changes()
        return log

    # READ
    # Филтриране по локация ( за проверка на складовете поотделно)
    def get_by_location(self, location_id):
        return [log for log in self.logs if str(log.location_id) == str(location_id)]

    # Другите методи остават същите
    def get_all(self):
        return self.logs

    def get_by_product(self, product_id):
        return [log for log in self.logs if log.product_id == product_id]

    def search(self, keyword):
        keyword = keyword.lower()
        return [ log for log in self.logs if keyword in log.action.lower() or keyword in log.timestamp.lower()]

    # SAVE
    def save_changes(self):
        self.repo.save([l.to_dict() for l in self.logs])
