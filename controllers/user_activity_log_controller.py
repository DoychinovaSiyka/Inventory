from typing import List, Optional
from models.user_activity_log import UserActivityLog



class UserActivityLogController:
    def __init__(self, repo):
        self.repo = repo
        raw_data = self.repo.load() or []
        # Зареждаме и сортираме по дата
        self.logs: List[UserActivityLog] = [UserActivityLog.from_dict(l) for l in raw_data]
        self.logs.sort(key=lambda x: x.timestamp, reverse=True)

    def log_action(self, user_id, action, details=""):
        new_log = UserActivityLog(user_id=str(user_id), action=action, details=details)
        self.logs.insert(0, new_log)
        self.save_changes()
        return new_log

    def get_all(self) -> List[UserActivityLog]:
        return self.logs

    def get_by_user(self, user_id: str) -> List[UserActivityLog]:
        uid = str(user_id).strip()
        # Търсим точно съвпадение за сигурност
        return [log for log in self.logs if str(log.user_id) == uid]

    def search_by_action(self, action_keyword: str) -> List[UserActivityLog]:
        keyword = action_keyword.lower()
        return [log for log in self.logs if keyword in log.action.lower()]

    def save_changes(self):
        # Записваме само последните 1000 лога например, за да не гърми диска - опционално
        self.repo.save([log.to_dict() for log in self.logs])

    def clear_logs(self):
        self.logs = []
        self.save_changes()