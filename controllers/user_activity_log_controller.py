from typing import List, Optional
from models.user_activity_log import UserActivityLog


class UserActivityLogController:
    """Контролерът управлява лог записите на потребителската активност.
    Координира записването и зареждането от JSON хранилището."""

    def __init__(self, repo):
        self.repo = repo
        # Зареждаме съществуващите логове от репозиториума
        raw_data = self.repo.load() or []
        self.logs: List[UserActivityLog] = [UserActivityLog.from_dict(l) for l in raw_data]

    # CREATE - Добавяне на нов лог
    def add_log(self, user_id, action, details=""):
        """ Създава нов лог запис. Вече не генерираме UUID и дати тук - моделът UserActivityLog. """
        new_log = UserActivityLog(user_id=user_id, action=action, details=details)
        self.logs.append(new_log)
        self.save_changes()
        return new_log

    # READ - Получаване на всички логове
    def get_all(self) -> List[UserActivityLog]:
        """Връща пълната история на действията."""
        return self.logs

    # READ - Филтриране по потребител
    def get_by_user(self, user_id: str) -> List[UserActivityLog]:
        """Връща всички действия на конкретен потребител."""
        uid = str(user_id)
        return [log for log in self.logs if log.user_id == uid]

    # READ - Търсене по действие
    def search_by_action(self, action_keyword: str) -> List[UserActivityLog]:
        """Търси логове по ключова дума в действието."""
        keyword = action_keyword.lower()
        return [log for log in self.logs if keyword in log.action.lower()]

    def save_changes(self):
        """Записва всички лог записи обратно в JSON файла."""
        self.repo.save([log.to_dict() for log in self.logs])

    # Изчистване на логове - полезно при администрация
    def clear_logs(self):
        """Изтрива всички записи от историята."""
        self.logs = []
        self.save_changes()



# UserActivityLogController е единственият контролер, който не използва dependency injection.
# Това е умишлено, защото той винаги работи само с един конкретен лог файл и е
# напълно самостоятелен. Всички останали контролери получават JSONRepository отвън,
# което е по‑професионално и следва SOLID принципите.
