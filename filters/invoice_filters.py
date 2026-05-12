from typing import List
from models.invoice import Invoice




def filter_by_active_status(invoices: List[Invoice], is_active: bool = True) -> List[Invoice]:
    """Филтрира фактурите по статус (активни или анулирани)."""
    return [inv for inv in invoices if inv.is_active == is_active]