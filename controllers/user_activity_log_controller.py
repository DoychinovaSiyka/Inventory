import uuid
import json  # Добавяме директен импорт за сигурност
from datetime import datetime
from models.user_activity_log import UserActivityLog
from storage.json_repository import JSONRepository


class UserActivityLogController:
    def __init__(self, filepath="data/user_activity_log.json"):
        self.filepath = filepath
        self.repo = JSONRepository(filepath)

    @staticmethod
    def _generate_log_id():
        return str(uuid.uuid4())

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # CREATE
    def add_log(self, user_id, action, details=""):
        """Добавя нов лог запис без да презаписва старите."""

        # Създавам новия запис
        log_entry = UserActivityLog(user_id, action, details, timestamp=self._now()).to_dict()
        log_entry["log_id"] = self._generate_log_id()

        try:
            # Зареждам съществуващите логове
            data = self.repo.get_all()

            # Ако repo.get_all() връща речник вместо списък, го превръщам
            if isinstance(data, dict):
                logs = list(data.values())
            elif isinstance(data, list):
                logs = data
            else:
                logs = []

            # Добавям новия лог
            logs.append(log_entry)

            # ЗАПИС: Използвам директен запис, за да не се бърка JSONRepository
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"Грешка при запис на лог: {e}")

    # READ
    def get_all(self):
        data = self.repo.get_all()
        if isinstance(data, dict):
            return list(data.values())
        return data if isinstance(data, list) else []

# UserActivityLogController е единственият контролер, който не използва dependency injection.
# Това е умишлено, защото той винаги работи само с един конкретен лог файл и е
# напълно самостоятелен. Всички останали контролери получават JSONRepository отвън,
# което е по‑професионално и следва SOLID принципите.
