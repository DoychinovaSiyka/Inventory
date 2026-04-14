from typing import List
from models.category import Category


def filter_categories(categories: List[Category], keyword: str) -> List[Category]:
    """Търси в списък от категории по име или описание.
    Връща списък с намерените резултати."""
    if not keyword:
        return categories

    keyword = keyword.lower()
    results = []

    for c in categories:
        # Проверяваме името
        name_match = keyword in c.name.lower()

        # Проверяваме описанието (ако съществува)
        desc_match = False
        if c.description:
            desc_match = keyword in c.description.lower()

        if name_match or desc_match:
            results.append(c)

    return results


def filter_by_parent(categories: List[Category], parent_id: str) -> List[Category]:
    """Връща само категориите, които са деца на конкретен родител."""
    return [c for c in categories if str(c.parent_id) == str(parent_id)]