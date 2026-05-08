from typing import List, Dict
from models.category import Category


def build_category_tree(categories: List[Category]) -> List[dict]:
    """Дървовидна структура от списък с категории."""
    tree = []
    # Категориите, които нямат родител – те са началото на дървото
    root_categories = [c for c in categories if c.parent_id is None]
    # За всеки корен добавям записа и после слизам надолу по децата
    for root in root_categories:
        tree.append({"category": root, "level": 0})
        _add_children_to_tree(root.category_id, categories, tree, current_level=1)

    return tree


def _add_children_to_tree(parent_id: str, all_categories: List[Category],
                          tree: List[dict], current_level: int):
    """ Помощна функция, която намира децата на дадена категория
    и ги добавя към дървото. След това продължава надолу рекурсивно."""
    # Търся всички категории, които имат този parent_id
    children = [c for c in all_categories if str(c.parent_id) == str(parent_id)]

    for child in children:
        tree.append({"category": child, "level": current_level})
        # Продължавам към следващото ниво
        _add_children_to_tree(child.category_id, all_categories, tree, current_level + 1)


def get_category_stats(categories: List[Category], products: List) -> dict:
    """Статистика – броя продукти във всяка категория."""
    stats = {}
    for cat in categories:
        count = sum(1 for p in products if cat.category_id in
                    [str(c) for c in p.categories])
        stats[cat.name] = count

    return stats
