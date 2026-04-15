from typing import List, Optional
from models.invoice import Invoice
from datetime import datetime


# Помощна функция за безопасно парсване на дати в различни формати
def _parse_invoice_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


# Търсене по клиент
def filter_by_customer(invoices: List[Invoice], keyword: str) -> List[Invoice]:
    if not keyword:
        return invoices
    keyword = keyword.lower().strip()
    return [inv for inv in invoices if keyword in inv.customer.lower()]


def filter_by_product(invoices: List[Invoice], keyword: str) -> List[Invoice]:
    if not keyword:
        return invoices
    keyword = keyword.lower().strip()
    return [inv for inv in invoices if keyword in inv.product.lower()]


# Търсене по дата (просто съвпадение на текст в началото)
def filter_by_date(invoices: List[Invoice], date_str: str) -> List[Invoice]:
    if not date_str:
        return invoices
    date_str = date_str.strip()
    return [inv for inv in invoices if inv.date.startswith(date_str)]


# Филтър по обща цена
def filter_by_total_range(invoices: List[Invoice],
                          min_value: Optional[float],
                          max_value: Optional[float]) -> List[Invoice]:
    results = invoices
    if min_value is not None:
        results = [inv for inv in results if inv.total_price >= float(min_value)]
    if max_value is not None:
        results = [inv for inv in results if inv.total_price <= float(max_value)]
    return results


# Филтър по дата диапазон
def filter_by_date_range(invoices: List[Invoice],
                         start_date: Optional[str],
                         end_date: Optional[str]) -> List[Invoice]:
    if not start_date and not end_date:
        return invoices

    start = _parse_invoice_date(start_date) if start_date else None
    end = _parse_invoice_date(end_date) if end_date else None
    filtered = []
    for inv in invoices:
        inv_date = _parse_invoice_date(inv.date)
        if not inv_date:
            continue
        if start and inv_date < start:
            continue
        # Ако end_date е само ден (напр. 2023-10-10), да включим целия ден до 23:59:59
        if end:
            # Ако end е подаден без час, го вдигам до края на деня за коректно сравнение
            if len(end_date.strip()) <= 10:
                inv_date_only = inv_date.replace(hour=0, minute=0, second=0, microsecond=0)
                if inv_date_only > end:
                    continue
            elif inv_date > end:
                continue

        filtered.append(inv)
    return filtered


# Комбиниран филтър - advanced_search
def filter_advanced(invoices: List[Invoice],
                    customer: Optional[str] = None,
                    product: Optional[str] = None,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    min_total: Optional[float] = None,
                    max_total: Optional[float] = None) -> List[Invoice]:

    results = invoices
    if customer:
        results = filter_by_customer(results, customer)
    if product:
        results = filter_by_product(results, product)

    results = filter_by_date_range(results, start_date, end_date)
    results = filter_by_total_range(results, min_total, max_total)

    return results