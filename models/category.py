import uuid
from datetime import datetime





class Category:
    def __init__(self, category_id, name, description="", parent_id=None, created=None, modified=None):
        if category_id:
            self.category_id = str(category_id)
        else:
            self.category_id = str(uuid.uuid4())


        self.name = name
        self.description = description

        if parent_id:
            self.parent_id = str(parent_id)
        else:
            self.parent_id = None



        now_val = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if isinstance(created, str):
            self.created = created
        else:
            self.created = now_val

        if isinstance(modified, str):
            self.modified = modified
        else:
            self.modified = now_val





    def update_modified(self):
        self.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')




    def to_dict(self):
        return {"category_id": self.category_id, "name": self.name,
                "description": self.description, "parent_id": self.parent_id,
                "created": self.created, "modified": self.modified}



    @staticmethod
    def from_dict(data):
        if not data:
            return None

        return Category(category_id=data.get("category_id"), name=data.get("name"),
                        description=data.get("description", ""), parent_id=data.get("parent_id"),
                        created=data.get("created"), modified=data.get("modified"))




    def __str__(self):
        short_id = self.category_id[:8]
        parent_info = f" (Подкатегория на: {self.parent_id[:8]})" if self.parent_id else ""
        return f"Категория: {self.name} [ID: {short_id}]{parent_info}"
