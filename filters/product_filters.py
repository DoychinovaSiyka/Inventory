from typing import List, Optional
from models.product import Product


def filter_by_category(products: List[Product], allowed_category_ids) -> List[Product]:
    """
    Филтрира продукти по списък от позволени категории.
    Използва се и от контролера, и от комбинирания филтър.
    """
    if not allowed_category_ids:
        return []

    # Превръщаме в сет от стрингове за бързина и избягване на проблеми с типа данни
    if isinstance(allowed_category_ids, str):
        allowed_set = {allowed_category_ids.strip()}
    else:
        allowed_set = {str(cid).strip() for cid in allowed_category_ids}

    results = []
    for p in products:
        # Вземаме ID-тата на категориите на продукта
        p_cat_ids = [str(c.category_id) if hasattr(c, "category_id") else str(c) for c in p.categories]

        # Проверяваме дали някоя от категориите на продукта е в позволения списък
        if any(cid in allowed_set for cid in p_cat_ids):
            results.append(p)
    return results


def filter_search(products: List[Product], keyword: str) -> List[Product]:
    """Търсене по име, описание или име на категория."""
    keyword = (keyword or "").lower().strip()
    if not keyword:
        return products

    search_words = keyword.split()
    results = []

    for p in products:
        product_text = f"{p.name} {p.description}".lower()

        # Проверка дали ВСИЧКИ думи от търсенето присъстват в продукта
        if all(word in product_text for word in search_words):
            results.append(p)
            continue

        # Или дали присъстват в името на някоя от категориите му
        for c in p.categories:
            c_name = (c.name if hasattr(c, "name") else str(c)).lower()
            if all(word in c_name for word in search_words):
                results.append(p)
                break
    return results


def filter_combined(products: List[Product], inventory_controller=None, **kwargs):
    """
    Главен филтър, който обединява всички критерии без да повтаря логика.
    Вика горните специализирани функции.
    """
    results = products

    # 1. Търсене по ключова дума
    if kwargs.get('keyword'):
        results = filter_search(results, kwargs['keyword'])

    # 2. Филтър по категория (поддържа йерархични списъци)
    if kwargs.get('category_id'):
        results = filter_by_category(results, kwargs['category_id'])

    # 3. Филтър по цена
    min_p = kwargs.get('min_price')
    max_p = kwargs.get('max_price')
    if min_p is not None or max_p is not None:
        results = [
            p for p in results
            if (min_p is None or p.price >= min_p) and (max_p is None or p.price <= max_p)
        ]

    # 4. Филтър по наличност (изисква контролер на инвентара)
    min_q = kwargs.get('min_quantity')
    max_q = kwargs.get('max_quantity')
    if (min_q is not None or max_q is not None) and inventory_controller:
        results = [
            p for p in results
            if (min_q is None or inventory_controller.get_total_stock(p.product_id) >= min_q) and
               (max_q is None or inventory_controller.get_total_stock(p.product_id) <= max_q)
        ]

    return results