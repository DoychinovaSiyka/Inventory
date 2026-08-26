from typing import List
from models.category import Category







def get_all_children_ids(categories, parent_id):
    result = []
    visited = set()

    def collect(pid):
        pid_str = str(pid)
        if pid_str in visited:
            return
        visited.add(pid_str)

        for c in categories:
            if str(c.parent_id) == pid_str:
                cid = str(c.category_id)
                result.append(cid)
                collect(cid)

    collect(parent_id)
    return result





def get_category_stats(categories, products):
    """Статистика само за родителските категории + броене на всички подкатегории."""
    stats = []


    parent_categories = [c for c in categories if c.parent_id is None]

    for parent in parent_categories:
        child_ids = get_all_children_ids(categories, parent.category_id)

        count = 0
        for p in products:
            for pc in p.categories:
                cat_id = str(pc if isinstance(pc, (str, int)) else pc.category_id)
                if cat_id in child_ids:
                    count += 1

        stats.append({"id": parent.category_id, "name": parent.name, "product_count": count})

    return stats
