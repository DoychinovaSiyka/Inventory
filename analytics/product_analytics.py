from typing import List, Optional, Dict
from models.product import Product


def calculate_average_price(products: List[Product]) -> float:
    """Връща средната цена на продуктите."""
    if not products:
        return 0.0
    total = sum(p.price for p in products)
    return round(total / len(products), 2)


def calculate_total_inventory_value(products: List[Product], inventory_controller=None) -> float:
    """Изчислява общата стойност на целия склад."""
    if inventory_controller is None or not products:
        return 0.0

    total = 0.0
    for p in products:
        stock = inventory_controller.get_total_stock(p.product_id)
        total += p.price * stock

    return round(total, 2)


def get_most_expensive_product(products: List[Product]) -> Optional[Product]:
    """Намирам най-скъпия продукт."""
    if not products:
        return None
    return max(products, key=lambda p: p.price)


def get_cheapest_product(products: List[Product]) -> Optional[Product]:
    if not products:
        return None
    return min(products, key=lambda p: p.price)


def group_products_by_category(products: List[Product]) -> Dict[str, List[Product]]:
    """ Групирам продуктите по име на категорията. Работи с Category обекти."""
    grouped = {}
    for p in products:
        for c in p.categories:
            cname = c.name
            if cname not in grouped:
                grouped[cname] = []

            grouped[cname].append(p)

    return grouped
