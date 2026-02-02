from storage.json_repository import Repository
from models.category import Category
from validators.category_validator import CategoryValidator
from datetime import datetime


class CategoryController:
    def __init__(self, repo: Repository):
        self.repo = repo
        self.categories = [Category.from_dict(c) for c in self.repo.load()]

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------
    def add(self, name, description=""):
        CategoryValidator.validate_name(name)
        CategoryValidator.validate_unique(name, self.categories)
        CategoryValidator.validate_description(description)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        category = Category(
            name=name,
            description=description,
            created=now,
            modified=now
        )

        self.categories.append(category)
        self._save()
        return category

    # ---------------------------------------------------------
    # READ
    # ---------------------------------------------------------
    def get_all(self):
        return self.categories

    def get_by_id(self, category_id):
        return next((c for c in self.categories if c.category_id == category_id), None)

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------
    def update_name(self, category_id, new_name):
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError("Категорията не е намерена.")

        CategoryValidator.validate_update_name(new_name)
        CategoryValidator.validate_unique(new_name, self.categories)

        category.name = new_name
        category.update_modified()
        self._save()
        return True

    def update_description(self, category_id, new_description):
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError("Категорията не е намерена.")

        CategoryValidator.validate_description(new_description)

        category.description = new_description
        category.update_modified()
        self._save()
        return True

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------
    def remove(self, category_id):
        original_len = len(self.categories)
        self.categories = [c for c in self.categories if c.category_id != category_id]

        if len(self.categories) < original_len:
            self._save()
            return True
        return False

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------
    def search(self, keyword):
        keyword = keyword.lower()
        return [
            c for c in self.categories
            if keyword in c.name.lower()
               or keyword in (c.description or "").lower()
        ]

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------
    def _save(self):
        self.repo.save([c.to_dict() for c in self.categories])
