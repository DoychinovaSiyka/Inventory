from storage.json_repository import Repository
from models.product import Product
from validators.product_validator import ProductValidator
from controllers.category_controller  import CategoryController



class ProductController:
    def __init__(self, repo: Repository, category_controller: CategoryController):
        self.repo = repo
        self.category_controller = category_controller
        self.products = [Product.from_dict(p) for p in self.repo.load()]
        self._log = []  # само лог за действия

    def exists_by_name(self, name):
        return any(p.name.lower() == name.lower() for p in self.products)
    # create
    def add(self, name, category_ids, quantity, description,
            price):
        ProductValidator.validate_all(name, category_ids, quantity, description, price)
        # Проверка дали категориите съществуват
        categories = []
        for c_id in category_ids:
            c = self.category_controller.get_by_id(c_id)
            if not c:
                raise ValueError(f"Категория с ID {c_id} не съществува.")
            categories.append(c)


        product = Product(name, categories, quantity, description, price)
        self.products.append(product)
        self._save()
        return product

    # Read
    def get_all(self):
        return self.products
    def get_by_id(self,product_id):
        for p in self.products:
            if p.product_id == product_id:
                return p
        return None


    # UPDATE
    def update_price(self, product_id, new_price):
        p = self.get_by_id(product_id)
        if not p:
            return False
        p.price = new_price
        p.update_modified()
        self._save()
        return True


    def increase_quantity(self,product_id,amount):
        p = self.get_by_id(product_id)
        if not p:
            return  False
        p.quantity+= amount
        p.update_modified()
        self._save()
        return True

    def decrease_quantity(self,product_id,amount):
        p = self.get_by_id(product_id)
        if not p:
            return  False
        if p.quantity < amount:
            raise ValueError("Недостатъчна наличност.")
        p.quantity-= amount
        p.update_modified()
        self._save()
        return True

    # Delete
    def remove_by_name(self, name):
        original_len = len(self.products)
        self.products = [p for p in self.products if p.name != name]
        if len(self.products) < original_len:
            self._save()
            return True
        return False
    def remove_by_id(self, product_id):
        original_len = len(self.products)
        self.products = [p for p in self.products if p.product_id  != product_id ]
        if len(self.products) < original_len:
            self._save()
            return True
        return False


    def search(self, keyword):
        """Търси продукти по име или описание"""
        return [p for p in self.products
                if keyword in (p.name or "").lower()
                or keyword in (p.description or "").lower()]
    def filter_by_multiple_category_ids(self, category_ids):
        filtered = []
        for p in self.products:
            for c in p.categories:
                if c.category_id in category_ids:
                    filtered.append(p)
                    break  # спира, за да не добави продукта многократно
        return filtered







    def average_price(self):
        """Изчислява средната цена на всички продукти"""
        if not self.products:
            return 0.0
        return sum(p.price for p in self.products) / len(self.products)

    def check_low_stock(self, threshold=5):
        """Връща списък с продукти, които са под зададения праг"""
        return [p for p in self.products if p.quantity < threshold]



    def total_values(self):
        """Изчислява общата стойност на всички продукти (цена * количество)"""
        return sum(p.price * p.quantity for p in self.products)

    def most_expensive(self):
        return max(self.products, key=lambda p: p.price, default=None)

    def cheapest(self):
        return min(self.products, key=lambda p: p.price, default=None)

    def group_by_category(self):
        grouped = {}
        for p in self.products:
            for c in p.categories:
                grouped.setdefault(c.category_id, []).append(p)
        return grouped

    def sort_by_name(self):
        self.products.sort(key=lambda p: p.name.lower())

    def sort_by_price_desc(self):
        """Сортира продуктите в низходящ ред по цена"""
        return sorted(self.products, key=lambda p: p.price, reverse=True)

    def bubble_sort(self):
        sorted_products = self.products[:]
        n = len(sorted_products)
        for i in range(n):
            for j in range(0, n - i - 1):
                if sorted_products[j].price < sorted_products[j + 1].price:
                    sorted_products[j], sorted_products[j + 1] = sorted_products[j + 1], sorted_products[j]
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
            sorted_products[i], sorted_products[max_idx] = sorted_products[max_idx], sorted_products[i]
            i += 1

        return sorted_products

    def _save(self):
        self.repo.save([p.to_dict() for p in self.products])


