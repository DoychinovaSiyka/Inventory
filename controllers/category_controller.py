from typing import List, Optional
from models.category import Category
from validators.category_validator import CategoryValidator
from filters.category_filters import filter_categories, get_all_children_objects, get_all_children_ids
from analytics.category_analytics import build_category_tree, get_category_stats


class CategoryController:
    """Управлява категориите и гарантира йерархичната цялост."""

    def __init__(self, repo, activity_log_controller=None):
        self.repo = repo
        raw_data = self.repo.load() or []
        self.categories: List[Category] = [Category.from_dict(c) for c in raw_data]


    def get_all(self) -> List[Category]:
        """Връща списък с всички категории (нужен за View-тата)."""
        return self.categories


    def _save_changes(self) -> None:
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

        CategoryValidator.validate_name(name)
        CategoryValidator.validate_unique(name, self.categories)
        CategoryValidator.validate_no_cycle(None, parent_id, self.categories)

        category = Category(category_id=None, name=name, description=description, parent_id=parent_id)
        self.categories.append(category)
        self._save_changes()
        return category

    def get_by_id(self, category_id: str) -> Optional[Category]:
        target = str(category_id or "").strip()
        if not target:
            return None

        for c in self.categories:
            if c.category_id == target:
                return c

        for c in self.categories:
            if c.category_id.startswith(target):
                return c
        return None

    def get_subcategories(self, parent_id: Optional[str]) -> List[Category]:
        """Връща само директните деца (ниво 1) на категорията."""
        # Ако не е подаден родител, търсим тези с parent_id = None
        if not parent_id:
            return [c for c in self.categories if c.parent_id is None]

        parent = self.get_by_id(parent_id)
        pid = parent.category_id if parent else None

        return [c for c in self.categories if c.parent_id == pid]

    def search(self, keyword: str) -> List[Category]:
        """Търсене чрез външния филтър модул."""
        cleaned = (keyword or "").strip()
        if len(cleaned) < 2:
            return []
        return filter_categories(self.categories, cleaned)

    def filter_by_parent(self, parent_id: str) -> List[Category]:
        """Връща всички наследници (обекти) надолу по дървото."""
        return get_all_children_objects(self.categories, parent_id)

    def get_all_hierarchical_ids(self, parent_id: str) -> List[str]:
        """Връща списък от всички ID-та в клон на дървото (за филтър на продукти)."""
        return get_all_children_ids(self.categories, parent_id)

    def get_stats(self, product_controller) -> dict:
        """ Връща речник от типа: {'Име на категория': брой продукти}."""
        products = product_controller.get_all() if product_controller else []
        return get_category_stats(self.categories, products)

    def get_visual_tree(self) -> List[dict]:
        """Връща дървото"""
        return build_category_tree(self.categories)

    def remove(self, category_id: str, user_id: str, product_controller=None) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            return False

        products = product_controller.get_all() if product_controller else []
        # дали има закачени продукти или подкатегории - преди изтриване
        CategoryValidator.validate_can_delete(category.category_id, self.categories, products)

        self.categories = [c for c in self.categories if c.category_id != category.category_id]
        self._save_changes()
        return True