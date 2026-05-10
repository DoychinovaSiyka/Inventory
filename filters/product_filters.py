from typing import List


def filter_search(products: List, keyword: str) -> List:
    """Търсене по име, описание и имена на категории."""
    if not keyword:
        return products

    keyword = keyword.lower().strip()
    words = keyword.split()
    results = []

    for p in products:
        # Имена на категориите
        category_names = [c.name.lower() for c in p.categories]

        full_text = (f"{p.name.lower()} " 
                     f"{p.description.lower()} " 
                     f"{' '.join(category_names)}")

        # Всички думи трябва да присъстват
        if all(word in full_text for word in words):
            results.append(p)

    return results




def filter_combined(products: List, **kwargs):
    """ Универсален филтър - keyword, category_ids (list), min_price, max_price."""
    results = products
    keyword = kwargs.get("keyword")
    if keyword:
        results = filter_search(results, keyword)

    #  Филтър по категории (включително йерархия)
    category_ids = kwargs.get("category_ids")
    if category_ids:
        wanted = set(str(cid) for cid in category_ids)

        filtered = []
        for p in results:
            product_cats = {str(c.category_id) for c in p.categories}
            if product_cats & wanted:
                filtered.append(p)
        results = filtered


    min_p = kwargs.get("min_price")
    max_p = kwargs.get("max_price")
    try:
        if min_p not in (None, ""):
            min_val = float(min_p)
            results = [p for p in results if float(p.price) >= min_val]

        if max_p not in (None, ""):
            max_val = float(max_p)
            results = [p for p in results if float(p.price) <= max_val]

    except (ValueError, TypeError):
        pass

    return results
