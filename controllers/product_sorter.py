from controllers.product_controller import ProductController




class ProductSorter:
    def __init__(self, product_controller: ProductController):
        self.product_controller = product_controller

    def sort_by_name_asc(self):
        return self.product_controller.get_custom_sort(sort_type="name", algorithm="merge", reverse=False)

    def sort_by_name_desc(self):
        return self.product_controller.get_custom_sort(sort_type="name", algorithm="merge", reverse=True)

    def sort_price_desc(self):
        return self.product_controller.get_custom_sort(sort_type="price", algorithm="quick", reverse=True)

    def sort_price_asc(self):
        return self.product_controller.get_custom_sort(sort_type="price", algorithm="quick", reverse=False)
