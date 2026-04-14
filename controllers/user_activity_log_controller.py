import uuid
from models.user_activity_log import UserActivityLog
from storage.json_repository import JSONRepository


class UserActivityLogController:
    def __init__(self, filepath="data/user_activity_log.json"):
        # UserActivityLogController е единственият контролер, който не използва
        # dependency injection.
        # Това е умишлено, защото той винаги работи само с един конкретен лог файл и е
        # напълно самостоятелен. Всички останали контролери получават JSONRepository отвън,
        # което е по‑професионално и следва SOLID принципите.
        self.repo = JSONRepository(filepath)

    # Вътрешен метод за генериране на уникално ID за всеки лог
    @staticmethod
    def _generate_log_id():
        return str(uuid.uuid4())

    # CREATE
    def add_log(self, user_id, action, details=""):
        # Създавам лог записа чрез модела
        log_entry = UserActivityLog(user_id, action, details).to_dict()
        # Добавяме уникално log_id
        log_entry["log_id"] = self._generate_log_id()

        # Зареждам текущите записи
        data = self.repo.get_all()
        if not isinstance(data, list):
            data = []  # защита при повреден или празен JSON

        # Добавям новия запис
        data.append(log_entry)
        # Записвам обратно в JSON файла
        self.repo.save(data)

    # READ
    def get_all_logs(self):
        # Връща всички логове от JSON файла
        data = self.repo.get_all()
        return data if isinstance(data, list) else []


# UserActivityLogController е единственият контролер, който не използва dependency injection.
# Това е умишлено, защото той винаги работи само с един конкретен лог файл и е
# напълно самостоятелен.
# Всички останали контролери получават JSONRepository отвън,
# което е по‑професионално и следва SOLID принципите.
