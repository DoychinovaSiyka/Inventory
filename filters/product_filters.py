from typing import List
from models.product import Product


def filter_search(products: List[Product], keyword: str) -> List[Product]:
    if not keyword: return products
    keyword = keyword.lower().strip()
    words = keyword.split()

    results = []
    for p in products:
        cat_names = " ".join([c.name.lower() for c in p.categories])
        full_text = f"{p.name.lower()} {p.description.lower()} {cat_names}"
        if all(word in full_text for word in words):
            results.append(p)
    return results


def filter_combined(products: List[Product], inventory_controller=None, **kwargs):
    """филтър, който обединява всички критерии."""

    results = products

    if kwargs.get("keyword"):
        results = filter_search(results, kwargs["keyword"])

    if kwargs.get("category_id"):
        target = str(kwargs["category_id"]).strip()
        results = [p for p in results if any(str(c.category_id) == target for c in p.categories)]

    min_p, max_p = kwargs.get("min_price"), kwargs.get("max_price")
    if min_p is not None:
        results = [p for p in results if p.price >= min_p]
    if max_p is not None:
        results = [p for p in results if p.price <= max_p]

    return results