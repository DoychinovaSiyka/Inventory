from storage.json_repository import Repository
from models.product import Product


class ProductController():
    def __init__(self, repo:Repository):
        self.repo = repo
        self.products = [Product.from_dict(p) for p in self.repo.load()]
        self._cache = {} # кеш
        self._log = []

    def add(self, name,categories, quantity, description, price):
        product = Product(name, categories, quantity, description, price )
        self.products.append(product)
        self._save()
        return product

    def clear_cache(self):
        self._cache.clear()


    def update_price(self,name,new_price):
        for p in self.products:
            if p.name == name:
                p.price = new_price
                self._cache.clear()
                self._save()
                return True
        return False



    def sort_by_name(self):
        self.products.sort(key = lambda p:p.name.lower())

    def filter_by_multiple_category_ids(self,category_ids):

        key = ("filter_by_multiple_category_ids",tuple(sorted(category_ids)))
        if key in self._cache:
            return self._cache[key]
        filtered = []
        for p in self.products:
            for c in p.categories:
                if c.category_id in category_ids:
                    filtered.append(p)
                    break # спира, за да не добави продукта многократно
        self._cache[key] = filtered
        return filtered



    def remove_by_name(self, name):
        original_len = len(self.products)
        self.products = [p for p in self.products if p.name!= name]
        if len(self.products) < original_len:
            self._cache.clear()
            self._save()
            return True
        return False

    def get_all(self):
        return self.products

    def _log_action(self,action,product):
        self._log.append({
            "action":action,"name":product.name,
            "price":product.price,
            "quantity":product.quantity})



    def sort_by_price_desc_cached(self):
        """Сортира продуктитите в низходящ ред по цена"""
        key = ("sort_by_price_desc",len(self.products))
        if key in self._cache:
            return self._cache[key]
        sorted_list = sorted(self.products,key = lambda p:p.price,reverse = True)
        self._cache[key] = sorted_list
        return sorted_list


    def average_price(self):
        key = ("average_price",len(self.products))
        if key in self._cache:
            return self._cache[key]
        if not self.products:
            result = 0.0
        else:
            result = sum(p.price for p in self.products)/ len(self.products)
        self._cache[key] = result
        return result

    def check_low_stock(self, threshold=5):
        key = ("low_stock", threshold, len(self.products))
        if key in self._cache:
            return self._cache[key]
        result = [p for p in self.products if p.quantity < threshold]
        self._cache[key] = result
        return result

    def search(self, keyword):
        key = ("search", keyword.lower())
        if key in self._cache:
            return self._cache[key]
        result = [p for p in self.products if keyword in (p.name or "").lower() or
                  keyword in (p.description or "").lower()]
        self._cache[key] = result
        return result

    def most_expensive(self):
        return max(self.products,key = lambda p:p.price,default =None)

    def cheapest(self):
        return min(self.products,key = lambda p:p.price,default = None)

    def total_values(self):
        key = ("total_value", len(self.products))
        if key in self._cache:
            return self._cache[key]
        result = sum(p.price*p.quantity for p in self.products)
        self._cache[key] = result
        return result



    def group_by_category(self):
        grouped = {}
        for p in self.products:
            for c in p.categories:
                grouped.setdefault(c.category_id,[]).append(p)
        return grouped

    def bubble_sort(self):
        sorted_products = self.products[:]
        n = len(sorted_products)
        for i in range(n):
            for j in range(0,n-i-1):
                if sorted_products[j].price < sorted_products[j+1].price:
                    sorted_products[j],sorted_products[j+1] = sorted_products[j+1],sorted_products[j]
        return sorted_products

    def selection_sort(self):
        sorted_products = self.products[:]
        i = 0
        n = len(sorted_products)

        while i < n:
            max_idx = i
            j = i + 1
            while j < n:
                if sorted_products[j].price > sorted_products[max_idx].price:
                    max_idx = j
                j += 1

            # Размяна
            sorted_products[i],sorted_products[max_idx] = sorted_products[max_idx],sorted_products[i]
            i+=1

        return sorted_products



    def _save(self):
        self.repo.save([p.to_dict() for p in self.products])





