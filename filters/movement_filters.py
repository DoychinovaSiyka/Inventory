from typing import List, Optional
from models.movement import Movement, MovementType
from datetime import datetime



#  Търсене по описание
def filter_by_description(movements: List[Movement], keyword: str) -> List[Movement]:
    keyword = (keyword or "").lower().strip()
    return [m for m in movements if keyword in (m.description or "").lower()]

#  Филтър по тип движение
def filter_by_type(movements: List[Movement], movement_type: MovementType) -> List[Movement]:
    return [m for m in movements if m.movement_type == movement_type]

#  Филтър по продукт
def filter_by_product(movements: List[Movement], product_id: str) -> List[Movement]:
    return [m for m in movements if m.product_id == product_id]

#  Филтър по локация
def filter_by_location(movements: List[Movement], location_id: str) -> List[Movement]:
    return [m for m in movements if m.location_id == location_id]


#  Филтър по потребител
def filter_by_user(movements: List[Movement], user_id: str) -> List[Movement]:
    return [m for m in movements if m.user_id == user_id]



#  Филтър по дата
def filter_by_date_range(movements: List[Movement],
                         start_date: Optional[str],
                         end_date: Optional[str]) -> List[Movement]:

    if not start_date and not end_date:
        return movements

    def parse(d):
        return datetime.strptime(d, "%Y-%m-%d %H:%M:%S")

    filtered = []
    for m in movements:
        m_date = parse(m.date)

        if start_date and m_date < parse(start_date):
            continue
        if end_date and m_date > parse(end_date):
            continue

        filtered.append(m)

    return filtered


#  Комбиниран филтър (advanced_filter)
def filter_advanced(movements: List[Movement],
                    movement_type=None,
                    start_date=None,
                    end_date=None,
                    product_id=None,
                    location_id=None,
                    user_id=None):

    results = movements

    if movement_type:
        results = filter_by_type(results, movement_type)

    if start_date or end_date:
        results = filter_by_date_range(results, start_date, end_date)

    if product_id:
        results = filter_by_product(results, product_id)

    if location_id:
        results = filter_by_location(results, location_id)

    if user_id:
        results = filter_by_user(results, user_id)

    return results
