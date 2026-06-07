from filters.category_filters import get_all_children_ids
from typing import List, Optional, Any


class CategoryValidator:


    @staticmethod
    def validate_name(name: Any) -> str:
        cleaned = str(name).strip()
        if not (3 <= len(cleaned) <= 50):
            raise ValueError("Името трябва да е между 3 и 50 символа.")
        return cleaned



    @staticmethod
    def validate_unique(name: str, categories: List[Any], exclude_id: Optional[str] = None) -> None:
        target = name.strip().lower()
        for c in categories:
            if exclude_id and str(c.category_id) == str(exclude_id):
                continue
            if c.name.strip().lower() == target:
                raise ValueError(f"Категория с име '{name}' вече съществува.")



    @staticmethod
    def validate_description(description: Any) -> str:
        cleaned = str(description).strip()
        if not (3 <= len(cleaned) <= 200):
            raise ValueError("Описанието трябва да е между 3 и 200 символа.")
        return cleaned



    @staticmethod
    def validate_no_cycle(category_id, parent_id, categories):
        """ Предотвратява циклични зависимости в йерархията (пр. А да е родител на Б, и Б на А). """
        if not parent_id:
            return

        # Категорията не може да е родител сама на себе си
        if category_id and str(category_id) == str(parent_id):
            raise ValueError("Категорията не може да бъде родител на самата себе си.")

        # Изкачваме се нагоре по веригата
        current_parent_id = parent_id

        while current_parent_id:
            if category_id and str(current_parent_id) == str(category_id):
                raise ValueError("Открита циклична зависимост в йерархията.")

            # Търсим родителя на текущия елемент
            parent_node = None
            for c in categories:
                if str(c.category_id) == str(current_parent_id):
                    parent_node = c
                    break

            # Ако няма родител - стигнали сме до корена
            if not parent_node:
                break

            current_parent_id = parent_node.parent_id





    @staticmethod
    def validate_can_delete(category_id, all_categories, products):
        cid = str(category_id)

        # Търсим ВСИЧКИ подкатегории
        all_descendant_ids = get_all_children_ids(all_categories, cid)
        if all_descendant_ids:
            raise ValueError(f"Категорията има {len(all_descendant_ids)} подкатегории в йерархията. Изтрийте ги първо.")

        # Проверка за продукти в тази конкретна категория
        for p in products:
            for pc in p.categories:
                current_id = str(pc) if isinstance(pc, (str, int)) else str(pc.category_id)
                if current_id == cid:
                    raise ValueError(f"Категорията се използва от продукт '{p.name}'.")