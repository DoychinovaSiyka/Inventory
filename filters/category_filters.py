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
