from abc import ABC, abstractmethod


class Repository(ABC):
    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def save(self, data):
        pass


# Repository е абстрактен клас, който определя общ интерфейс за работа с данни.
# Всеки конкретен репозиторий (JSON, CSV, база данни) трябва да имплементира load() и save().
# Това позволява контролерите да работят с абстракция, без да зависят от конкретния тип хранилище.
