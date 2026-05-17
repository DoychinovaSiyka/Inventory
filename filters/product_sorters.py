from typing import List, Callable



def quick_sort(products: List, key: Callable, reverse: bool) -> List:
    if len(products) <= 1:
        return products[:]

    pivot = products[len(products) // 2]
    pivot_val = key(pivot)

    left = []
    mid = []
    right = []


    for item in products:
        val = key(item)
        if val < pivot_val:
            left.append(item)
        elif val > pivot_val:
            right.append(item)
        else:
            mid.append(item)


    if reverse:
        return quick_sort(right, key, reverse) + mid + quick_sort(left, key, reverse)
    else:
        return quick_sort(left, key, reverse) + mid + quick_sort(right, key, reverse)



def merge_sort(products: List, key: Callable, reverse: bool) -> List:
    if len(products) <= 1:
        return products[:]

    mid = len(products) // 2
    left = merge_sort(products[:mid], key, reverse)
    right = merge_sort(products[mid:], key, reverse)

    return merge(left, right, key, reverse)


def merge(left: List, right: List, key: Callable, reverse: bool) -> List:
    result = []
    i = j = 0


    while i < len(left) and j < len(right):
        val_l = key(left[i])
        val_r = key(right[j])

        if (reverse and val_l > val_r) or (not reverse and val_l < val_r):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1


    result.extend(left[i:])
    result.extend(right[j:])
    return result
