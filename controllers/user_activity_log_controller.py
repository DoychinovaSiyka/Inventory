from models.user_activity_log import UserActivityLog
from storage.json_repository import JSONRepository

class UserActivityLogController:
    def __init__(self, filepath="data/user_activity_log.json"):
        self.repo = JSONRepository(filepath)

    def add_log(self, user_id, action, details=""):
        log = UserActivityLog(user_id, action, details).to_dict()
        data = self.repo.get_all()
        data.append(log)
        self.repo.save(data)

    def get_all_logs(self):
        return self.repo.get_all()


# UserActivityLogController е единственият контролер, който не използва dependency injection.
# Това е умишлено, защото той винаги работи само с един конкретен лог файл и е напълно самостоятелен.
# Всички останали контролери получават JSONRepository отвън, което е по‑професионално и следва SOLID принципите.