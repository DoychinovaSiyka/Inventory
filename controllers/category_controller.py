from typing import List, Optional
from models.category import Category
from validators.category_validator import CategoryValidator
from filters.category_filters import filter_categories
from analytics.category_analytics import build_category_tree


class CategoryController:
    """Контролерът управлява категориите и гарантира йерархичната цялост."""

    def __init__(self, repo, activity_log_controller=None):
        self.repo = repo
        self.activity_log = activity_log_controller

        # Зареждане на категориите
        raw_data = self.repo.load() or []
        self.categories: List[Category] = [Category.from_dict(c) for c in raw_data]

    def _log(self, user_id: str, action: str, message: str):
        if self.activity_log:
            self.activity_log.log_action(user_id, action, message)

    def _save_changes(self) -> None:
        self.repo.save([c.to_dict() for c in self.categories])

    def add(self, category_data: dict, user_id: str) -> Category:
        """Добавяне на категория с проверка за родител и цикли."""
        name = category_data.get("name", "").strip()
        description = category_data.get("description", "").strip()
        parent_input = category_data.get("parent_id")

        # ОПРАВКА: Намиране на точния родител
        parent_id = None
        if parent_input:
            parent_cat = self.get_by_id(parent_input)
            if parent_cat:
                parent_id = parent_cat.category_id
            else:
                raise ValueError(f"Родителска категория с ID {parent_input} не съществува.")

        CategoryValidator.validate_name(name)
        CategoryValidator.validate_unique(name, self.categories)
        CategoryValidator.validate_description(description)
        CategoryValidator.validate_parent_exists(parent_id, self.categories)
        CategoryValidator.validate_no_cycle(None, parent_id, self.categories)

        category = Category(category_id=None, name=name, description=description, parent_id=parent_id)
        self.categories.append(category)
        self._save_changes()

        self._log(user_id, "ADD_CATEGORY", f"Добавена категория: {name}")
        return category

    def update_name(self, category_id: str, new_name: str, user_id: str) -> bool:
        category = CategoryValidator.validate_exists(category_id, self)
        new_name = new_name.strip()
        CategoryValidator.validate_update_name(new_name)

        if category.name == new_name:
            return True

        # Проверка за уникалност, изключвайки текущата категория
        CategoryValidator.validate_unique(new_name,
                                          [c for c in self.categories if c.category_id != category.category_id])

        old_name = category.name
        category.name = new_name
        category.update_modified()
        self._save_changes()
        self._log(user_id, "EDIT_CATEGORY", f"Преименувана категория: {old_name} -> {new_name}")
        return True

    def remove(self, category_id: str, user_id: str, product_controller=None) -> bool:
        """Изтриване само ако категорията е празна (няма продукти и подкатегории)."""
        category = self.get_by_id(category_id)
        if not category:
            return False

        # Валидацията проверява дали има продукти или деца
        products = product_controller.get_all() if product_controller else []
        CategoryValidator.validate_can_delete(category.category_id, self.categories, products)

        self.categories = [c for c in self.categories if c.category_id != category.category_id]
        self._save_changes()
        self._log(user_id, "DELETE_CATEGORY", f"Изтрита категория: {category.name}")
        return True

    def get_by_id(self, category_id: str) -> Optional[Category]:
        """Интелигентно търсене: първо точно съвпадение, после по префикс."""
        target_id = str(category_id).strip()
        if not target_id:
            return None

        # 1. Точно съвпадение (защита от парадокси)
        for c in self.categories:
            if c.category_id == target_id:
                return c

        # 2. Кратко ID (за удобство)
        for c in self.categories:
            if c.category_id.startswith(target_id):
                return c
        return None

    def get_all(self) -> List[Category]:
        return self.categories

    def get_subcategories(self, parent_id: str) -> List[Category]:
        """Връща списък с преки наследници."""
        parent = self.get_by_id(parent_id)
        pid = parent.category_id if parent else None
        return [c for c in self.categories if c.parent_id == pid]

    def get_category_tree(self) -> List[dict]:
        """Генерира дървовидна структура за визуализация."""
        return build_category_tree(self.categories)

    def search(self, keyword: str) -> List[Category]:
        """Търсене по име или описание."""
        if not keyword or len(keyword.strip()) < 2:
            return []
        return filter_categories(self.categories, keyword.strip())