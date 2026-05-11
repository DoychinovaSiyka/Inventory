from typing import List, Optional, Dict


def calculate_average_price(products: List) -> float:
    if not products:
        return 0.0
    total = sum(p.price for p in products)
    return round(total / len(products), 2)



def calculate_total_inventory_value(products: List, inventory_controller) -> float:
    if not products or not inventory_controller:
        return 0.0
    total = 0.0
    for p in products:
        stock = inventory_controller.get_total_stock(p.product_id)
        total += p.price * stock
    return round(total, 2)



def group_products_by_category(products: List) -> Dict[str, List]:
    """Групира продукти по име на категория."""
    grouped = {}

    for p in products:
        if not p.categories:
            if "Без категория" not in grouped:
                grouped["Без категория"] = []
            grouped["Без категория"].append(p)
            continue


        for cat in p.categories:
            try:
                cname = cat.name
            except Exception:
                cname = "ID: " + str(cat)

            if cname not in grouped:
                grouped[cname] = []

            grouped[cname].append(p)

    return grouped
