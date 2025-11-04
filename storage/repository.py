from abc import  ABC,abstractmethod

class Repository(ABC):
    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def save(self,data):
        pass



