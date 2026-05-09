from typing import List
from models.category import Category

def build_category_tree(categories: List[Category]) -> List[dict]:
    """Изгражда йерархията на категориите стъпка по стъпка (с нива за визуализация)."""
    tree = []
    if not categories:
        return tree

    # Намираме кои са главните категории (тези без родител)
    root_categories = [
        c for c in categories
        if c.parent_id is None or str(c.parent_id).strip() == "" or str(c.parent_id).lower() == "none"
    ]

    # За всяка главна категория започваме да търсим нейните деца
    for root in root_categories:
        tree.append({"category": root, "level": 0})
        _add_children_recursive_view(root.category_id, categories, tree, 1)

    return tree

def _add_children_recursive_view(parent_id: str, all_categories: List[Category], tree: List[dict], current_level: int):
    """Търси подкатегории рекурсивно и ги добавя в списъка с ниво на отместване."""
    if not parent_id:
        return

    parent_id_str = str(parent_id).strip()

    for c in all_categories:
        # Проверка дали текущата категория е дете на parent_id
        if c.parent_id and str(c.parent_id).strip() == parent_id_str:
            tree.append({"category": c, "level": current_level})
            # Проверяваме за наследници на по-долно ниво
            _add_children_recursive_view(c.category_id, all_categories, tree, current_level + 1)

def get_category_stats(categories: List[Category], products: List) -> dict:
    """Изчислява колко продукта има във всяка категория."""
    stats = {}

    for cat in categories:
        count = 0
        current_cat_id = str(cat.category_id).strip()

        for prod in products:
            # Проверяваме дали категорията присъства в списъка на продукта
            if any(str(p_cat.category_id).strip() == current_cat_id for p_cat in prod.categories):
                count += 1

        stats[cat.name] = count

    return stats