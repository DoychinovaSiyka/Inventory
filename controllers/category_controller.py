from typing import Optional, List
from datetime import datetime
from storage.json_repository import Repository
from models.category import Category
from validators.category_validator import CategoryValidator


class CategoryController:
    def __init__(self, repo: Repository):
        self.repo = repo
        self.categories: List[Category] = [Category.from_dict(c) for c in self.repo.load()]
        # Зареждаме всички категории от JSON файла чрез хранилището (JSONRepository).
        # Методът repo.load() връща списък от речници, а Category.from_dict()
        # преобразува всеки речник в Category обект. Така получаваме списък от реални Category обекти,
        # с които контролерът може да работи.

    def add(self, name: str, description: str = "") -> Category:
        CategoryValidator.validate_name(name)
        CategoryValidator.validate_unique(name, self.categories)
        CategoryValidator.validate_description(description)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        category = Category(
            name=name,
            description=description,
            created=now,
            modified=now
        )
        # Създаваме нова категория чрез конструктора на Category.
        # Подаваме всички полета, описани в документацията — name, description, created и modified.
        # Това гарантира, че Category обектът е валиден още при създаването си.

        self.categories.append(category)
        self._save()
        return category

    def get_all(self) -> List[Category]:
        return self.categories

    def get_by_id(self, category_id: str) -> Optional[Category]:
        return next((c for c in self.categories if c.category_id == category_id), None)

    def update_name(self, category_id: str, new_name: str) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError("Категорията не е намерена.")

        CategoryValidator.validate_update_name(new_name)
        CategoryValidator.validate_unique(new_name, self.categories)

        category.name = new_name
        category.update_modified()
        self._save()
        return True

    def update_description(self, category_id: str, new_description: str) -> bool:
        category = self.get_by_id(category_id)
        if not category:
            raise ValueError("Категорията не е намерена.")

        CategoryValidator.validate_description(new_description)

        category.description = new_description
        category.update_modified()
        self._save()
        return True

    def remove(self, category_id: str) -> bool:
        original_len = len(self.categories)
        self.categories = [c for c in self.categories if c.category_id != category_id]

        if len(self.categories) < original_len:
            self._save()
            return True

        return False

    def search(self, keyword: str) -> List[Category]:
        keyword = keyword.lower()
        return [
            c for c in self.categories
            if keyword in c.name.lower()
            or keyword in (c.description or "").lower()
        ]

    def _save(self) -> None:
        self.repo.save([c.to_dict() for c in self.categories])
