from collections import Counter



def get_category_stats(categories, products):
    """Брои продуктите във всяка категория с O(N) сложност."""
    counts = Counter()
    for p in products:
        for pc in p.categories:
            cat_id = str(pc if isinstance(pc, (str, int)) else pc.category_id)
            counts[cat_id] += 1


    return [{"id": cat.category_id, "name": cat.name, "product_count": counts[str(cat.category_id)]} for cat in categories]