from typing import List, Dict
from models.category import Category


def build_category_tree(categories: List[Category]) -> List[dict]:
    """Изгражда йерархична структура (дърво) от плосък списък с категории.
    Връща списък от речници, подходящ за визуализация в менюта.
    """
    tree = []
    # 1. Намираме коренните категории (тези без родител)
    root_categories = [c for c in categories if c.parent_id is None]
    # 2. За всяка коренна категория, намираме нейните деца рекурсивно
    for root in root_categories:
        # Добавяме корена (Ниво 0)
        tree.append({"category": root, "level": 0})
        # Викаме помощната функция за децата му
        _add_children_to_tree(root.category_id, categories, tree, current_level=1)

    return tree


def _add_children_to_tree(parent_id: str, all_categories: List[Category], tree: List[dict], current_level: int):
    """Помощна (private) функция, която обхожда дървото надолу."""
    # Намираме всички категории, чийто родител е подаденият ID
    children = [c for c in all_categories if str(c.parent_id) == str(parent_id)]
    for child in children:
        tree.append({"category": child,"level": current_level})
        # Продължаваме надолу към следващото ниво (рекурсия)
        _add_children_to_tree(child.category_id, all_categories, tree, current_level + 1)


def get_category_stats(categories: List[Category], products: List) -> dict:
    """Пример за допълнителна аналитика: Колко продукта има във всяка категория."""
    stats = {}
    for cat in categories:
        count = sum(1 for p in products if cat.category_id in [str(c) for c in p.categories])
        stats[cat.name] = count
    return stats