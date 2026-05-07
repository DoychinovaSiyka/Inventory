import uuid
from datetime import datetime
from validators.category_validator import CategoryValidator


class Category:
    def __init__(self, category_id, name, description="", parent_id=None, created=None, modified=None):


        if not category_id:
            self.category_id = str(uuid.uuid4())
        else:
            self.category_id = str(category_id)

        self.name = name
        self.description = description
        self.parent_id = str(parent_id) if parent_id else None

        now = Category.now()
        self.created = created or now
        self.modified = modified or now

        CategoryValidator.validate_name(self.name)
        CategoryValidator.validate_description(self.description)

    @staticmethod
    def now():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def update_modified(self):
        """Обновяваме датата при промяна."""
        self.modified = Category.now()

    def to_dict(self):
        """Записваме в JSON ПЪЛНОТО ID (36 символа)."""
        return {
            "category_id": self.category_id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        return Category(
            category_id=data.get("category_id"),
            name=data.get("name"),
            description=data.get("description", ""),
            parent_id=data.get("parent_id"),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def __str__(self):
        short_id = self.category_id[:8]
        # Ако има родител, също му показваме само първите 8 символа
        parent_info = f" (Подкатегория на: {self.parent_id[:8]})" if self.parent_id else ""

        return f"Категория: {self.name} [ID: {short_id}]{parent_info}"