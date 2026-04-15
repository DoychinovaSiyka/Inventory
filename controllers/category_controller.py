import uuid
from typing import Optional, List
from datetime import datetime
from storage.json_repository import Repository
from models.category import Category
from validators.category_validator import CategoryValidator
from filters.category_filters import filter_categories
from analytics.category_analytics import build_category_tree


class CategoryController:
    def __init__(self, repo: Repository, activity_log_controller=None):
        self.repo = repo
        self.activity_log = activity_log_controller
        self.categories: List[Category] = []
        # Зареждане на категориите от JSON файла - Контролерът нарежда зареждането
        self._load_categories()

    def _load_categories(self):
        raw_data = self.repo.load()
        self.categories = [Category.from_dict(c) for c in raw_data]

    def _log(self, user_id, action, message):
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)

    # CRUD операции
    def add(self, category_data: dict, user_id: str) -> Category:
        """Добавя нова категория или подкатегория."""
        name = category_data.get('name')
        description = category_data.get('description', "")
        parent_id = category_data.get('parent_id')


        CategoryValidator.validate_name(name)
        CategoryValidator.validate_unique(name, self.categories)
        CategoryValidator.validate_description(description)
        CategoryValidator.validate_parent_exists(parent_id, self.categories)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        category = Category(category_id=str(uuid.uuid4()), name=name, description=description,
                            parent_id=parent_id, created=now, modified=now)

        self.categories.append(category)
        self.save_changes()
        self._log(user_id, "ADD_CATEGORY", f"Успешно добавена категория: {name}")
        return category

    def update_name(self, category_id: str, new_name: str, user_id: str) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError("Категорията не е намерена.")

        CategoryValidator.validate_update_name(new_name)
        CategoryValidator.validate_unique(new_name, [c for c in self.categories if c.category_id != category_id])

        category.name = new_name
        category.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_CATEGORY", f"Името на категория {category_id} променено на {new_name}")
        return True

    def update_description(self, category_id: str, new_description: str, user_id: str) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError("Категорията не е намерена.")

        CategoryValidator.validate_description(new_description)
        category.description = new_description
        category.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_CATEGORY", f"Описанието на категория {category_id} е обновено")
        return True

    def update_parent(self, category_id: str, parent_id: Optional[str], user_id: str) -> bool:
        """Промяна на родителската категория."""
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError("Категорията не е намерена.")

        CategoryValidator.validate_parent_exists(parent_id, self.categories)
        CategoryValidator.validate_parent_id(parent_id, category_id)

        category.parent_id = parent_id
        category.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_CATEGORY", f"Родителят на категория {category_id} е променен")
        return True

    def remove(self, category_id: str, user_id: str, product_controller=None) -> bool:
        CategoryValidator.validate_can_delete(category_id, self.categories, product_controller)
        original_len = len(self.categories)
        self.categories = [c for c in self.categories if str(c.category_id) != str(category_id)]

        if len(self.categories) < original_len:
            self.save_changes()
            self._log(user_id, "DELETE_CATEGORY", f"Изтрита категория ID {category_id}")
            return True
        return False

    # Методи за достъп
    def get_all(self) -> List[Category]:
        return self.categories

    def get_by_id(self, category_id: str) -> Optional[Category]:
        return next((c for c in self.categories if str(c.category_id) == str(category_id)), None)

    def get_subcategories(self, parent_id: str) -> List[Category]:
        return [c for c in self.categories if str(c.parent_id) == str(parent_id)]

    # Контролерът  не строи дървото - вика
    def get_category_tree(self) -> List[dict]:
        """Изграждане на йерархия за менюто чрез външна логика."""
        return build_category_tree(self.categories)

    def search(self, keyword: str) -> List[Category]:
        """Търсене по име или описание чрез външен филтър."""
        return filter_categories(self.categories, keyword)

    def save_changes(self) -> None:
        # Записване на категориите обратно в JSON файла
        self.repo.save([c.to_dict() for c in self.categories])
