from typing import List, Dict
from models.movement import Movement
from models.invoice import Invoice


def _match_string(target: str, keyword: str) -> bool:
    if not keyword:
        return True
    return keyword.lower().strip() in (target or "").lower()


def _match_date(date_val: str, date_str: str) -> bool:
    """Помощна функция за филтриране по дата."""
    if not date_str:
        return True
    return str(date_val).startswith(date_str.strip())


def filter_movements_by_product(movements: List[Movement], product_controller, keyword: str):
    """Филтрира движенията по име на продукт през неговия контролер."""
    result = []
    for m in movements:
        product = product_controller.get_by_id(m.product_id)
        if product and _match_string(product.name, keyword):
            result.append(m)
    return result


def filter_movements_by_type(movements: List[Movement], m_type: str):
    """Филтър по тип движение – IN, OUT или MOVE."""
    return [m for m in movements if m.movement_type.name == m_type.upper()]


def filter_sales_by_customer(invoices: List[Invoice], keyword: str):
    """Търсене на продажби по име на клиент (само за активни фактури)."""
    # СИНХРОН: Първо филтрираме само активните
    active_invoices = [inv for inv in invoices if inv.is_active]

    if not keyword or len(keyword.strip()) < 2:
        return active_invoices

    return [inv for inv in active_invoices if _match_string(inv.customer, keyword)]


def filter_sales_by_product(invoices: List[Invoice], product_name: str):
    """Търсене на продажби по име на продукт (само за активни фактури)."""
    active_invoices = [inv for inv in invoices if inv.is_active]
    return [inv for inv in active_invoices if _match_string(inv.product, product_name)]


def group_turnover_by_day(invoices: List[Invoice]):
    """Групира оборота по дни за статистически справки."""
    turnover = {}
    # СИНХРОН: Гледаме само активните фактури, за да не товарим оборота с анулирани суми
    active_invoices = [inv for inv in invoices if inv.is_active]

    for inv in active_invoices:
        date_only = str(inv.date).split(" ")[0]
        try:
            total = float(inv.total_price)
        except:
            total = 0.0

        entry = turnover.setdefault(date_only, {"total": 0.0, "count": 0})
        entry["total"] += total
        entry["count"] += 1

    return [{"date": d, "total": round(v["total"], 2), "count": v["count"]}
            for d, v in turnover.items()]


def group_top_products(invoices: List[Invoice]):
    """Статистика за най-продаваните продукти (само от валидни продажби)."""
    stats = {}
    # СИНХРОН: Анулирана фактура означава върната стока, затова не я броим тук
    active_invoices = [inv for inv in invoices if inv.is_active]

    for inv in active_invoices:
        name = inv.product
        if name not in stats:
            stats[name] = {"qty": 0.0, "total": 0.0}
        try:
            stats[name]["qty"] += float(inv.quantity)
            stats[name]["total"] += float(inv.total_price)
        except:
            continue

    return [{"product": p, "quantity": round(v["qty"], 2),
             "total": round(v["total"], 2)} for p, v in stats.items()]