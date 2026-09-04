from abc import ABC, abstractmethod




class AbstractController(ABC):
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
        if raw is None:
            return []
        return [self.from_dict(item) for item in raw]



    def save(self, data):
        normalized = [self.to_dict(obj) for obj in data]
        self.repo.save(normalized)
