
from storage.json_repository import Repository  # ако имаш абстрактен интерфейс
from models.category import Category

class CategoryController():
    def __init__(self,repo:Repository): #  Това прави контролера независим от конкретната имплементация и съвместим с DIP.
        self.repo = repo # Инициализираме хранилището, което ще работи с JSON файлове
        self.categories = [Category.from_dict(c) for c in self.repo.load()] # зареждаме категориите от файла и ги преобразуваме в обект от тип Category

    def add(self,name):
        category = Category(name)
        self.categories.append(category)
        self._save()
        return category

    def remove(self,category_id):
        original_len = len(self.categories)
        self.categories = [c for c in self.categories if c.category_id!= category_id]
        if len(self.categories) < original_len:
            self._save()
            return True
        return False

    def update_name(self, category_id, new_name):
        for c in self.categories:
            if c.category_id == category_id:
                c.name = new_name
                self._save()
                return True
        return False

    def get_all(self):
        return self.categories

    def _save(self):
        self.repo.save([c.to_dict() for c in self.categories])


# Конторолера е за изтриване  добавяне търсене






