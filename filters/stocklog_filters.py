from typing import List
from models.stock_log import StockLog


def filter_by_location(logs: List[StockLog], location_id: str) -> List[StockLog]:
    """ Филтрира логовете по склад. """
    target_id = str(location_id).strip()
    return [log for log in logs if str(log.location_id) == target_id]


def filter_by_product(logs: List[StockLog], product_id: str) -> List[StockLog]:
    """ Филтрира логовете по конкретен продукт. """
    target_id = str(product_id).strip()
    return [log for log in logs if str(log.product_id) == target_id]


def filter_search(logs: List[StockLog], keyword: str) -> List[StockLog]:
    """ Търси по ключова дума в действието или времето на записа. """
    if not keyword or not str(keyword).strip():
        return logs  # Ако няма ключова дума, връщаме всичко без излишни цикли

    clean_keyword = str(keyword).lower().strip()

    return [log for log in logs if clean_keyword in log.action.lower()
            or clean_keyword in log.timestamp.lower()]