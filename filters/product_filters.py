from typing import List
from models.product import Product


def filter_by_category(products: List[Product], category_input) -> List[Product]:
    """Филтрира продукти по категория."""

    if not category_input:
        return products

    allowed_ids = []

    if isinstance(category_input, (list, tuple, set)):
        for cid in category_input:
            allowed_ids.append(str(cid).strip())
    else:
        allowed_ids.append(str(category_input).strip())

    results = []

    for p in products:
        product_cat_ids = []
        for c in p.categories:
            product_cat_ids.append(str(c.category_id))

        # Проверка за съвпадение
        match_found = False
        for pid in product_cat_ids:
            for allowed in allowed_ids:
                if pid == allowed:
                    match_found = True
                    break
            if match_found:
                break

        if match_found:
            results.append(p)

    return results


def filter_search(products: List[Product], keyword: str) -> List[Product]:
    """Търсене по име, описание или име на категория."""

    if not keyword:
        return products

    keyword = keyword.lower().strip()
    words = keyword.split()

    results = []

    for p in products:
        name_text = p.name.lower()
        desc_text = p.description.lower()

        cat_names = ""
        for c in p.categories:
            cat_names += " " + c.name.lower()

        full_text = name_text + " " + desc_text + " " + cat_names

        # Проверка дали всички думи присъстват
        all_found = True
        for w in words:
            if w not in full_text:
                all_found = False
                break

        if all_found:
            results.append(p)

    return results


def filter_combined(products: List[Product], inventory_controller=None, **kwargs):
    """Главен филтър, който обединява всички критерии."""

    results = products

    # Търсене по ключова дума
    if "keyword" in kwargs and kwargs["keyword"]:
        results = filter_search(results, kwargs["keyword"])

    # Филтър по категория
    if "category_id" in kwargs and kwargs["category_id"]:
        results = filter_by_category(results, kwargs["category_id"])

    # Филтър по цена
    min_p = kwargs.get("min_price")
    max_p = kwargs.get("max_price")

    if min_p is not None or max_p is not None:
        filtered = []
        for p in results:
            ok = True

            if min_p is not None:
                if p.price < min_p:
                    ok = False
            if max_p is not None:
                if p.price > max_p:
                    ok = False

            if ok:
                filtered.append(p)
        results = filtered

    return results
