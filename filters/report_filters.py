from typing import List, Dict
from models.movement import Movement
from models.invoice import Invoice


# Помощни вътрешни функции (за вътрешна употреба)

def _match_string(target: str, keyword: str) -> bool:
    """ Унифицирано търсене: малки букви и премахване на интервали. """
    if not keyword: return True
    return keyword.lower().strip() in (target or "").lower()


def _match_date(date_val: str, date_str: str) -> bool:
    """ Унифицирано филтриране по дата. """
    if not date_str: return True
    return date_val.startswith(date_str.strip())


# Филтри за Фактури и Движения
def filter_out_invoices(invoices: List[Invoice], movements: List[Movement]) -> List[Invoice]:
    """ Филтър: само OUT фактури чрез мапване на движенията. """
    movement_map = {m.movement_id: m for m in movements}
    return [inv for inv in invoices if (m := movement_map.get(inv.movement_id)) and m.movement_type.name == "OUT"]


def filter_movements_by_product(movements: List[Movement], product_controller, keyword: str):
    """ Движения по име на продукт. """
    result = []
    for m in movements:
        product = product_controller.get_by_id(m.product_id)
        if product and _match_string(product.name, keyword):
            result.append(m)
    return result


def filter_movements_by_type(movements: List[Movement], movement_type: str):
    """ Движения по тип (IN/OUT/MOVE). """
    return [m for m in movements if m.movement_type.name == movement_type.upper()]


def filter_movements_by_date(movements: List[Movement], date_str: str):
    """ Движения по дата (ГГГГ-ММ-ДД). """
    return [m for m in movements if _match_date(m.date, date_str)]


# Филтри за Продажби
def filter_sales_by_customer(invoices: List[Invoice], keyword: str):
    """ Продажби по клиент (мин. 3 символа). """
    if len(keyword.strip()) < 3: return []
    return [inv for inv in invoices if _match_string(inv.customer, keyword)]


def filter_sales_by_product(invoices: List[Invoice], product_name: str):
    """ Продажби по име на продукт. """
    return [inv for inv in invoices if _match_string(inv.product, product_name)]


def filter_sales_by_date(invoices: List[Invoice], date_str: str):
    return [inv for inv in invoices if _match_date(inv.date, date_str)]


#  Логика за Групиране - Справки
def group_turnover_by_day(invoices: List[Invoice]):
    """ Групира оборот по дни. """
    turnover = {}
    for inv in invoices:
        date_only = inv.date.split(" ")[0]
        total = float(inv.total_price)

        entry = turnover.setdefault(date_only, {"total": 0.0, "count": 0})
        entry["total"] += total
        entry["count"] += 1

    return [{"date": d, "total": round(v["total"], 2), "count": v["count"]}
            for d, v in turnover.items()]


def group_top_products(invoices: List[Invoice]):
    """ Групира статистика по продукти. """
    stats = {}
    for inv in invoices:
        name = inv.product
        if name not in stats:
            stats[name] = {"qty": 0.0, "total": 0.0}

        stats[name]["qty"] += float(inv.quantity)
        stats[name]["total"] += float(inv.total_price)

    return [{"product": p, "quantity": round(v["qty"], 2), "total": round(v["total"], 2)}
            for p, v in stats.items()]