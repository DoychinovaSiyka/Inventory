from typing import List
from models.category import Category




def filter_categories(categories, keyword):
    if not keyword:
        return categories

    keyword = keyword.lower().strip()
    results = []

    for c in categories:
        name_txt = (c.name or "").lower()
        desc_txt = (c.description or "").lower()
        full_id = str(c.category_id).lower()

        if keyword in name_txt or keyword in desc_txt or full_id.startswith(keyword):
            results.append(c)

    return results




def get_all_children_objects(categories: List[Category], parent_id: str, visited=None) -> List[Category]:
    """Рекурсивно събиране на всички наследници."""
    results = []
    if not parent_id:
        return results

    if visited is None:
        visited = set()

    parent_id_str = str(parent_id).strip()
    if parent_id_str in visited:
        return results
    visited.add(parent_id_str)

    for c in categories:
        if c.parent_id and str(c.parent_id).strip() == parent_id_str:
            results.append(c)
            results.extend(get_all_children_objects(categories, c.category_id, visited))

    return results



def get_all_children_ids(categories, parent_id):
    """Връща списък с ID-то на родителя и всички негови подкатегории."""
    result = [str(parent_id)]

    # намираме всички деца
    for cat in categories:
        if str(cat.parent_id) == str(parent_id):
            result.append(str(cat.category_id))

            # проверяваме и под-децата
            for sub in categories:
                if str(sub.parent_id) == str(cat.category_id):
                    result.append(str(sub.category_id))


    unique = []
    for cid in result:
        if cid not in unique:
            unique.append(cid)

    return unique
