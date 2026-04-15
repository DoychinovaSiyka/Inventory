from datetime import datetime
from validators.category_validator import CategoryValidator


class Category:
    def __init__(self, category_id, name, description="", parent_id=None, created=None, modified=None):
        #  UUID - получавам от Контролера. Моделът НЕ ГЕНЕРИРА ID и ДАТИ – Контролерът ги подава
        self.category_id = str(category_id) if category_id else None
        self.name = name
        self.description = description
        self.parent_id = str(parent_id) if parent_id else None
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.created = created or now
        self.modified = modified or now
        CategoryValidator.validate_name(self.name)
        CategoryValidator.validate_description(self.description)


    def update_modified(self):
        self.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        """Сериализация за запис в JSON."""
        return {"category_id": self.category_id, "name": self.name, "description": self.description,
            "parent_id": self.parent_id, "created": self.created, "modified": self.modified}

    @staticmethod
    def from_dict(data):
        """Десериализация при зареждане от JSON."""
        if not data:
            return None
        return Category(category_id=data.get("category_id"), name=data.get("name"),
                        description=data.get("description", ""),
                        parent_id=data.get("parent_id"),
                        created=data.get("created"),
                        modified=data.get("modified"))

    def __str__(self):
        parent_info = f" (подкатегория на {self.parent_id})" if self.parent_id else ""
        return f"Категория: {self.name}{parent_info}"
