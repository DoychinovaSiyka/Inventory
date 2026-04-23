from typing import List, Dict
from models.movement import Movement
from models.invoice import Invoice


# Малки помощни функции за вътрешно ползване
def _match_string(target: str, keyword: str) -> bool:
    """Правя търсенето по-унифицирано – малки букви, без излишни интервали."""
    if not keyword:
        return True
    return keyword.lower().strip() in (target or "").lower()


def _match_date(date_val: str, date_str: str) -> bool:
    """Базова проверка за дата – просто сравнявам началото на стринга."""
    if not date_str:
        return True
    return date_val.startswith(date_str.strip())


# Филтри за фактури и движения
def filter_out_invoices(invoices: List[Invoice], movements: List[Movement]) -> List[Invoice]:
    """Връща само фактурите, които са свързани с OUT движения."""
    movement_map = {m.movement_id: m for m in movements}
    return [inv for inv in invoices
            if (m := movement_map.get(inv.movement_id))
            and m.movement_type.name == "OUT"]


def filter_movements_by_product(movements: List[Movement], product_controller, keyword: str):
    """Филтрирам движенията по име на продукт."""
    result = []
    for m in movements:
        product = product_controller.get_by_id(m.product_id)
        if product and _match_string(product.name, keyword):
            result.append(m)
    return result


def filter_movements_by_type(movements: List[Movement], movement_type: str):
    """Филтър по тип движение – IN, OUT или MOVE."""
    return [m for m in movements if m.movement_type.name == movement_type.upper()]


def filter_movements_by_date(movements: List[Movement], date_str: str):
    """Филтър по дата – просто проверявам дали започва с подадения текст."""
    return [m for m in movements if _match_date(m.date, date_str)]


# Филтри за продажби
def filter_sales_by_customer(invoices: List[Invoice], keyword: str):
    """Търсене на продажби по клиент. Изисквам поне 3 символа, за да има смисъл."""
    if len(keyword.strip()) < 3:
        return []
    return [inv for inv in invoices if _match_string(inv.customer, keyword)]


def filter_sales_by_product(invoices: List[Invoice], product_name: str):
    return [inv for inv in invoices if _match_string(inv.product, product_name)]


def filter_sales_by_date(invoices: List[Invoice], date_str: str):
    """Филтър по дата на фактурата."""
    return [inv for inv in invoices if _match_date(inv.date, date_str)]


# Групиране за справки
def group_turnover_by_day(invoices: List[Invoice]):
    """Групирам оборота по дни – колко продажби и каква сума има за всеки ден."""
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
    """Правя статистика кои продукти се продават най-много."""
    stats = {}

    for inv in invoices:
        name = inv.product
        if name not in stats:
            stats[name] = {"qty": 0.0, "total": 0.0}

        stats[name]["qty"] += float(inv.quantity)
        stats[name]["total"] += float(inv.total_price)

    return [{"product": p, "quantity": round(v["qty"], 2), "total": round(v["total"], 2)}
            for p, v in stats.items()]
