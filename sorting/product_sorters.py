from typing import List, Callable, Any
from models.product import Product


def sort_by_name_logic(products: List[Product]) -> List[Product]:
    """Сортирам по име – директно върху оригиналния списък."""
    products.sort(key=lambda p: p.name.lower())
    return products

def sort_by_price_desc_logic(products: List[Product]) -> List[Product]:
    """Правя нов списък, подреден по цена - от най-скъпите надолу."""
    return sorted(products, key=lambda p: p.price, reverse=True)

def bubble_sort_logic(products: List[Product], key: Callable, reverse: bool) -> List[Product]:
    """Bubble sort – сравнявам съседни елементи и разменям, ако трябва."""
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
    """Selection sort – търся най-подходящия елемент и го местя отпред."""
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
