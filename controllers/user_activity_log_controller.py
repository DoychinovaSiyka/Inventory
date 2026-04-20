import uuid
from datetime import datetime
from models.user_activity_log import UserActivityLog
from storage.json_repository import JSONRepository


class UserActivityLogController:
    def __init__(self, filepath="data/user_activity_log.json"):
        # Този контролер е единственият, който не използва dependency injection.
        # Причината е, че работи само с един конкретен лог файл и е напълно самостоятелен.
        # Всички други контролери получават JSONRepository отвън, което е по‑чисто и следва SOLID принципите.
        self.repo = JSONRepository(filepath)

    # Генерирам уникално ID за всеки лог запис
    @staticmethod
    def _generate_log_id():
        return str(uuid.uuid4())

    @staticmethod
    def _now() -> str:
        """Връща текущата дата и час в стандартен формат."""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # CREATE
    def add_log(self, user_id, action, details=""):
        """Добавя нов лог запис. Контролерът не съдържа бизнес логика – просто създава модела и го записва."""

        # Създавам лог записа чрез модела
        log_entry = UserActivityLog(user_id, action, details, timestamp = self._now()).to_dict()

        # Добавям уникално log_id
        log_entry["log_id"] = self._generate_log_id()

        # Зареждам текущите записи от файла
        data = self.repo.get_all()
        if not isinstance(data, list):
            data = []  # защита при празен или повреден JSON

        # Добавям новия запис
        data.append(log_entry)

        # Записвам обратно в JSON файла
        self.repo.save(data)

    # READ – връща всички логове от JSON файла
    def get_all(self):
        data = self.repo.get_all()
        return data if isinstance(data, list) else []


# UserActivityLogController е единственият контролер, който не използва dependency injection.
# Това е умишлено, защото той винаги работи само с един конкретен лог файл и е
# напълно самостоятелен. Всички останали контролери получават JSONRepository отвън,
# което е по‑професионално и следва SOLID принципите.
