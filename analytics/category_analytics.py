from typing import List, Dict
from models.category import Category


def build_category_tree(categories: List[Category]) -> List[dict]:
    """Изгражда йерархията на категориите стъпка по стъпка."""
    tree = []
    if not categories:
        return tree

    # 1. Намираме кои са главните категории (тези без родител)
    root_categories = []
    for c in categories:
        if c.parent_id is None or str(c.parent_id).strip() == "" or str(c.parent_id).lower() == "none":
            root_categories.append(c)

    # 2. За всяка главна категория започваме да търсим нейните деца
    for root in root_categories:
        # Добавяме главната категория (ниво 0)
        tree.append({"category": root, "level": 0})
        # Викаме помощника да намери децата й
        _add_children_human_way(root.category_id, categories, tree, 1)

    return tree


def _add_children_human_way(parent_id: str, all_categories: List[Category], tree: List[dict], current_level: int):
    """Търси подкатегории по най-обикновения начин с цикъл."""
    if not parent_id:
        return

    parent_id_str = str(parent_id).strip()

    # Обхождаме всички категории, за да видим кои са деца на текущия parent_id
    for c in all_categories:
        # Ако родителското ID на категорията съвпада с търсеното
        if c.parent_id and str(c.parent_id).strip() == parent_id_str:
            # Добавяме детето в списъка с неговото ниво
            tree.append({"category": c, "level": current_level})
            # Веднага проверяваме дали това дете има свои собствени деца (рекурсия)
            _add_children_human_way(c.category_id, all_categories, tree, current_level + 1)


def get_category_stats(categories: List[Category], products: List) -> dict:
    """Изчислява колко продукта има във всяка категория с вложени цикли."""
    stats = {}

    for cat in categories:
        count = 0
        current_cat_id = str(cat.category_id).strip()

        for prod in products:
            # Проверяваме списъка с категории на продукта
            for p_cat_obj in prod.categories:
                if str(p_cat_obj.category_id).strip() == current_cat_id:
                    count += 1
                    break

        stats[cat.name] = count

    return stats