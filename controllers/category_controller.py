from storage.json_repository import Repository
from models.category import Category
from validators.category_validator import CategoryValidator


class CategoryController():
    def __init__(self, repo: Repository):
        self.repo = repo
        self.categories = [Category.from_dict(c) for c in self.repo.load()]


    def add(self, name,description = ""):
        CategoryValidator.validate_name(name)
        CategoryValidator.validate_unique(name, self.categories)
        CategoryValidator.validate_description(description)

        category = Category(name = name,description = description)
        self.categories.append(category)
        self._save()
        return category

    def remove(self, category_id):
        original_len = len(self.categories)
        self.categories = [c for c in self.categories if c.category_id != category_id]

        if len(self.categories) < original_len:
            self._save()
            return True
        return False

    def update_name(self, category_id, new_name):
        CategoryValidator.validate_update_name(new_name)
        CategoryValidator.validate_unique(new_name,self.categories)

        for c in self.categories:
            if c.category_id == category_id:
                c.name = new_name
                self._save()
                return True
        return False

    def update_description(self, category_id, new_description):
        CategoryValidator.validate_description(new_description)

        for c in self.categories:
            if c.category_id == category_id:
                c.description = new_description
                c.update_modified()
                self._save()
                return True
        return False

    def get_all(self):
        return self.categories

    def get_by_id(self, category_id):
        for c in self.categories:
            if c.category_id == category_id:
                return c
        return False

    def _save(self):
        self.repo.save([c.to_dict() for c in self.categories])





