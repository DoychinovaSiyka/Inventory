import uuid
from datetime import datetime
from validators.category_validator import CategoryValidator
from typing import Optional


class Category:
    def __init__(self, name, description="", category_id=None, parent_id=None, created=None, modified=None):
        self.category_id = category_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.parent_id = parent_id
        self.created = created if created else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.modified = modified if modified else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        CategoryValidator.validate_name(self.name)
        CategoryValidator.validate_description(self.description)

    def update_modified(self):
        """Обновява датата на последна промяна."""
        self.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        """Сериализация: от обект към речник (за запис в JSON)."""
        return {
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'created': self.created,
            'modified': self.modified
        }

    @staticmethod
    def from_dict(data):
        """Десериализация: от речник към обект (при зареждане от JSON)."""
        return Category(category_id=data.get("category_id"), name=data.get("name"),
                        description=data.get("description"), parent_id=data.get("parent_id"),
                        created=data.get("created"), modified=data.get("modified"))
