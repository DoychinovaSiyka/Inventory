from typing import List
from models.category import Category


def build_category_tree(categories: List[Category]) -> List[dict]:
    """Изгражда йерархията на категориите стъпка по стъпка."""
    tree = []
    if not categories:
        return tree

    # кои са главните категории
    root_categories = []
    for c in categories:
        if c.parent_id is None:
            root_categories.append(c)
        else:
            pid = str(c.parent_id).strip().lower()
            if pid == "" or pid == "none":
                root_categories.append(c)

    # започваме да търсим нейните деца за главната категория
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
        if c.parent_id is not None:
            c_parent_str = str(c.parent_id).strip()
            if c_parent_str == parent_id_str:
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
            # Категорията присъства ли в списъка на продукта
            for p_cat in prod.categories:
                p_cat_id = str(p_cat.category_id).strip()
                if p_cat_id == current_cat_id:
                    count += 1
                    break  # не проверяваме другите категории на продукта

        stats[cat.name] = count

    return stats
