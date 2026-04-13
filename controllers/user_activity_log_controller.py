from models.user_activity_log import UserActivityLog
from storage.json_repository import JSONRepository


class UserActivityLogController:
    def __init__(self, filepath="data/user_activity_log.json"):
        # UserActivityLogController е единственият контролер, който не използва
        # dependency injection.
        # Това е умишлено, защото той винаги работи само с един конкретен лог файл и е
        # напълно самостоятелен.
        # Всички останали контролери получават JSONRepository отвън,
        # което е по‑професионално и следва SOLID принципите.
        self.repo = JSONRepository(filepath)

    # CREATE
    def add_log(self, user_id, action, details=""):
        # Създаваме лог записа чрез модела
        log_entry = UserActivityLog(user_id, action, details).to_dict()

        # Зареждаме текущите записи
        data = self.repo.get_all()

        # Добавяме новия запис
        data.append(log_entry)

        # Записваме обратно в JSON файла
        self.repo.save(data)

    # READ
    def get_all_logs(self):
        # Връща всички логове от JSON файла
        return self.repo.get_all()


# UserActivityLogController е единственият контролер, който не използва dependency injection.
# Това е умишлено, защото той винаги работи само с един конкретен лог файл и е
# напълно самостоятелен.
# Всички останали контролери получават JSONRepository отвън,
# което е по‑професионално и следва SOLID принципите.
