from typing import List, Dict
from models.movement import Movement
from models.invoice import Invoice


def _match_string(target: str, keyword: str) -> bool:
    if not keyword:
        return True
    return keyword.lower().strip() in (target or "").lower()




def filter_movements_by_type(movements: List[Movement], m_type: str):
    """Филтър по тип движение – IN, OUT или MOVE."""
    return [m for m in movements if m.movement_type.name == m_type.upper()]







