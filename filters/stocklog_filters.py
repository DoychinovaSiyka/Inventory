from typing import List
from models.stock_log import StockLog


def filter_by_location(logs: List[StockLog], location_id: str) -> List[StockLog]:
    return [log for log in logs if str(log.location_id) == str(location_id)]


def filter_by_product(logs: List[StockLog], product_id: str) -> List[StockLog]:
    return [log for log in logs if str(log.product_id) == str(product_id)]


def filter_search(logs: List[StockLog], keyword: str) -> List[StockLog]:
    keyword = (keyword or "").lower().strip()
    return [log for log in logs
            if keyword in log.action.lower() or keyword in log.timestamp.lower()]
