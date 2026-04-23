import uuid
import json  # Използва се за директен запис в JSON файла
from datetime import datetime
from models.user_activity_log import UserActivityLog
from storage.json_repository import JSONRepository


class UserActivityLogController:
    def __init__(self, filepath="data/user_activity_log.json"):
        # Път до файла, в който се съхраняват логовете
        self.filepath = filepath
        # Репозитори за четене на JSON съдържанието
        self.repo = JSONRepository(filepath)

    @staticmethod
    def _generate_log_id():
        # Генерира уникален идентификатор за всеки лог запис
        return str(uuid.uuid4())

    @staticmethod
    def _now() -> str:
        # Връща текущата дата и час във формат YYYY-MM-DD HH:MM:SS
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # CREATE
    def add_log(self, user_id, action, details=""):
        """Добавя нов запис в лог файла, без да изтрива или презаписва старите записи."""

        # Създаваме нов лог запис като речник
        log_entry = UserActivityLog(user_id, action, details, timestamp=self._now()).to_dict()
        log_entry["log_id"] = self._generate_log_id()

        try:
            # Зареждаме текущото съдържание на лог файла
            data = self.repo.get_all()

            # Уеднаквяване на структурата – ако е речник, го превръщаме в списък
            if isinstance(data, dict):
                logs = list(data.values())
            elif isinstance(data, list):
                logs = data
            else:
                logs = []

            # Добавям новия запис към списъка
            logs.append(log_entry)
            # Записваме обратно в JSON файла
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"Грешка при запис на лог: {e}")

    # READ
    def get_all(self):
        # Връща всички логове като списък, независимо от формата в JSON файла
        data = self.repo.get_all()
        if isinstance(data, dict):
            return list(data.values())
        return data if isinstance(data, list) else []




# UserActivityLogController е единственият контролер, който не използва dependency injection.
# Това е умишлено, защото той винаги работи само с един конкретен лог файл и е
# напълно самостоятелен. Всички останали контролери получават JSONRepository отвън,
# което е по‑професионално и следва SOLID принципите.
