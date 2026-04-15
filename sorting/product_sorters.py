from typing import List, Callable, Any
from models.product import Product


def sort_by_name_logic(products: List[Product]) -> List[Product]:
    """Сортира оригиналния списък по име (in-place)."""
    products.sort(key=lambda p: p.name.lower())
    return products

def sort_by_price_desc_logic(products: List[Product]) -> List[Product]:
    """Връща нов списък, сортиран по цена (низходящо)."""
    return sorted(products, key=lambda p: p.price, reverse=True)

def bubble_sort_logic(products: List[Product], key: Callable, reverse: bool) -> List[Product]:
    """Bubble Sort: Сравнява съседни елементи и ги разменя при нужда."""
    arr = products[:]
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            a, b = key(arr[j]), key(arr[j + 1])
            if reverse and a < b:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
            elif not reverse and a > b:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def selection_sort_logic(products: List[Product], key: Callable, reverse: bool) -> List[Product]:
    """Selection Sort: Намира най-добрия елемент и го поставя на текущата позиция."""
    arr = products[:]
    n = len(arr)
    i = 0
    while i < n:
        best = i
        j = i + 1
        while j < n:
            if reverse and key(arr[j]) > key(arr[best]):
                best = j
            elif not reverse and key(arr[j]) < key(arr[best]):
                best = j
            j += 1
        arr[i], arr[best] = arr[best], arr[i]
        i += 1
    return arr