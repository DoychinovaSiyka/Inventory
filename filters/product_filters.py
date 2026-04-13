from typing import List, Optional
from models.product import Product

#  BASIC SEARCH
def filter_search(products: List[Product], keyword: str) -> List[Product]:
    keyword = (keyword or "").lower().strip()
    if not keyword:
        return []

    results = []
    for p in products:
        if keyword in p.name.lower() or keyword in (p.description or "").lower():
            results.append(p)
            continue

        for c in p.categories:
            if keyword in c.name.lower():
                results.append(p)
                break

    return results


#  CATEGORY FILTERS
def filter_by_category(products: List[Product], category_id: str) -> List[Product]:
    return [p for p in products
            if any(str(getattr(c, "category_id", c)) == str(category_id) for c in p.categories)]

def filter_by_multiple_category_ids(products: List[Product], category_ids: List[str]) -> List[Product]:
    target_ids = [str(cid) for cid in category_ids]
    filtered = []

    for p in products:
        for c in p.categories:
            c_id = getattr(c, "category_id", c)
            if str(c_id) in target_ids:
                filtered.append(p)
                break

    return filtered


#  SUPPLIER FILTER
def filter_by_supplier(products: List[Product], supplier_id: str) -> List[Product]:
    return [p for p in products if str(p.supplier_id) == str(supplier_id)]


#  PRICE FILTERS
def filter_by_price_range(products: List[Product],
                          min_price: Optional[float],
                          max_price: Optional[float]) -> List[Product]:

    results = products
    if min_price is not None:
        results = [p for p in results if p.price >= min_price]
    if max_price is not None:
        results = [p for p in results if p.price <= max_price]

    return results


#  QUANTITY FILTERS
def filter_by_quantity_range(products: List[Product],
                             min_qty: Optional[float],
                             max_qty: Optional[float]) -> List[Product]:

    results = products
    if min_qty is not None:
        results = [p for p in results if p.quantity >= min_qty]
    if max_qty is not None:
        results = [p for p in results if p.quantity <= max_qty]

    return results


def filter_low_stock(products: List[Product], threshold: float = 5) -> List[Product]:
    return [p for p in products if p.quantity < threshold]



#  WAREHOUSE LOOKUP
def filter_warehouses(products: List[Product], product_name: str) -> List[str]:
    product_name = product_name.lower()
    warehouses = []

    for p in products:
        if p.name.lower() == product_name and p.quantity > 0:
            loc_id = p.location_id
            if loc_id and loc_id not in warehouses:
                warehouses.append(loc_id)

    return warehouses


#  COMBINED SEARCH
def filter_combined(products: List[Product],
                    name_keyword: Optional[str] = None,
                    category_id: Optional[str] = None,
                    min_price: Optional[float] = None,
                    max_price: Optional[float] = None,
                    min_qty: Optional[float] = None,
                    max_qty: Optional[float] = None,
                    supplier_id: Optional[str] = None) -> List[Product]:

    results = products

    # keyword
    if name_keyword:
        kw = name_keyword.lower()
        results = [p for p in results if kw in p.name.lower() or kw in (p.description or "").lower()]

    # category
    if category_id is not None:
        filtered = []
        for p in results:
            for c in p.categories:
                c_id = getattr(c, "category_id", c)
                if str(c_id) == str(category_id):
                    filtered.append(p)
                    break
        results = filtered


    if supplier_id is not None:
        results = [p for p in results if str(p.supplier_id) == str(supplier_id)]

    if min_price is not None:
        results = [p for p in results if p.price >= min_price]
    if max_price is not None:
        results = [p for p in results if p.price <= max_price]

    if min_qty is not None:
        results = [p for p in results if p.quantity >= min_qty]
    if max_qty is not None:
        results = [p for p in results if p.quantity <= max_qty]

    return results
