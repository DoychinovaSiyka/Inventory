from typing import List, Optional
from models.category import Category
from validators.category_validator import CategoryValidator
# Импорти на логиката
from filters.category_filters import (
    filter_categories,
    filter_by_parent as filter_logic,
    get_all_children_ids
)
from analytics.category_analytics import build_category_tree


class CategoryController:
    """Контролерът управлява категориите и гарантира йерархичната цялост."""

    def __init__(self, repo, activity_log_controller=None):
        self.repo = repo
        raw_data = self.repo.load() or []
        self.categories: List[Category] = [Category.from_dict(c) for c in raw_data]

    def _save_changes(self) -> None:
        """Записва промените в базата."""
        self.repo.save([c.to_dict() for c in self.categories])

    def add(self, category_data: dict, user_id: str) -> Category:
        name = category_data.get("name", "").strip()
        description = category_data.get("description", "").strip()
        parent_input = category_data.get("parent_id")

        parent_id = None
        if parent_input:
            parent = self.get_by_id(parent_input)
            if not parent:
                raise ValueError(f"Родителска категория {parent_input} не съществува.")
            parent_id = parent.category_id

        # Валидации
        CategoryValidator.validate_name(name)
        CategoryValidator.validate_unique(name, self.categories)
        CategoryValidator.validate_description(description)
        CategoryValidator.validate_no_cycle(None, parent_id, self.categories)

        category = Category(category_id=None, name=name, description=description, parent_id=parent_id)
        self.categories.append(category)
        self._save_changes()
        return category

    def update_parent(self, category_id: str, new_parent_id: str, user_id: str) -> bool:
        category = CategoryValidator.validate_exists(category_id, self.categories)

        if not new_parent_id:
            category.parent_id = None
        else:
            new_parent = self.get_by_id(new_parent_id)
            if not new_parent:
                raise ValueError("Новият родител не съществува.")

            CategoryValidator.validate_no_cycle(category.category_id, new_parent.category_id, self.categories)
            category.parent_id = new_parent.category_id

        category.update_modified()
        self._save_changes()
        return True

    def get_by_id(self, category_id: str) -> Optional[Category]:
        target = str(category_id or "").strip()
        if not target:
            return None

        # Първо търсим точно съвпадение
        for c in self.categories:
            if c.category_id == target:
                return c
        # Второ търсим по начало на ID (за удобство в конзолата)
        for c in self.categories:
            if c.category_id.startswith(target):
                return c
        return None

    def filter_by_parent(self, parent_id: str) -> List[Category]:
        """Използва рекурсивната логика от филтрите за връщане на обекти."""
        return filter_logic(self.categories, parent_id)

    def get_all_hierarchical_ids(self, parent_id: str) -> List[str]:
        """Връща списък от всички ID-та в дървото (за филтър на продукти)."""
        return get_all_children_ids(self.categories, parent_id)

    def search(self, keyword: str) -> List[Category]:
        """Търсене в име и описание."""
        cleaned = (keyword or "").strip()
        if len(cleaned) < 2:
            return []
        return filter_categories(self.categories, cleaned)

    def get_subcategories(self, parent_id: Optional[str]) -> List[Category]:
        """Връща само директните деца на дадена категория."""
        pid = None
        if parent_id:
            parent = self.get_by_id(parent_id)
            pid = parent.category_id if parent else None

        return [c for c in self.categories if c.parent_id == pid]

    def get_all(self) -> List[Category]:
        return self.categories

    def remove(self, category_id: str, user_id: str, product_controller=None) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            return False

        products = product_controller.get_all() if product_controller else []
        CategoryValidator.validate_can_delete(category.category_id, self.categories, products)

        self.categories = [c for c in self.categories if c.category_id != category.category_id]
        self._save_changes()
        return True