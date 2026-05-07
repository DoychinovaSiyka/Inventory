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

        if parent_id:
            self.parent_id = str(parent_id)
        else:
            self.parent_id = None

        now = Category.now()

        if created:
            self.created = created
        else:
            self.created = now

        if modified:
            self.modified = modified
        else:
            self.modified = now

        CategoryValidator.validate_name(self.name)
        CategoryValidator.validate_description(self.description)

    @staticmethod
    def now():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def update_modified(self):
        self.modified = Category.now()

    def to_dict(self):
        return {"category_id": self.category_id, "name": self.name, "description": self.description,
                "parent_id": self.parent_id, "created": self.created, "modified": self.modified}

    @staticmethod
    def from_dict(data):
        if not data:
            return None

        return Category(category_id=data.get("category_id"), name=data.get("name"),
                        description=data.get("description", ""), parent_id=data.get("parent_id"),
                        created=data.get("created"), modified=data.get("modified"))

    def __str__(self):
        short_id = self.category_id[:8]

        if self.parent_id:
            parent_info = f" (Подкатегория на: {self.parent_id[:8]})"
        else:
            parent_info = ""

        return f"Категория: {self.name} [ID: {short_id}]{parent_info}"
