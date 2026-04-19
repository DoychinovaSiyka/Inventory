from typing import List, Optional, Dict
from models.product import Product


def calculate_average_price(products: List[Product]) -> float:
    """Връща средната цена на продуктите. Ако списъкът е празен – 0."""
    if not products:
        return 0.0

    total = sum(p.price for p in products)
    return round(total / len(products), 2)


def calculate_total_inventory_value(products: List[Product],
                                    inventory_controller=None) -> float:
    """ Изчислявам общата стойност на склада. Количествата не са в Product,
    а в inventory.json, затова ги взимам от контролера."""
    if inventory_controller is None:
        return 0.0

    total = 0.0
    for p in products:
        stock = inventory_controller.get_total_stock(p.product_id)
        total += p.price * stock

    return round(total, 2)


def get_most_expensive_product(products: List[Product]) -> Optional[Product]:
    """Намирам най-скъпия продукт. Ако няма продукти – връщам None."""
    if not products:
        return None
    return max(products, key=lambda p: p.price)


def get_cheapest_product(products: List[Product]) -> Optional[Product]:
    """Намирам най-евтиния продукт. При празен списък – None."""
    if not products:
        return None
    return min(products, key=lambda p: p.price)


def group_products_by_category(products: List[Product]) -> Dict[str, List[Product]]:
    """ Групирам продуктите по име на категорията. Работи с Category обекти,
    не със стрингове."""
    grouped = {}
    for p in products:
        for c in p.categories:
            cname = c.name

            if cname not in grouped:
                grouped[cname] = []

            grouped[cname].append(p)

    return grouped
