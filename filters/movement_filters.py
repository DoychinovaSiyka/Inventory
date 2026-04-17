from typing import List, Optional
from models.movement import Movement, MovementType
from datetime import datetime


def _parse_movement_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def filter_by_description(movements: List[Movement], keyword: str) -> List[Movement]:
    keyword = (keyword or "").lower().strip()
    return [m for m in movements if keyword in (m.description or "").lower()]


# Филтър за доставки използва се в search_delivery
def filter_deliveries(movements: List[Movement], keyword: str, product_controller, supplier_controller) -> List[
    Movement]:
    keyword = (keyword or "").lower().strip()
    if not keyword:
        return [m for m in movements if m.movement_type == MovementType.IN]

    results = []
    for m in movements:
        if m.movement_type != MovementType.IN:
            continue
        # 1. Търсене по ID на движение
        if keyword in str(m.movement_id).lower():
            results.append(m)
            continue
        # 2. Търсене по име на продукт - чрез ProductController
        product = product_controller.get_by_id(m.product_id)
        if product and keyword in product.name.lower():
            results.append(m)
            continue
        # 3. Търсене по име на доставчик - чрез SupplierController
        if m.supplier_id and supplier_controller:
            supplier = supplier_controller.get_by_id(m.supplier_id)
            if supplier and keyword in supplier.name.lower():
                results.append(m)
                continue
    return results


# Филтър по дата диапазон
def filter_by_date_range(movements: List[Movement],
                         start_date: Optional[str],
                         end_date: Optional[str]) -> List[Movement]:
    if not start_date and not end_date:
        return movements
    start = _parse_movement_date(start_date) if start_date else None
    end = _parse_movement_date(end_date) if end_date else None
    filtered = []
    for m in movements:
        m_date = _parse_movement_date(m.date)
        if not m_date:
            continue
        if start and m_date < start:
            continue
        if end:
            # Ако е подадена само дата (10 символа), включваме целия ден
            if len(end_date.strip()) <= 10:
                if m_date.date() > end.date():
                    continue
            elif m_date > end:
                continue
        filtered.append(m)
    return filtered


# Комбиниран филтър (advanced_filter)
def filter_advanced(movements: List[Movement],
                    movement_type=None, start_date=None,
                    end_date=None, product_id=None,
                    location_id=None, user_id=None):
    results = movements

    if movement_type:
        # Приемаме както Enum, така и String за по-голяма гъвкавост
        type_name = movement_type.name if isinstance(movement_type, MovementType) else str(movement_type)
        results = [m for m in results if m.movement_type.name == type_name]

    if start_date or end_date:
        results = filter_by_date_range(results, start_date, end_date)
    if product_id:
        results = [m for m in results if str(m.product_id) == str(product_id)]
    if location_id:
        results = [m for m in results if str(m.location_id) == str(location_id)]
    if user_id:
        results = [m for m in results if str(m.user_id) == str(user_id)]

    return results

    # ================== ТЪРСЕНЕ И ФИЛТРИРАНЕ ==================

    def search_by_description(self, keyword: str) -> List[Movement]:
        """Търси движения, чието описание съдържа ключовата дума."""
        keyword = keyword.lower()
        return [
            m for m in self.movements
            if keyword in m.description.lower()
        ]

    def advanced_filter(self, movement_type=None, start_date=None, end_date=None,
                        product_id=None, location_id=None, user_id=None) -> List[Movement]:
        """
        Разширено филтриране по много критерии (Логика "И").
        Ако даден параметър е None, той се игнорира.
        """
        results = self.movements

        if movement_type:
            results = [m for m in results if m.movement_type.name == movement_type]

        if product_id:
            results = [m for m in results if m.product_id == product_id]

        if location_id:
            results = [m for m in results if m.location_id == location_id]

        if user_id:
            results = [m for m in results if m.user_id == user_id]

        if start_date:
            results = [m for m in results if m.date >= start_date]

        if end_date:
            results = [m for m in results if m.date <= end_date]

        return results