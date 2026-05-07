from typing import List, Optional
from models.category import Category
from validators.category_validator import CategoryValidator
from filters.category_filters import filter_categories
from analytics.category_analytics import build_category_tree


class CategoryController:
    """Контролерът управлява категориите и координира CRUD операциите."""
    def __init__(self, repo, activity_log_controller=None):
        self.repo = repo
        self.activity_log = activity_log_controller

        # Зареждане на категориите от JSON файла
        raw_data = self.repo.load() or []
        self.categories: List[Category] = [Category.from_dict(c) for c in raw_data]

    def _log(self, user_id: str, action: str, message: str):
        if self.activity_log:
            self.activity_log.log_action(user_id, action, message)

    def _save_changes(self) -> None:
        self.repo.save([c.to_dict() for c in self.categories])

    def add(self, category_data: dict, user_id: str) -> Category:
        name = category_data.get("name")
        description = category_data.get("description", "")
        parent_id = category_data.get("parent_id")
        if parent_id:
            parent_cat = self.get_by_id(parent_id)
            parent_id = parent_cat.category_id if parent_cat else parent_id

        CategoryValidator.validate_name(name)
        CategoryValidator.validate_unique(name, self.categories)
        CategoryValidator.validate_description(description)
        CategoryValidator.validate_parent_exists(parent_id, self.categories)
        CategoryValidator.validate_no_cycle(None, parent_id, self.categories)

        category = Category(category_id=None, name=name, description=description, parent_id=parent_id)
        self.categories.append(category)
        self._save_changes()

        short_id = category.category_id[:8]
        self._log(user_id, "ADD_CATEGORY", f"Добавена категория: {name} (ID: {short_id})")
        return category

    def update_name(self, category_id: str, new_name: str, user_id: str) -> bool:
        category = CategoryValidator.validate_exists(category_id, self)
        CategoryValidator.validate_update_name(new_name)

        if category.name == new_name:
            return True

        CategoryValidator.validate_unique(new_name,
                                          [c for c in self.categories if c.category_id != category.category_id])
        category.name = new_name
        category.update_modified()
        self._save_changes()
        self._log(user_id, "EDIT_CATEGORY", f"Име на кат. {category.category_id[:8]} променено на {new_name}")
        return True

    def remove(self, category_id: str, user_id: str, product_controller=None) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            return False

        products = product_controller.get_all() if product_controller else []
        CategoryValidator.validate_can_delete(category.category_id, self.categories, products)

        before = len(self.categories)
        self.categories = [c for c in self.categories if c.category_id != category.category_id]

        if len(self.categories) < before:
            self._save_changes()
            self._log(user_id, "DELETE_CATEGORY", f"Категория {category.category_id[:8]} е изтрита")
            return True
        return False

    def get_by_id(self, category_id: str) -> Optional[Category]:
        """Намиране на обект както по пълно ID, така и по първите 8 символа, въведени от потребителя."""
        target_id = str(category_id).strip()
        if not target_id:
            return None

        for c in self.categories:
            if c.category_id.startswith(target_id):
                return c
        return None


    def get_all(self) -> List[Category]:
        return self.categories

    def get_subcategories(self, parent_id: str) -> List[Category]:
        parent = self.get_by_id(parent_id)
        pid = parent.category_id if parent else parent_id
        return [c for c in self.categories if c.parent_id == pid]

    def get_category_tree(self) -> List[dict]:
        return build_category_tree(self.categories)

    def search(self, keyword: str) -> List[Category]:
        if not keyword or len(keyword.strip()) < 3:
            return []
        return filter_categories(self.categories, keyword)