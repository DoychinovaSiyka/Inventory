def get_category_stats(categories, products):
    """Брои продуктите във всяка категория."""
    result = []

    for cat in categories:
        cat_id = str(cat.category_id)
        count = 0

        for p in products:
            for pc in p.categories:
                if type(pc) is str or type(pc) is int:
                    current_id = str(pc)
                else:
                    current_id = str(pc.category_id)

                if current_id == cat_id:
                    count += 1
                    break


        result.append({"id": cat.category_id, "name": cat.name, "product_count": count})

    return result
