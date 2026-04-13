from typing import List, Optional
from models.invoice import Invoice
from datetime import datetime


#  Търсене по клиент
def filter_by_customer(invoices: List[Invoice], keyword: str) -> List[Invoice]:
    keyword = (keyword or "").lower().strip()
    return [inv for inv in invoices if keyword in inv.customer.lower()]


#  Търсене по продукт
def filter_by_product(invoices: List[Invoice], keyword: str) -> List[Invoice]:
    keyword = (keyword or "").lower().strip()
    return [inv for inv in invoices if keyword in inv.product.lower()]


#  Търсене по дата (начало на датата)
def filter_by_date(invoices: List[Invoice], date_str: str) -> List[Invoice]:
    return [inv for inv in invoices if inv.date.startswith(date_str)]


#  Филтър по обща цена
def filter_by_total_range(invoices: List[Invoice],
                          min_value: Optional[float],
                          max_value: Optional[float]) -> List[Invoice]:

    results = invoices

    if min_value is not None:
        results = [inv for inv in results if inv.total_price >= float(min_value)]

    if max_value is not None:
        results = [inv for inv in results if inv.total_price <= float(max_value)]

    return results


#  Филтър по дата диапазон
def filter_by_date_range(invoices: List[Invoice],
                         start_date: Optional[str],
                         end_date: Optional[str]) -> List[Invoice]:

    if not start_date and not end_date:
        return invoices

    def parse(d):
        return datetime.strptime(d, "%Y-%m-%d %H:%M:%S")

    filtered = []
    for inv in invoices:
        inv_date = parse(inv.date)

        if start_date and inv_date < parse(start_date):
            continue
        if end_date and inv_date > parse(end_date):
            continue

        filtered.append(inv)

    return filtered


#  Комбиниран филтър (advanced_search)
def filter_advanced(invoices: List[Invoice],
                    customer: Optional[str] = None,
                    product: Optional[str] = None,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    min_total: Optional[float] = None,
                    max_total: Optional[float] = None):

    results = invoices

    if customer:
        results = filter_by_customer(results, customer)

    if product:
        results = filter_by_product(results, product)

    results = filter_by_date_range(results, start_date, end_date)
    results = filter_by_total_range(results, min_total, max_total)

    return results
