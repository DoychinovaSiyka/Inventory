def get_category_stats(categories, products):
    """Брои продуктите и връща точната структура, която контролерът изисква."""
    result = []

    for cat in categories:
        cat_id = str(cat.category_id)
        count = 0

        for p in products:
            for pc in p.categories:
                pc_id = str(pc.category_id) if hasattr(pc, 'category_id') else str(pc)

                if pc_id == cat_id:
                    count += 1
                    break

        result.append({"id": cat.category_id, "name": cat.name, "product_count": count})

    return result