from typing import List
from models.category import Category

def filter_categories(categories: List[Category], keyword: str) -> List[Category]:
    """Търси в списък с категории по име или описание (case-insensitive)."""
    if not keyword:
        return categories

    keyword = keyword.lower().strip()
    results = []

    for c in categories:
        name_txt = (c.name or "").lower()
        desc_txt = (c.description or "").lower()

        if keyword in name_txt or keyword in desc_txt:
            results.append(c)

    return results

def get_all_children_objects(categories: List[Category], parent_id: str) -> List[Category]:
    """Рекурсивно събира ВСИЧКИ обекти (категории), които са наследници на parent_id."""
    results = []
    if not parent_id:
        return results

    parent_id_str = str(parent_id).strip()

    for c in categories:
        if c.parent_id and str(c.parent_id).strip() == parent_id_str:
            results.append(c)
            # Продължаваме надолу по дървото
            results.extend(get_all_children_objects(categories, c.category_id))

    return results

def get_all_children_ids(categories: List[Category], parent_id: str) -> List[str]:
    """Връща списък от ID-то на родителя и ВСИЧКИ негови наследници (за филтриране)."""
    # Взимаме обектите наследници
    children = get_all_children_objects(categories, parent_id)
    # Връщаме началния ID + всички намерени ID-та
    return [str(parent_id)] + [str(c.category_id) for c in children]