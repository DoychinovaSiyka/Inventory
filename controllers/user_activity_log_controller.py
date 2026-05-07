from typing import List, Optional
from models.user_activity_log import UserActivityLog

class UserActivityLogController:
    """Контролерът управлява логовете и ги записва в JSON."""
    def __init__(self, repo):
        self.repo = repo
        # Зареждаме съществуващите логове
        raw_data = self.repo.load() or []
        self.logs: List[UserActivityLog] = [UserActivityLog.from_dict(l) for l in raw_data]


    def log_action(self, user_id, action, details=""):
        # user_id тук трябва да е пълното UUID (вече го оправихме в MovementController и ProductController)
        new_log = UserActivityLog(user_id=str(user_id), action=action, details=details)
        self.logs.append(new_log)
        self.save_changes()
        return new_log

    # READ - Получаване на всички логове
    def get_all(self) -> List[UserActivityLog]:
        return self.logs

    # READ - Филтриране по потребител
    def get_by_user(self, user_id: str) -> List[UserActivityLog]:
        """Връща действия на потребител, поддържа и кратко ID."""
        uid = str(user_id).strip()
        return [log for log in self.logs if str(log.user_id).startswith(uid)]

    # READ - Търсене по действие
    def search_by_action(self, action_keyword: str) -> List[UserActivityLog]:
        keyword = action_keyword.lower()
        return [log for log in self.logs if keyword in log.action.lower()]

    def save_changes(self):
        self.repo.save([log.to_dict() for log in self.logs])

    def clear_logs(self):
        """Изчистване на историята."""
        self.logs = []
        self.save_changes()