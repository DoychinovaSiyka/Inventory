import uuid
from typing import Optional, List
from datetime import datetime
from storage.json_repository import Repository
from models.category import Category
from validators.category_validator import CategoryValidator


class CategoryController:
    def __init__(self, repo: Repository):
        self.repo = repo
        # Зареждане на категориите от JSON файла
        self.categories: List[Category] = [Category.from_dict(c) for c in self.repo.load()]

    # CRUD операции
    def add(self, name: str, description: str = "", parent_id: Optional[str] = None) -> Category:
        """Добавя нова категория или подкатегория."""
        CategoryValidator.validate_name(name)
        CategoryValidator.validate_unique(name, self.categories)
        CategoryValidator.validate_description(description)

        # Проверка за валиден родител
        if parent_id and not self.get_by_id(parent_id):
            raise ValueError("Родителската категория не съществува.")

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Генериране на уникално ID
        category = Category(category_id=str(uuid.uuid4()), name=name, description=description,
                            parent_id=parent_id, created=now, modified=now)

        self.categories.append(category)
        self.save_changes()
        return category

    def update_name(self, category_id: str, new_name: str) -> bool:
        # Намиране на категорията
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError("Категорията не е намерена.")

        CategoryValidator.validate_update_name(new_name)

        # Проверка за уникално име
        CategoryValidator.validate_unique(new_name,
                                          [c for c in self.categories if c.category_id != category_id])

        category.name = new_name
        category.update_modified()
        self.save_changes()
        return True

    def update_description(self, category_id: str, new_description: str) -> bool:
        # Намиране на категорията
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError("Категорията не е намерена.")

        CategoryValidator.validate_description(new_description)
        category.description = new_description
        category.update_modified()
        self.save_changes()
        return True

    def update_parent(self, category_id: str, parent_id: Optional[str]) -> bool:
        """Промяна на родителската категория."""
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError("Категорията не е намерена.")

        # Проверка дали новият родител съществува
        if parent_id and not self.get_by_id(parent_id):
            raise ValueError("Новият родител не съществува.")

        # Проверка дали не става собствен родител
        CategoryValidator.validate_parent_id(parent_id, category_id)

        category.parent_id = parent_id
        category.update_modified()
        self.save_changes()
        return True

    def remove(self, category_id: str, product_controller=None) -> bool:
        # Забрана за изтриване, ако има подкатегории
        has_children = any(str(c.parent_id) == str(category_id) for c in self.categories)
        if has_children:
            raise ValueError("Не може да изтриете категория с подкатегории!")

        # Забрана за изтриване, ако има продукти в категорията
        if product_controller:
            has_products = any(
                str(category_id) in [
                    str(cat.category_id) if isinstance(cat, Category) else str(cat)
                    for cat in p.categories
                ]
                for p in product_controller.get_all()
            )
            if has_products:
                raise ValueError("Не може да изтриете категория с налични продукти!")

        original_len = len(self.categories)
        self.categories = [c for c in self.categories if str(c.category_id) != str(category_id)]

        if len(self.categories) < original_len:
            self.save_changes()
            return True

        return False

    # Методи за достъп
    def get_all(self) -> List[Category]:
        return self.categories

    def get_by_id(self, category_id: str) -> Optional[Category]:
        # Търсене по ID
        return next((c for c in self.categories if str(c.category_id) == str(category_id)), None)

    def get_subcategories(self, parent_id: str) -> List[Category]:
        # Връща подкатегориите на даден родител
        return [c for c in self.categories if str(c.parent_id) == str(parent_id)]

    def get_category_tree(self) -> List[dict]:
        # Изграждане на йерархия за менюто
        tree = []
        main_categories = [c for c in self.categories if c.parent_id is None]

        for main in main_categories:
            tree.append({"category": main, "level": 0})
            for child in self.get_subcategories(main.category_id):
                tree.append({"category": child, "level": 1})

        return tree

    def search(self, keyword: str) -> List[Category]:
        # Търсене по име или описание
        keyword = keyword.lower()
        return [c for c in self.categories
                if keyword in c.name.lower() or keyword in (c.description or "").lower()]

    def select_category(self, raw_index):
        index = int(raw_index)
        categories = self.get_all()

        if index < 0 or index >= len(categories):
            raise ValueError("Невалиден избор на категория.")

        return categories[index]

    def save_changes(self) -> None:
        # Записване на категориите обратно в JSON файла
        self.repo.save([c.to_dict() for c in self.categories])
