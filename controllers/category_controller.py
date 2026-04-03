import uuid
from typing import Optional, List
from datetime import datetime
from storage.json_repository import Repository
from models.category import Category
from validators.category_validator import CategoryValidator


class CategoryController:
    def __init__(self, repo: Repository):
        self.repo = repo
        # Зареждаме всички категории от JSON файла чрез хранилището (JSONRepository).
        # Методът repo.load() връща списък от речници, а Category.from_dict()
        # преобразува всеки речник в Category обект. Така получаваме списък от реални Category обекти,
        # с които контролерът може да работи.
        self.categories: List[Category] = [Category.from_dict(c) for c in self.repo.load()]

    def add(self, name: str, description: str = "", parent_id: Optional[str] = None) -> Category:
        """Добавя нова категория или подкатегория (с parent_id)."""
        CategoryValidator.validate_name(name)
        CategoryValidator.validate_unique(name, self.categories)
        CategoryValidator.validate_description(description)

        # ДОБАВКА: Проверка дали родителят съществува
        if parent_id and not self.get_by_id(parent_id):
            raise ValueError("Родителската категория не съществува.")

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Тук използваме uuid за category_id, за да е сигурно уникално при йерархия
        category = Category(
            category_id=str(uuid.uuid4()),
            name=name,
            description=description,
            parent_id=parent_id,  # ДОБАВКА
            created=now,
            modified=now
        )

        self.categories.append(category)
        self.save_changes()
        return category

    def get_all(self) -> List[Category]:
        return self.categories

    def get_by_id(self, category_id: str) -> Optional[Category]:
        # Подсигуряваме сравнението като стрингове
        return next((c for c in self.categories if str(c.category_id) == str(category_id)), None)

    # Метод за намиране на подкатегории
    def get_subcategories(self, parent_id: str) -> List[Category]:
        return [c for c in self.categories if str(c.parent_id) == str(parent_id)]

    # Метод за йерархично дърво (за менюто)
    def get_category_tree(self) -> List[dict]:
        tree = []
        main_categories = [c for c in self.categories if c.parent_id is None]
        for main in main_categories:
            tree.append({"category": main, "level": 0})
            children = self.get_subcategories(main.category_id)
            for child in children:
                tree.append({"category": child, "level": 1})
        return tree

    def update_name(self, category_id: str, new_name: str) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError("Категорията не е намерена.")

        CategoryValidator.validate_update_name(new_name)
        # Проверяваме уникалност, но изключваме текущата категория
        CategoryValidator.validate_unique(new_name, [c for c in self.categories
                                                     if c.category_id != category_id])

        category.name = new_name
        category.update_modified()
        self.save_changes()
        return True

    def update_description(self, category_id: str, new_description: str) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError("Категорията не е намерена.")

        CategoryValidator.validate_description(new_description)
        category.description = new_description
        category.update_modified()
        self.save_changes()
        return True

    def remove(self, category_id: str, product_controller=None) -> bool:
        #  Не трием категория, ако тя самата е родител на други
        has_children = any(str(c.parent_id) == str(category_id) for c in self.categories)
        if has_children:
            raise ValueError("Не може да изтриете категория, която има подкатегории!")

        # Проверка дали има продукти, свързани с тази категория, преди да я изтрием
        if product_controller:
            # Тук проверяваме в продуктите (поддържаме и стария и новия формат на запис)
            has_products = any(str(category_id) in [str(getattr(cat, 'category_id', cat)) for cat in p.categories]
                for p in product_controller.get_all())
            if has_products:
                raise ValueError("Не може да изтриете категория с налични продукти в нея!")

        original_len = len(self.categories)
        self.categories = [c for c in self.categories if str(c.category_id) != str(category_id)]

        if len(self.categories) < original_len:
            self.save_changes()
            return True
        return False

    def search(self, keyword: str) -> List[Category]:
        keyword = keyword.lower()
        return [c for c in self.categories
                if keyword in c.name.lower() or keyword in (c.description or "").lower()]

    def save_changes(self) -> None:
        # Записваме промените обратно в JSON файла чрез репозиторито
        self.repo.save([c.to_dict() for c in self.categories])