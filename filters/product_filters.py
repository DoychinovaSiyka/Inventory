from typing import List


def filter_combined(products: List, **kwargs):
    """Филтър за продукти. Поддържа: keyword (име/описание/категория), category_ids (списък)."""
    results = products

    keyword = kwargs.get("keyword")
    if keyword:
        keyword = keyword.lower().strip()
        words = keyword.split()

        filtered_by_text = []
        for p in results:
            cat_names = " ".join([c.name.lower() for c in p.categories])
            full_text = f"{p.name.lower()} {p.description.lower()} {cat_names}"


            if all(word in full_text for word in words):
                filtered_by_text.append(p)
        results = filtered_by_text


    category_ids = kwargs.get("category_ids")
    if category_ids:
        wanted_ids = set(str(cid) for cid in category_ids)

        filtered_by_cat = []
        for p in results:
            product_cat_ids = {str(c.category_id) for c in p.categories}
            if product_cat_ids & wanted_ids:
                filtered_by_cat.append(p)
        results = filtered_by_cat


    return results