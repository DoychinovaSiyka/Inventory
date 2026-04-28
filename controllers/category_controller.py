import uuid
from typing import Optional, List
from storage.json_repository import Repository
from models.category import Category
from validators.category_validator import CategoryValidator
from filters.category_filters import filter_categories
from analytics.category_analytics import build_category_tree


class CategoryController:
    """Контролерът управлява категориите и координира работата между модела,
    валидаторите и хранилището, като изпълнява основните CRUD операции."""
    def __init__(self, repo: Repository, activity_log_controller=None):
        self.repo = repo
        self.activity_log = activity_log_controller
        self.categories: List[Category] = []
        self._load_categories()

    # Зареждам категориите от JSON файла
    def _load_categories(self):
        raw_data = self.repo.load() or []
        self.categories = [Category.from_dict(c) for c in raw_data]

    # Добавям запис в логовете, ако има лог контролер
    def _log(self, user_id: str, action: str, message: str):
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)

    # CREATE
    def add(self, category_data: dict, user_id: str) -> Category:
        name = category_data.get("name")
        description = category_data.get("description", "")
        parent_id = category_data.get("parent_id")

        CategoryValidator.validate_name(name)
        CategoryValidator.validate_unique(name, self.categories)
        CategoryValidator.validate_description(description)
        CategoryValidator.validate_parent_exists(parent_id, self.categories)
        CategoryValidator.validate_no_cycle(None, parent_id, self.categories)

        category = Category(category_id=str(uuid.uuid4()), name=name, description=description, parent_id=parent_id)
        self.categories.append(category)
        self._save_changes()
        self._log(user_id, "ADD_CATEGORY", f"Добавена категория: {name}")

        return category


    def update_name(self, category_id: str, new_name: str, user_id: str) -> bool:
        category = CategoryValidator.validate_exists(category_id, self)
        CategoryValidator.validate_update_name(new_name)

        if category.name == new_name:
            return True
        CategoryValidator.validate_unique(new_name, [c for c in self.categories if c.category_id != category_id])

        category.name = new_name
        category.update_modified()
        self._save_changes()
        self._log(user_id, "EDIT_CATEGORY", f"Име променено на {new_name}")
        return True

    # UPDATE – промяна на описание
    def update_description(self, category_id: str, new_description: str, user_id: str) -> bool:
        category = CategoryValidator.validate_exists(category_id, self)
        CategoryValidator.validate_description(new_description)

        if category.description == new_description:
            return True

        category.description = new_description
        category.update_modified()
        self._save_changes()
        self._log(user_id, "EDIT_CATEGORY", "Описание обновено")
        return True

    # UPDATE – промяна на родител
    def update_parent(self, category_id: str, parent_id: Optional[str], user_id: str) -> bool:
        category = CategoryValidator.validate_exists(category_id, self)

        if category.parent_id == parent_id:
            return True

        CategoryValidator.validate_parent_exists(parent_id, self.categories)
        CategoryValidator.validate_parent_id(parent_id, category_id)
        CategoryValidator.validate_no_cycle(category_id, parent_id, self.categories)

        category.parent_id = parent_id
        category.update_modified()
        self._save_changes()
        self._log(user_id, "EDIT_CATEGORY", "Родител променен")
        return True

    # DELETE
    def remove(self, category_id: str, user_id: str, product_controller=None) -> bool:
        CategoryValidator.validate_exists(category_id, self)

        products = product_controller.get_all() if product_controller else []
        CategoryValidator.validate_can_delete(category_id, self.categories, products)

        before = len(self.categories)
        self.categories = [c for c in self.categories if c.category_id != category_id]

        deleted = len(self.categories) < before
        if deleted:
            self._save_changes()
            self._log(user_id, "DELETE_CATEGORY", f"Категория {category_id} изтрита")

        return deleted

    # Публични методи за достъп
    def get_all(self) -> List[Category]:
        return self.categories

    def get_by_id(self, category_id: str) -> Optional[Category]:
        for c in self.categories:
            if c.category_id == category_id:
                return c
        return None

    def get_subcategories(self, parent_id: str) -> List[Category]:
        return [c for c in self.categories if c.parent_id == parent_id]


    def get_category_tree(self) -> List[dict]:
        return build_category_tree(self.categories)

    # Търсене
    def search(self, keyword: str) -> List[Category]:
        if not keyword or len(keyword.strip()) < 3:
            return []
        return filter_categories(self.categories, keyword)

    # Запис
    def _save_changes(self) -> None:
        self.repo.save([c.to_dict() for c in self.categories])
