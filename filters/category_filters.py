from typing import List
from models.category import Category

def filter_categories(categories: List[Category], keyword: str) -> List[Category]:
    """Търси в списък с категории по име или описание."""
    if not keyword:
        return categories

    keyword = keyword.lower().strip()
    results = []

    for c in categories:
        name_match = keyword in c.name.lower() if c.name else False
        desc_match = keyword in c.description.lower() if c.description else False

        if name_match or desc_match:
            results.append(c)

    return results

def get_all_children_ids(categories: List[Category], parent_id: str) -> List[str]:
    """
    Рекурсивно събира ID-то на родителя и ВСИЧКИ негови наследници.
    Използва се от вюто за филтриране на продукти в главна категория.
    """
    child_ids = [parent_id]
    for cat in categories:
        if str(cat.parent_id) == str(parent_id):
            child_ids.extend(get_all_children_ids(categories, cat.category_id))
    return child_ids

def filter_by_parent(categories: List[Category], parent_id: str) -> List[Category]:
    """
    Връща списък от обекти Category, които са наследници на parent_id.
    """
    results = []
    parent_id_str = str(parent_id) if parent_id else None

    for c in categories:
        if str(c.parent_id) == parent_id_str:
            results.append(c)
            # Рекурсивно добавяме децата на намерената подкатегория
            results.extend(filter_by_parent(categories, c.category_id))

    return results