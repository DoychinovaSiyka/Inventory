from typing import List, Optional
from models.movement import Movement, MovementType
from datetime import datetime


def _parse_movement_date(date_val) -> Optional[datetime]:
    """Парсва дата безопасно – работи и с обекти, и със стрингове."""
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
    """ Филтър за доставки (IN). Търси по име на продукт (от записа) или име на доставчик (през неговия контролер)."""
    keyword = (keyword or "").lower().strip()

    # Вземаме само доставките
    in_movements = [m for m in movements if m.movement_type == MovementType.IN]

    if not keyword:
        return in_movements

    results = []
    for m in in_movements:
        if keyword in (m.product_name or "").lower():
            results.append(m)
            continue


        if m.supplier_id and supplier_controller:
            supplier = supplier_controller.get_by_id(m.supplier_id)
            if supplier and keyword in supplier.name.lower():
                results.append(m)
                continue
    return results


def filter_advanced(movements: List[Movement], **kwargs):
    """Главен комбиниран филтър. Поддържа всички критерии едновременно."""
    results = []

    m_type = kwargs.get("movement_type")
    start_date = kwargs.get("start_date")
    end_date = kwargs.get("end_date")
    product_id = kwargs.get("product_id")
    location_id = kwargs.get("location_id")
    user_id = kwargs.get("user_id")

    # Подготвяме датите за сравнение веднъж
    s_dt = _parse_movement_date(start_date)
    e_dt = _parse_movement_date(end_date)

    for m in movements:
        #  Филтър по тип (работи със стрингове или Enum обекти)
        if m_type:
            target_type = m_type.name if hasattr(m_type, 'name') else str(m_type)
            if m.movement_type.name != target_type:
                continue

        #  Филтър по дати (сравняваме datetime обекти)
        m_dt = _parse_movement_date(m.date)
        if s_dt and m_dt and m_dt < s_dt:
            continue
        if e_dt and m_dt and m_dt > e_dt:
            continue

        #  Филтър по Продукт или Потребител
        if product_id and str(m.product_id) != str(product_id):
            continue
        if user_id and str(m.user_id) != str(user_id):
            continue

        #  Филтър по Локация (обхваща и преместванията MOVE)
        if location_id:
            loc_id = str(location_id)
            if m.movement_type == MovementType.MOVE:
                # При MOVE проверяваме дали локацията е "ОТ" или "ДО"
                if m.from_location_id != loc_id and m.to_location_id != loc_id:
                    continue
            elif m.location_id != loc_id:
                continue

        results.append(m)
    return results