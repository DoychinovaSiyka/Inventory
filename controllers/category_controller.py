from typing import List, Optional
from models.category import Category
from validators.category_validator import CategoryValidator
from filters.category_filters import filter_categories
from filters.category_analytics import build_category_tree, get_category_stats


class CategoryController:
    """Управлява категориите и гарантира йерархичната цялост."""
    def __init__(self, repo, activity_log_controller=None):
        self.repo = repo
        raw_data = self.repo.load() or []
        self.categories: List[Category] = [Category.from_dict(c) for c in raw_data]


    def get_all(self) -> List[Category]:
        return self.categories

    def _save_changes(self) -> None:
        """Записва промените в репозиторито."""
        self.repo.save([c.to_dict() for c in self.categories])


    def add(self, category_data: dict, user_id: str) -> Category:
        name = CategoryValidator.validate_name(category_data.get("name", ""))
        description = CategoryValidator.validate_description(category_data.get("description", ""))

        CategoryValidator.validate_unique(name, self.categories)

        parent_id = None
        parent_input = category_data.get("parent_id")
        if parent_input:
            parent = self.get_by_id(parent_input)
            if not parent:
                raise ValueError(f"Родителска категория '{parent_input}' не съществува.")
            parent_id = parent.category_id


        CategoryValidator.validate_no_cycle(None, parent_id, self.categories)

        category = Category(category_id=None, name=name, description=description, parent_id=parent_id)
        self.categories.append(category)
        self._save_changes()
        return category



    def update(self, category_id: str, updates: dict) -> bool:
        """Обновява категория с валидация само на променените полета."""
        category = self.get_by_id(category_id)
        if not category:
            return False


        new_name = updates.get("name", category.name).strip()
        new_desc = updates.get("description", category.description).strip()

        new_parent_input = updates.get("parent_id")
        if new_parent_input:
            parent_obj = self.get_by_id(new_parent_input)
            new_parent_id = parent_obj.category_id if parent_obj else None
        else:
            new_parent_id = category.parent_id


        if new_name != category.name:
            CategoryValidator.validate_name(new_name)
            CategoryValidator.validate_unique(new_name, self.categories, exclude_id=category.category_id)

        if new_desc != category.description:
            CategoryValidator.validate_description(new_desc)

        if new_parent_id != category.parent_id:
            CategoryValidator.validate_no_cycle(category.category_id, new_parent_id, self.categories)


        category.name = new_name
        category.description = new_desc
        category.parent_id = new_parent_id
        category.update_modified()
        self._save_changes()
        return True

    def get_by_id(self, user_input: str) -> Optional[Category]:
        target = str(user_input or "").strip()
        if len(target) != 8:
            return None

        for c in self.categories:
            if c.category_id[:8] == target:
                return c
        return None

    def get_all_hierarchical_ids(self, parent_short_id: str) -> list:

        parent_cat = self.get_by_id(parent_short_id)
        if not parent_cat:
            return []

        result = [parent_cat.category_id]
        all_cats = self.get_all()
        for cat in all_cats:
            if cat.parent_id == parent_cat.category_id:
                result.extend(self.get_all_hierarchical_ids(cat.category_id[:8]))

        return list(set(result))

    def search(self, keyword: str) -> List[Category]:
        """Търсене по име или описание чрез филтър модула."""
        cleaned = (keyword or "").strip()
        if len(cleaned) < 3:
            return []
        return filter_categories(self.categories, cleaned)

    def get_stats(self, product_controller) -> dict:
        """Статистика за броя продукти във всяка категория."""
        if product_controller is not None:
            products = product_controller.get_all()
        else:
            products = []

        return get_category_stats(self.categories, products)

    def get_visual_tree(self) -> List[dict]:
        """Изгражда йерархичното дърво за визуализация."""
        return build_category_tree(self.categories)


    def remove(self, category_id: str, user_id: str, product_controller) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            return False

        if product_controller is not None:
            products = product_controller.get_all()
        else:
            products = []

        CategoryValidator.validate_can_delete(category.category_id, self.categories, products)
        self.categories = [c for c in self.categories if c.category_id != category.category_id]
        self._save_changes()
        return True

    def validate_field(self, field_type: str, value: str) -> Optional[str]:
        try:
            if field_type == "name":
                CategoryValidator.validate_name(value)

            elif field_type == "description":
                CategoryValidator.validate_description(value)

            elif field_type == "parent":
                if value and not self.get_by_id(value):
                    raise ValueError("Невалидна родителска категория.")

            return None
        except ValueError as e:
            return str(e)