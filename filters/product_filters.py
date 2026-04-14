from typing import List, Optional
from models.product import Product

# BASIC SEARCH
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

        # категории
        for c in categories:
            c_name = c.name.lower() if hasattr(c, "name") else str(c).lower()
            if keyword in c_name:
                results.append(p)
                break

        # тагове
        for t in tags:
            if keyword in t.lower():
                results.append(p)
                break

        # доставчик (по ID)
        if supplier_id and keyword in supplier_id:
            results.append(p)

    return results


# CATEGORY FILTERS
def filter_by_category(products: List[Product], category_id: str) -> List[Product]:
    category_id = str(category_id)
    return [
        p for p in products
        if any(str(c.category_id) == category_id for c in (p.categories or []))
    ]


def filter_by_multiple_category_ids(products: List[Product], category_ids: List[str]) -> List[Product]:
    target_ids = set(str(cid) for cid in category_ids)
    filtered = []

    for p in products:
        for c in (p.categories or []):
            if str(c.category_id) in target_ids:
                filtered.append(p)
                break

    return filtered


# SUPPLIER FILTER
def filter_by_supplier(products: List[Product], supplier_id: str) -> List[Product]:
    supplier_id = str(supplier_id)
    return [p for p in products if str(p.supplier_id) == supplier_id]


# PRICE FILTERS
def filter_by_price_range(products: List[Product],
                          min_price: Optional[float],
                          max_price: Optional[float]) -> List[Product]:

    results = [p for p in products if p.price is not None]

    if min_price is not None:
        results = [p for p in results if p.price >= min_price]
    if max_price is not None:
        results = [p for p in results if p.price <= max_price]

    return results


# QUANTITY FILTERS
def filter_by_quantity_range(products: List[Product],
                             min_qty: Optional[float],
                             max_qty: Optional[float]) -> List[Product]:

    results = [p for p in products if p.quantity is not None]

    if min_qty is not None:
        results = [p for p in results if p.quantity >= min_qty]
    if max_qty is not None:
        results = [p for p in results if p.quantity <= max_qty]

    return results


def filter_low_stock(products: List[Product], threshold: float = 5) -> List[Product]:
    return [p for p in products if p.quantity is not None and p.quantity < threshold]


# WAREHOUSE LOOKUP
def filter_warehouses(products: List[Product], product_name: str) -> List[str]:
    product_name = product_name.lower()
    warehouses = []

    for p in products:
        if not p.name or p.quantity is None:
            continue

        if p.name.lower() == product_name and p.quantity > 0:
            if p.location_id and p.location_id not in warehouses:
                warehouses.append(p.location_id)

    return warehouses


# COMBINED SEARCH (ОПРАВЕНА ВЕРСИЯ)
def filter_combined(products: List[Product],
                    name_keyword: Optional[str] = None,
                    category_id: Optional[str] = None,
                    min_price: Optional[float] = None,
                    max_price: Optional[float] = None,
                    min_qty: Optional[float] = None,
                    max_qty: Optional[float] = None,
                    supplier_id: Optional[str] = None) -> List[Product]:

    results = [p for p in products if p.name]

    # ключова дума → име + описание + категории + тагове
    if name_keyword:
        kw = name_keyword.lower().strip()
        filtered = []

        for p in results:
            name = p.name.lower()
            description = (p.description or "").lower()
            categories = p.categories or []
            tags = p.tags or []

            match = False

            if kw in name or kw in description:
                match = True

            for c in categories:
                if kw in c.name.lower():
                    match = True
                    break

            for t in tags:
                if kw in t.lower():
                    match = True
                    break

            if match:
                filtered.append(p)

        results = filtered

    # категория
    if category_id is not None:
        cid = str(category_id)
        results = [
            p for p in results
            if any(str(c.category_id) == cid for c in (p.categories or []))
        ]

    # доставчик
    if supplier_id is not None:
        sid = str(supplier_id)
        results = [p for p in results if str(p.supplier_id) == sid]

    # цена
    if min_price is not None:
        results = [p for p in results if p.price is not None and p.price >= min_price]
    if max_price is not None:
        results = [p for p in results if p.price is not None and p.price <= max_price]

    # количество
    if min_qty is not None:
        results = [p for p in results if p.quantity is not None and p.quantity >= min_qty]
    if max_qty is not None:
        results = [p for p in results if p.quantity is not None and p.quantity <= max_qty]

    return results
