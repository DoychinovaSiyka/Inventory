
def filter_combined(products, **kwargs):
    """Филтър за продукти по ключова дума и категории."""
    results = products

    keyword = kwargs.get("keyword")
    if keyword:
        keyword = keyword.lower().strip()
        words = keyword.split()

        filtered = []
        for p in results:
            text = p.name.lower() + " " + p.description.lower()

            for c in p.categories:
                text += " " + c.name.lower()

            ok = True
            for w in words:
                if w not in text:
                    ok = False
                    break

            if ok:
                filtered.append(p)

        results = filtered



    category_ids = kwargs.get("category_ids")
    if category_ids:
        wanted = []
        for cid in category_ids:
            wanted.append(str(cid))

        filtered = []
        for p in results:
            product_cat_ids = []
            for c in p.categories:
                product_cat_ids.append(str(c.category_id))


            match = False
            for cid in product_cat_ids:
                if cid in wanted:
                    match = True
                    break

            if match:
                filtered.append(p)

        results = filtered

    return results
