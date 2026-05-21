
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
        wanted = set(str(cid) for cid in category_ids)

        filtered = []
        for p in results:
            for c in p.categories:
                if str(c.category_id) in wanted:
                    filtered.append(p)
                    break

        results = filtered

    return results
