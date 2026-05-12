def build_category_tree(categories, parent_id=None, level=0):
    """Изгражда дървото по по-прост начин, но със същата логика."""
    tree = []
    children = []
    for c in categories:
        if (c.parent_id is None and parent_id is None) or str(c.parent_id) == str(parent_id):
            children.append(c)

    children.sort(key=lambda x: x.name)

    # Добавяме ги в дървото и викаме рекурсия за всяко дете
    for child in children:
        tree.append({"category": child, "level": level})
        subtree = build_category_tree(categories, child.category_id, level + 1)
        for item in subtree:
            tree.append(item)

    return tree





def get_category_stats(categories, products):
    """Брои продуктите във всяка категория по по-прост начин."""
    stats = {}

    for cat in categories:
        cat_id = str(cat.category_id)
        count = 0

        for p in products:
            for pc in p.categories:
                if str(pc.category_id) == cat_id:
                    count += 1
                    break

        stats[cat.name] = count

    return stats
