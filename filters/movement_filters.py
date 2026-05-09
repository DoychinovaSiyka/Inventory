from typing import List, Optional
from models.movement import Movement, MovementType
from datetime import datetime


def _parse_movement_date(date_val) -> Optional[datetime]:
    """Парсва дата от обект или стринг."""
    if not date_val:
        return None
    if isinstance(date_val, datetime):
        return date_val

    date_str = str(date_val).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def filter_deliveries(movements: List[Movement], keyword: str,
                      product_controller, supplier_controller) -> List[Movement]:
    """Филтър за доставки (IN) по име на продукт или доставчик."""
    keyword = (keyword or "").lower().strip()
    if not keyword:
        return [m for m in movements if m.movement_type == MovementType.IN]

    results = []
    for m in movements:
        if m.movement_type != MovementType.IN:
            continue

        if keyword in str(m.movement_id).lower():
            results.append(m)
            continue

        product = product_controller.get_by_id(m.product_id)
        if product and keyword in product.name.lower():
            results.append(m)
            continue

        if m.supplier_id and supplier_controller:
            supplier = supplier_controller.get_by_id(m.supplier_id)
            if supplier and keyword in supplier.name.lower():
                results.append(m)
                continue
    return results


def filter_advanced(movements: List[Movement], movement_type=None, start_date=None,
                    end_date=None, product_id=None, location_id=None, user_id=None):
    """Главен филтър за движения с поддръжка на всички критерии."""
    results = []

    for m in movements:
        m_date = _parse_movement_date(m.date)

        # Тип движение
        if movement_type:
            type_name = movement_type.name if hasattr(movement_type, 'name') else str(movement_type)
            if m.movement_type.name != type_name:
                continue

        # 2. Дати
        if start_date:
            s_date = _parse_movement_date(start_date)
            if m_date and m_date.date() < s_date.date():
                continue
        # Проверка за крайна дата
        if end_date:
            e_date = _parse_movement_date(end_date)
            if m_date and m_date.date() > e_date.date():
                continue


        if product_id and str(m.product_id) != str(product_id):
            continue


        if user_id and str(m.user_id) != str(user_id):
            continue

        # проверка за MOVE
        if location_id:
            loc_id = str(location_id)
            if m.movement_type.name == "MOVE":
                if m.from_location_id != loc_id and m.to_location_id != loc_id:
                    continue
            else:
                if m.location_id != loc_id:
                    continue

        results.append(m)
    return results