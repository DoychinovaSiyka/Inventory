from typing import List, Optional
from models.category import Category
from validators.category_validator import CategoryValidator
from filters.category_filters import filter_categories
from filters.category_analytics import build_category_tree, get_category_stats


class CategoryController:
    """Управлява категориите и гарантира йерархичната цялост."""

    def __init__(self, repo):
        self.repo = repo
        self.categories: List[Category] = self._load()

    def _load(self) -> List[Category]:
        raw = self.repo.load() or []
        return [Category.from_dict(c) for c in raw]

    def _save(self) -> None:
        self.repo.save([c.to_dict() for c in self.categories])

    def get_all(self) -> List[Category]:
        return self.categories

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
        self._save()
        return category

    def update(self, category_id: str, updates: dict) -> bool:
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

        self._save()
        return True

    def remove(self, category_id: str, user_id: str, product_controller) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            return False

        products = product_controller.get_all() if product_controller else []
        CategoryValidator.validate_can_delete(category.category_id, self.categories, products)

        self.categories = [c for c in self.categories if c.category_id != category.category_id]
        self._save()
        return True



    def get_by_id(self, user_input: str) -> Optional[Category]:
        target = str(user_input or "").strip().lower()
        for c in self.categories:
            full_id = str(c.category_id).lower()
            if full_id.startswith(target) or target == full_id:
                return c
        return None



    def get_all_hierarchical_ids(self, parent_short_id: str) -> list:
        parent_cat = self.get_by_id(parent_short_id)
        if not parent_cat:
            return []

        result = [parent_cat.category_id]
        for cat in self.categories:
            if cat.parent_id == parent_cat.category_id:
                result.extend(self.get_all_hierarchical_ids(cat.category_id[:8]))

        return list(set(result))

    def search(self, keyword: str) -> List[dict]:
        cleaned = (keyword or "").strip().lower()
        if not cleaned:
            return []

        results = []
        for c in self.categories:
            full_id = str(c.category_id).lower()
            if cleaned in c.name.lower() or full_id.startswith(cleaned):
                parent_obj = self.get_by_id(c.parent_id) if c.parent_id else None
                results.append({"id": c.category_id,  "name": c.name,
                                "description": c.description, "parent": parent_obj.name if parent_obj else None})
        return results



    def get_stats(self, product_controller) -> dict:
        products = product_controller.get_all() if product_controller else []
        raw = get_category_stats(self.categories, products)

        return {"total_categories": raw.get("total_categories", 0),
                "categories": [{"id": c["id"][:8], "name": c["name"], "product_count": c["product_count"]}
                               for c in raw.get("categories", [])]}



    def get_visual_tree(self) -> List[dict]:
        def build_recursive_list(parent_id=None, level=0):
            result = []
            children = [c for c in self.categories if c.parent_id == parent_id]
            children.sort(key=lambda x: x.name.lower())

            for child in children:
                result.append({"category": child, "level": level})
                result.extend(build_recursive_list(child.category_id, level + 1))
            return result

        return build_recursive_list()



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