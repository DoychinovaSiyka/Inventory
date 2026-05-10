from typing import List, Optional
from models.movement import Movement, MovementType
from datetime import datetime


def _parse_movement_date(date_val) -> Optional[datetime]:
    # Опитваме се да превърнем входа в дата.
    if not date_val:
        return None

    if isinstance(date_val, datetime):
        return date_val

    date_str = str(date_val).strip()

    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass

    return None


def filter_deliveries(movements: List[Movement], keyword: str, product_controller, supplier_controller) -> List[Movement]:
    # Филтър само за доставки (IN)
    if keyword:
        keyword = keyword.lower().strip()
    else:
        keyword = ""

    # Първо взимаме само IN движенията
    deliveries = []
    for m in movements:
        if m.movement_type == MovementType.IN:
            deliveries.append(m)

    # Ако няма ключова дума – връщаме всички доставки
    if keyword == "":
        return deliveries

    results = []

    for m in deliveries:
        # Проверка по име на продукт
        product_name = m.product_name or ""
        if keyword in product_name.lower():
            results.append(m)
            continue

        # Проверка по име на доставчик
        if m.supplier_id and supplier_controller:
            supplier = supplier_controller.get_by_id(m.supplier_id)
            if supplier:
                supplier_name = supplier.name.lower()
                if keyword in supplier_name:
                    results.append(m)
                    continue

    return results


def filter_advanced(movements: List[Movement], **kwargs):
    # Комбиниран филтър – проверява всички критерии един по един
    results = []

    m_type = kwargs.get("movement_type")
    start_date = kwargs.get("start_date")
    end_date = kwargs.get("end_date")
    product_id = kwargs.get("product_id")
    location_id = kwargs.get("location_id")
    user_id = kwargs.get("user_id")


    start_dt = _parse_movement_date(start_date)
    end_dt = _parse_movement_date(end_date)


    expected_type = None
    if m_type:
        if isinstance(m_type, MovementType):
            expected_type = m_type.name
        else:
            expected_type = str(m_type)

    for m in movements:

        # Филтър по тип движение
        if expected_type is not None:
            if m.movement_type.name != expected_type:
                continue

        movement_dt = _parse_movement_date(m.date)
        if start_dt is not None and movement_dt is not None:
            if movement_dt < start_dt:
                continue

        #  Филтър по дата (крайна)
        if end_dt is not None and movement_dt is not None:
            if movement_dt > end_dt:
                continue

        if product_id:
            if str(m.product_id) != str(product_id):
                continue

        if user_id:
            if str(m.user_id) != str(user_id):
                continue


        if location_id:
            wanted_loc = str(location_id)

            if m.movement_type == MovementType.MOVE:
                # При MOVE проверяваме и двете локации
                from_loc = str(m.from_location_id) if m.from_location_id else ""
                to_loc = str(m.to_location_id) if m.to_location_id else ""

                if wanted_loc != from_loc and wanted_loc != to_loc:
                    continue
            else:
                # При IN/OUT проверяваме само основната локация
                if str(m.location_id) != wanted_loc:
                    continue

        results.append(m)

    return results
