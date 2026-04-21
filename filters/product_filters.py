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
        # категории
        for c in categories:
            c_name = c.name.lower() if hasattr(c, "name") else str(c).lower()
            if keyword in c_name:
                results.append(p)
                break
        for t in tags:
            if keyword in t.lower():
                results.append(p)
                break

        # доставчик (по ID)
        if supplier_id and keyword in supplier_id:
            results.append(p)

    return results



def filter_by_category(products: List[Product], category_id: str) -> List[Product]:
    category_id = str(category_id)
    return [p for p in products if any(str(c.category_id) == category_id for c in (p.categories or []))]


def filter_by_multiple_category_ids(products: List[Product], category_ids: List[str]) -> List[Product]:
    target_ids = set(str(cid) for cid in category_ids)
    filtered = []
    for p in products:
        for c in (p.categories or []):
            if str(c.category_id) in target_ids:
                filtered.append(p)
                break

    return filtered



def filter_by_supplier(products: List[Product], supplier_id: str) -> List[Product]:
    supplier_id = str(supplier_id)
    return [p for p in products if str(p.supplier_id) == supplier_id]


def filter_by_price_range(products: List[Product],
                          min_price: Optional[float],
                          max_price: Optional[float]) -> List[Product]:

    results = [p for p in products if p.price is not None]
    if min_price is not None:
        results = [p for p in results if p.price >= min_price]
    if max_price is not None:
        results = [p for p in results if p.price <= max_price]

    return results



def filter_by_quantity_range(products: List[Product],
                             min_qty: Optional[float],
                             max_qty: Optional[float]) -> List[Product]:

    results = [p for p in products if p.quantity is not None]
    if min_qty is not None:
        results = [p for p in results if p.quantity >= min_qty]
    if max_qty is not None:
        results = [p for p in results if p.quantity <= max_qty]

    return results

def filter_low_stock(products, threshold, inventory_controller=None):
    """Връща продуктите, които са паднали под зададения минимум.
    Количествата не са в Product, а идват от inventory.json."""

    if inventory_controller is None:
        return []

    low = []
    for p in products:
        stock = inventory_controller.get_total_stock(p.product_id)
        if stock < threshold:
            low.append(p)

    return low

# Проверки и търсене на складове
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


# Комбинирано търсене по няколко критерия
def filter_combined(products, inventory_controller, keyword=None,
                    min_price=None, max_price=None, min_quantity=None,
                    max_quantity=None, category_id=None, supplier_id=None, location_id=None):

    results = products

    # Ключова дума
    if keyword:
        kw = keyword.lower()
        results = [p for p in results
                   if kw in p.name.lower()
                   or kw in p.description.lower()]

    # Цена
    if min_price is not None:
        results = [p for p in results if p.price >= min_price]

    if max_price is not None:
        results = [p for p in results if p.price <= max_price]

    # Количество - от инвентара
    if min_quantity is not None or max_quantity is not None:
        filtered = []
        for p in results:
            total = inventory_controller.get_total_stock(p.product_id)
            if min_quantity is not None and total < min_quantity:
                continue
            if max_quantity is not None and total > max_quantity:
                continue
            filtered.append(p)
        results = filtered


    if category_id:
        results = [p for p in results
                   if any(c.category_id == category_id for c in p.categories)]


    if supplier_id:
        results = [p for p in results if p.supplier_id == supplier_id]


    if location_id:
        results = [p for p in results if p.location_id == location_id]

    return results
