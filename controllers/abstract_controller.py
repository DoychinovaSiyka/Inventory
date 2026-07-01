from abc import ABC, abstractmethod

class AbstractController(ABC):
    """Базов учебен MVC контролер – без enterprise нотки."""

    def __init__(self, repo):
        self.repo = repo

    @abstractmethod
    def from_dict(self, data):
        pass

    @abstractmethod
    def to_dict(self, obj):
        pass

    def load(self):
        raw = self.repo.load()
        if not raw:
            return []

        # Учебен MVC: работим само със списъци
        if isinstance(raw, list):
            return [self.from_dict(x) for x in raw]

        # Ако е речник – връщаме го както е (InventoryController го обработва)
        if isinstance(raw, dict):
            return {k: self.from_dict(v) for k, v in raw.items()}

        return self.from_dict(raw)

    def save(self, data):
        if isinstance(data, list):
            normalized = [self.to_dict(x) for x in data]
        elif isinstance(data, dict):
            normalized = {k: self.to_dict(v) for k, v in data.items()}
        else:
            normalized = self.to_dict(data)

        self.repo.save(normalized)
