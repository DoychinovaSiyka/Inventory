class ProductViewModel:
    @staticmethod
    def group_by_category(products_by_category: dict):
        """ Преобразува групираните по категории продукти
        структура удобна за визуализация. """
        result = {}

        for category_id, products in products_by_category.items():
            items = []
            for p in products:
                items.append({
                    "name": p.name,
                    "location": p.location_id,
                    "quantity": p.quantity,
                    "unit": p.unit
                })
            result[category_id] = items

        return result