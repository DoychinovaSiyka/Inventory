from typing import List, Optional
from models.category import Category
from validators.category_validator import CategoryValidator
from controllers.abstract_controller import AbstractController


class CategoryController(AbstractController):

    def __init__(self, repo):
        super().__init__(repo)
        self.categories: List[Category] = self.load()

    def from_dict(self, data):
        return Category.from_dict(data)

    def to_dict(self, obj):
        return obj.to_dict()

    def _save(self):
        self.save(self.categories)

    def get_all(self) -> List[Category]:
        return self.categories

    def get_by_id(self, user_input: str) -> Optional[Category]:
        target = str(user_input or "").strip().lower()
        for c in self.categories:
            full_id = str(c.category_id).lower()
            if full_id.startswith(target) or target == full_id:
                return c
        return None

    # -----------------------------
    # ADD
    # -----------------------------
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

    # -----------------------------
    # UPDATE
    # -----------------------------
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

    # -----------------------------
    # REMOVE (без зависимост от product_controller)
    # -----------------------------
    def remove(self, category_id: str) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            return False

        # проста MVC проверка: дали категорията има деца
        for c in self.categories:
            if c.parent_id == category.category_id:
                raise ValueError("Категорията има подкатегории и не може да бъде изтрита.")

        self.categories = [c for c in self.categories if c.category_id != category.category_id]
        self._save()
        return True

    # -----------------------------
    # TREE VIEW
    # -----------------------------
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

    # -----------------------------
    # VALIDATION
    # -----------------------------
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
