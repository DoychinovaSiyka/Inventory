from typing import List


def filter_search(products: List, keyword: str) -> List:
    """Търсене по име, описание и имена на категории."""
    if not keyword:
        return products

    keyword = keyword.lower().strip()
    words = keyword.split()
    results = []

    for p in products:
        # Извличаме имената на категориите безопасно
        cat_names_list = []
        for c in p.categories:
            if hasattr(c, "name"):
                cat_names_list.append(c.name.lower())

        cat_names = " ".join(cat_names_list)

        # Генерираме целия текст за търсене веднъж за продукта
        full_text = f"{p.name.lower()} {p.description.lower()} {cat_names}"

        # Проверка дали ВСИЧКИ думи от търсенето присъстват в текста
        if all(word in full_text for word in words):
            results.append(p)

    return results


def filter_combined(products: List, **kwargs):
    """
    Универсален филтър с оптимизирана производителност. Поддържа: keyword, category_ids (list), min_price, max_price."""
    results = products

    if kwargs.get("keyword"):
        results = filter_search(results, kwargs["keyword"])

    # Йерархичен филтър по категории
    category_ids = kwargs.get("category_ids")
    if category_ids:
        # Използваме set за O(1) скорост на търсене
        search_set = set(str(cid) for cid in category_ids)
        results = [p for p in results if set(p.get_category_ids()).intersection(search_set)]

    #  филтър по цена
    try:
        # Конвертираме границите към float ВЕДНЪЖ преди циклите
        min_p = kwargs.get("min_price")
        if min_p is not None and min_p != "":
            min_val = float(min_p)
            results = [p for p in results if p.price >= min_val]

        max_p = kwargs.get("max_price")
        if max_p is not None and max_p != "":
            max_val = float(max_p)
            results = [p for p in results if p.price <= max_val]

    except (ValueError, TypeError):
        pass

    return results