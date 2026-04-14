from typing import List, Optional, Dict
from models.product import Product

def calculate_average_price(products: List[Product]) -> float:
    """Изчислява средната цена на наличните продукти."""
    if not products:
        return 0.0
    total = sum(p.price for p in products)
    return total / len(products)

def calculate_total_inventory_value(products: List[Product]) -> float:
    """Изчислява общата стойност на целия инвентар (цена * количество)."""
    total = sum(p.price * p.quantity for p in products)
    return round(total, 2)

def get_most_expensive_product(products: List[Product]) -> Optional[Product]:
    """Намира най-скъпия продукт в списъка."""
    if not products:
        return None
    return max(products, key=lambda p: p.price)

def get_cheapest_product(products: List[Product]) -> Optional[Product]:
    if not products:
        return None
    return min(products, key=lambda p: p.price)

def group_products_by_category(products: List[Product]) -> Dict[str, List[Product]]:
    """Групира продуктите по ID на категорията им."""
    grouped = {}
    for p in products:
        for c in p.categories:
            cid = c.category_id
            if cid not in grouped:
                grouped[cid] = []
            grouped[cid].append(p)
    return grouped