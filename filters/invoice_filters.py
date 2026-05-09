from typing import List, Optional
from models.invoice import Invoice
from datetime import datetime


def _parse_invoice_date(date_str: str) -> Optional[datetime]:
    """ Превръща текста в дата, за да можем да сравняваме периоди. """
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def filter_by_customer(invoices: List[Invoice], keyword: str) -> List[Invoice]:
    """Търси фактури по името на клиента по част от име."""

    if not keyword:
        return invoices

    keyword = str(keyword).strip()
    results = []

    for inv in invoices:
        customer_name = inv.customer or ""
        customer_name = customer_name.strip()

        if len(keyword) > len(customer_name):
            continue

        name_parts = customer_name.split()

        # Дали keyword се съдържа в която и да е част
        match_found = False
        for part in name_parts:
            if keyword in part:
                match_found = True
                break
        if match_found:
            results.append(inv)

    return results


def filter_by_product(invoices: List[Invoice], keyword: str) -> List[Invoice]:
    """ Филтрира фактурите по името на продадения продукт. """
    if not keyword:
        return invoices
    keyword = str(keyword).lower().strip()
    return [inv for inv in invoices if keyword in (inv.product or "").lower()]


def filter_by_date(invoices: List[Invoice], date_str: str) -> List[Invoice]:
    """ Бързо търсене на фактури от конкретен ден. """
    if not date_str:
        return invoices
    target = str(date_str).strip()
    return [inv for inv in invoices if str(inv.date).startswith(target)]


def filter_by_total_range(invoices: List[Invoice], min_v: Optional[float], max_v: Optional[float]) -> List[Invoice]:
    """ Търси фактури в диапазон на цената (например от 100 до 500 лв). """
    results = invoices
    if min_v is not None:
        results = [i for i in results if float(i.total_price) >= float(min_v)]
    if max_v is not None:
        results = [i for i in results if float(i.total_price) <= float(max_v)]
    return results


def filter_by_date_range(invoices: List[Invoice], start_str: Optional[str], end_str: Optional[str]) -> List[Invoice]:
    """ Търси фактури издадени между две дати. """
    if not start_str and not end_str:
        return invoices

    start_dt = _parse_invoice_date(start_str)
    end_dt = _parse_invoice_date(end_str)

    filtered = []
    for inv in invoices:
        inv_dt = _parse_invoice_date(inv.date)
        if not inv_dt:
            continue

        if start_dt and inv_dt < start_dt:
            continue
        if end_dt and inv_dt > end_dt:
            continue
        filtered.append(inv)
    return filtered


def filter_advanced(invoices: List[Invoice], **kwargs) -> List[Invoice]:
    """Комбинира всичко (клиент, продукт, дати и цени) в едно търсене. """
    res = invoices
    if kwargs.get("customer"):
        res = filter_by_customer(res, kwargs["customer"])
    if kwargs.get("product"):
        res = filter_by_product(res, kwargs["product"])

    if kwargs.get("start_date") or kwargs.get("end_date"):
        res = filter_by_date_range(res, kwargs.get("start_date"), kwargs.get("end_date"))

    if kwargs.get("min_total") is not None or kwargs.get("max_total") is not None:
        res = filter_by_total_range(res, kwargs.get("min_total"), kwargs.get("max_total"))

    return res