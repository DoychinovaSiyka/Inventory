from typing import List, Callable



def bubble_sort(products: List, key: Callable, reverse: bool) -> List:
    arr = products[:]
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            val_a = key(arr[j])
            val_b = key(arr[j + 1])
            if (reverse and val_a < val_b) or (not reverse and val_a > val_b):
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr



def selection_sort(products: List, key: Callable, reverse: bool) -> List:
    arr = products[:]
    n = len(arr)
    for i in range(n):
        min_index = i
        for j in range(i + 1, n):
            val_j = key(arr[j])
            val_best = key(arr[min_index])
            if (reverse and val_j > val_best) or (not reverse and val_j < val_best):
                min_index = j
        arr[i], arr[min_index] = arr[min_index], arr[i]
    return arr