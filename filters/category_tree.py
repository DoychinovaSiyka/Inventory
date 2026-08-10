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
