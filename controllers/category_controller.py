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

        raw_data = self.repo.load()
        if raw_data is None:
            raw_data = []

        self.categories: List[Category] = []
        for c in raw_data:
            self.categories.append(Category.from_dict(c))

    def _log(self, user_id: str, action: str, message: str):
        if self.activity_log:
            self.activity_log.log_action(user_id, action, message)

    def _save_changes(self) -> None:
        data = []
        for c in self.categories:
            data.append(c.to_dict())
        self.repo.save(data)

    def add(self, category_data: dict, user_id: str) -> Category:
        name = category_data.get("name", "")
        name = name.strip()

        description = category_data.get("description", "")
        description = description.strip()
        parent_input = category_data.get("parent_id")

        parent_id = None
        if parent_input:
            parent = self.get_by_id(parent_input)
            if parent is None:
                raise ValueError(f"Родителска категория с ID {parent_input} не съществува.")
            parent_id = parent.category_id

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
        category = CategoryValidator.validate_exists(category_id, self.categories)

        new_name = new_name.strip()
        CategoryValidator.validate_update_name(new_name)

        if category.name == new_name:
            return True

        other_categories = []
        for c in self.categories:
            if c.category_id != category.category_id:
                other_categories.append(c)

        CategoryValidator.validate_unique(new_name, other_categories)

        old_name = category.name
        category.name = new_name
        category.update_modified()

        self._save_changes()
        self._log(user_id, "EDIT_CATEGORY", f"Преименувана категория: {old_name} -> {new_name}")
        return True
    def update_description(self, category_id: str, new_description: str, user_id: str) -> bool:
        category = CategoryValidator.validate_exists(category_id, self.categories)

        if new_description is None:
            return True

        new_description = new_description.strip()
        CategoryValidator.validate_description(new_description)

        if category.description == new_description:
            return True

        old_desc = category.description
        category.description = new_description
        category.update_modified()
        self._save_changes()
        self._log(user_id, "EDIT_CATEGORY", f"Промяна на описание: '{old_desc}' -> '{new_description}'")
        return True

    def update_parent(self, category_id: str, new_parent_id: str, user_id: str) -> bool:
        category = CategoryValidator.validate_exists(category_id, self.categories)

        if new_parent_id is None:
            return True

        new_parent = self.get_by_id(new_parent_id)
        if new_parent is None:
            raise ValueError("Новият родител не съществува.")

        if new_parent.category_id == category.category_id:
            raise ValueError("Категория не може да бъде родител сама на себе си.")

        CategoryValidator.validate_parent_exists(new_parent.category_id, self.categories)
        CategoryValidator.validate_no_cycle(category.category_id, new_parent.category_id, self.categories)

        old_parent = category.parent_id
        category.parent_id = new_parent.category_id
        category.update_modified()

        self._save_changes()
        self._log(user_id, "EDIT_CATEGORY", f"Промяна на родител: {old_parent} -> {new_parent.category_id}")
        return True


    def remove(self, category_id: str, user_id: str, product_controller=None) -> bool:
        """Изтриване само ако категорията е празна (няма продукти и подкатегории)."""
        category = self.get_by_id(category_id)
        if category is None:
            self._log(user_id, "DELETE_CATEGORY_FAIL",
                      f"Несъществуваща категория: {category_id}")
            return False

        products = []
        if product_controller is not None:
            products = product_controller.get_all()

        CategoryValidator.validate_can_delete(category.category_id, self.categories, products)

        new_list = []
        for c in self.categories:
            if c.category_id != category.category_id:
                new_list.append(c)

        self.categories = new_list
        self._save_changes()

        self._log(user_id, "DELETE_CATEGORY", f"Изтрита категория: {category.name}")
        return True

    def get_by_id(self, category_id: str) -> Optional[Category]:
        target = str(category_id).strip()
        if target == "":
            return None

        for c in self.categories:
            if c.category_id == target:
                return c

        for c in self.categories:
            if c.category_id.startswith(target):
                return c

        return None

    def get_all(self) -> List[Category]:
        return self.categories

    def get_subcategories(self, parent_id: str) -> List[Category]:
        parent = self.get_by_id(parent_id)

        if parent is None:
            pid = None
        else:
            pid = parent.category_id

        result = []
        for c in self.categories:
            if c.parent_id == pid:
                result.append(c)

        return result

    def get_category_tree(self) -> List[dict]:
        return build_category_tree(self.categories)

    def search(self, keyword: str) -> List[Category]:
        if keyword is None:
            return []

        cleaned = keyword.strip()
        if len(cleaned) < 3:
            return []
        return filter_categories(self.categories, cleaned)
