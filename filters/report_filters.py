from typing import List
from models.movement import Movement
from models.invoice import Invoice


#  Филтър: само OUT фактури
def filter_out_invoices(invoices: List[Invoice], movements: List[Movement]) -> List[Invoice]:
    out_list = []
    movement_map = {m.movement_id: m for m in movements}

    for inv in invoices:
        m = movement_map.get(inv.movement_id)
        if m and m.movement_type.name == "OUT":
            out_list.append(inv)

    return out_list

#  Движения по продукт
def filter_movements_by_product(movements: List[Movement], product_controller, keyword: str):
    keyword = keyword.lower()
    result = []

    for m in movements:
        product = product_controller.get_by_id(m.product_id)
        if product and keyword in product.name.lower():
            result.append(m)

    return result


#  Движения по тип
def filter_movements_by_type(movements: List[Movement], movement_type: str):
    movement_type = movement_type.upper()
    return [m for m in movements if m.movement_type.name == movement_type]


#  Движения по дата
def filter_movements_by_date(movements: List[Movement], date_str: str):
    return [m for m in movements if m.date.startswith(date_str)]


#  Продажби по клиент
def filter_sales_by_customer(invoices, keyword):
    keyword = keyword.strip().lower()

    # Минимум 3 букви за да избегнем грешни съвпадения
    if len(keyword) < 3:
        return []

    return [
        inv for inv in invoices
        if keyword in inv.customer.lower()
    ]

#  Продажби по продукт
def filter_sales_by_product(invoices: List[Invoice], product: str):
    product = product.lower()
    return [inv for inv in invoices if product in inv.product.lower()]


#  Продажби по дата
def filter_sales_by_date(invoices: List[Invoice], date_str: str):
    return [inv for inv in invoices if inv.date.startswith(date_str)]
