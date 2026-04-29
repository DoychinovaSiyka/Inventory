from typing import List, Optional
from models.product import Product


def filter_search(products: List[Product], keyword: str) -> List[Product]:
    keyword = (keyword or "").lower().strip()
    if not keyword:
        return []

    results = []
    for p in products:
        name = p.name.lower() if p.name else ""
        description = p.description.lower() if p.description else ""
        categories = p.categories or []
        tags = p.tags or []
        supplier_id = str(p.supplier_id).lower() if p.supplier_id else ""

        # име + описание
        if keyword in name or keyword in description:
            results.append(p)
            continue

        found_category = False
        for c in categories:
            c_name = c.name.lower() if hasattr(c, "name") else str(c).lower()
            if keyword in c_name:
                found_category = True
                break
        if found_category:
            results.append(p)
            continue

        found_tag = False
        for t in tags:
            if keyword in t.lower():
                found_tag = True
                break
        if found_tag:
            results.append(p)
            continue

        # доставчик (по ID)
        if supplier_id and keyword in supplier_id:
            results.append(p)

    return results



def filter_by_category(products: List[Product], category_id: str) -> List[Product]:
    category_id = str(category_id)
    results = []

    for p in products:
        categories = p.categories or []
        match = False
        for c in categories:
            if str(c.category_id) == category_id:
                match = True
                break
        if match:
            results.append(p)

    return results



def filter_by_multiple_category_ids(products: List[Product], category_ids: List[str]) -> List[Product]:
    target_ids = set(str(cid) for cid in category_ids)
    results = []
    for p in products:
        categories = p.categories or []
        found = False
        for c in categories:
            if str(c.category_id) in target_ids:
                found = True
                break
        if found:
            results.append(p)

    return results



def filter_by_supplier(products: List[Product], supplier_id: str) -> List[Product]:
    supplier_id = str(supplier_id)
    results = []

    for p in products:
        if str(p.supplier_id) == supplier_id:
            results.append(p)

    return results



def filter_by_price_range(products: List[Product], min_price: Optional[float], max_price: Optional[float]) -> List[Product]:
    results = []

    # първо взимаме само продуктите с цена
    for p in products:
        if p.price is not None:
            results.append(p)

    if min_price is not None:
        tmp = []
        for p in results:
            if p.price >= min_price:
                tmp.append(p)
        results = tmp

    if max_price is not None:
        tmp = []
        for p in results:
            if p.price <= max_price:
                tmp.append(p)
        results = tmp

    return results



def filter_low_stock(products, threshold, inventory_controller=None):
    """Връща продуктите, които са паднали под зададения минимум."""
    if inventory_controller is None:
        return []

    results = []

    for p in products:
        stock = inventory_controller.get_total_stock(p.product_id)
        if stock < threshold:
            results.append(p)

    return results



def filter_combined(products, inventory_controller, keyword=None, min_price=None, max_price=None, min_quantity=None,
                    max_quantity=None, category_id=None, supplier_id=None, location_id=None):

    results = []
    # копираме всички продукти
    for p in products:
        results.append(p)

    if keyword:
        kw = keyword.lower()
        tmp = []
        for p in results:
            if kw in p.name.lower() or kw in p.description.lower():
                tmp.append(p)
        results = tmp

    if min_price is not None:
        tmp = []
        for p in results:
            if p.price >= min_price:
                tmp.append(p)
        results = tmp

    if max_price is not None:
        tmp = []
        for p in results:
            if p.price <= max_price:
                tmp.append(p)
        results = tmp

    # количество (от инвентара)
    if min_quantity is not None or max_quantity is not None:
        tmp = []
        for p in results:
            total = inventory_controller.get_total_stock(p.product_id)
            if min_quantity is not None and total < min_quantity:
                continue
            if max_quantity is not None and total > max_quantity:
                continue
            tmp.append(p)
        results = tmp

    if category_id:
        tmp = []
        for p in results:
            found = False
            for c in p.categories:
                if c.category_id == category_id:
                    found = True
                    break
            if found:
                tmp.append(p)
        results = tmp

    if supplier_id:
        tmp = []
        for p in results:
            if p.supplier_id == supplier_id:
                tmp.append(p)
        results = tmp

    return results
