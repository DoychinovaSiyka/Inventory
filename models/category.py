import uuid
from datetime import datetime
from validators.category_validator import CategoryValidator

class Category:
    def __init__(self,name,description = "",category_id = None,created = None,modified = None):
        self.name = name
        self.category_id = category_id or str(uuid.uuid4())
        self.description = description
        self.created = created if created else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.modified = modified if modified else  datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        CategoryValidator.validate_name(name)
        self.validate()

    def validate(self):
        CategoryValidator.validate_name(self.name)

    def update_modified(self):
        self.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self): # сериализация от обект в текст
        return {
            'category_id':self.category_id,
            'name': self.name,
            'description': self.description,
            'created':self.created,
            'modified':self.modified,
        }

    @staticmethod
    def from_dict(data): # десериализация от текст превръщам в обект
        return Category(

            name = data.get("name"),
            description = data.get("description"),
            category_id=data.get("category_id"),
            created = data.get("created"),
            modified = data.get("modified"))



# Независимост — статичният
# метод не зависи от инстанция на класа и може да се
# извика директно за създаване на обект от данни.
