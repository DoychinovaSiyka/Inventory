import uuid

class Category:
    def __init__(self,name,category_id = None):
        self.name = name

        self.category_id = category_id or str(uuid.uuid4())

    @staticmethod
    def from_dict(data): # десериализация от текст превръщам в обект
        return Category(
            name = data["name"],
            category_id=data["category_id"],
        )

    def to_dict(self): # сериализация от обект в текст
        return {
            'name': self.name,

            'category_id': self.category_id
        }


# Независимост — статичният
# метод не зависи от инстанция на класа и може да се
# извика директно за създаване на обект от данни.
