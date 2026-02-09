from typing import Optional, List
from datetime import datetime
from storage.json_repository import Repository
from models.product import Product
from validators.product_validator import ProductValidator
from controllers.category_controller import CategoryController
from controllers.supplier_controller import SupplierController


class ProductController:
    def __init__(
        self,
        repo: Repository,
        category_controller: CategoryController,
        supplier_controller: SupplierController,
        activity_log_controller=None
    ):
        self.repo = repo
        self.category_controller = category_controller
        self.supplier_controller = supplier_controller
        self.activity_log = activity_log_controller
        self.products: List[Product] = []

        # Зареждане на продуктите
        for p_data in self.repo.load():
            product = Product.from_dict(p_data)

            fixed_categories = []
            for cid in product.categories:
                c = self.category_controller.get_by_id(cid)
                if c:
                    fixed_categories.append(c)

            product.categories = fixed_categories
            self.products.append(product)

    def _generate_id(self) -> int:
        if not self.products:
            return 1
        return max(p.product_id for p in self.products) + 1

    def exists_by_name(self, name: str) -> bool:
        return any(p.name.lower() == name.lower() for p in self.products)

    def add(
        self,
        name: str,
        category_ids: List[int],
        quantity: float,
        unit: str,
        description: str,
        price: float,
        supplier_id: Optional[int],
        user_id: str,  # ← ДОБАВЕНО
        tags: Optional[List[str]] = None
    ) -> Product:

        ProductValidator.validate_all(name, category_ids, quantity, unit, description, price)

        if self.exists_by_name(name):
            raise ValueError("Продукт с това име вече съществува.")

        categories = []
        for cid in category_ids:
            c = self.category_controller.get_by_id(cid)
            if not c:
                raise ValueError(f"Категория с ID {cid} не съществува.")
            categories.append(c)

        if supplier_id is not None:
            if not self.supplier_controller.get_by_id(supplier_id):
                raise ValueError(f"Доставчик с ID {supplier_id} не съществува.")

        now = str(datetime.now())

        product = Product(
            product_id=self._generate_id(),
            name=name,
            categories=categories,
            quantity=float(quantity),
            unit=unit,
            description=description,
            price=price,
            supplier_id=supplier_id,
            tags=tags or [],
            created=now,
            modified=now
        )

        self.products.append(product)
        self.save_changes()

        # ЛОГВАНЕ НА ДОБАВЯНЕ
        if self.activity_log:
            self.activity_log.add_log(
                user_id,
                "ADD_PRODUCT",
                f"Added product: {product.name}"
            )

        return product

    def get_all(self) -> List[Product]:
        return self.products

    def get_by_id(self, product_id: int) -> Optional[Product]:
        for p in self.products:
            if p.product_id == product_id:
                return p
        return None

    def update_name(self, product_id: int, new_name: str, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")

        if self.exists_by_name(new_name) and new_name != p.name:
            raise ValueError("Продукт с това име вече съществува.")

        ProductValidator.validate_name(new_name)
        p.name = new_name
        p.update_modified()
        self.save_changes()

        # ЛОГВАНЕ
        if self.activity_log:
            self.activity_log.add_log(
                user_id,
                "EDIT_PRODUCT",
                f"Updated name of product ID {product_id} to '{new_name}'"
            )

        return True

    def update_description(self, product_id: int, new_description: str, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")

        ProductValidator.validate_description(new_description)
        p.description = new_description
        p.update_modified()
        self.save_changes()

        if self.activity_log:
            self.activity_log.add_log(
                user_id,
                "EDIT_PRODUCT",
                f"Updated description of product ID {product_id}"
            )

        return True

    def update_categories(self, product_id: int, new_category_ids: List[int], user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")

        categories = []
        for c_id in new_category_ids:
            c = self.category_controller.get_by_id(c_id)
            if not c:
                raise ValueError(f"Категория с ID {c_id} не съществува.")
            categories.append(c)

        p.categories = categories
        p.update_modified()
        self.save_changes()

        if self.activity_log:
            self.activity_log.add_log(
                user_id,
                "EDIT_PRODUCT",
                f"Updated categories of product ID {product_id}"
            )

        return True

    def update_supplier(self, product_id: int, supplier_id: int, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")

        supplier = self.supplier_controller.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Доставчикът с ID {supplier_id} не съществува.")

        p.supplier_id = supplier_id
        p.update_modified()
        self.save_changes()

        if self.activity_log:
            self.activity_log.add_log(
                user_id,
                "EDIT_PRODUCT",
                f"Updated supplier of product ID {product_id}"
            )

        return True

    def update_price(self, product_id: int, new_price: float, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")

        ProductValidator.validate_price(new_price)
        p.price = new_price
        p.update_modified()
        self.save_changes()

        if self.activity_log:
            self.activity_log.add_log(
                user_id,
                "EDIT_PRODUCT",
                f"Updated price of product ID {product_id} to {new_price}"
            )

        return True

    def increase_quantity(self, product_id: int, amount: float, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")

        if amount < 0:
            raise ValueError("Количество трябва да е положително.")

        p.quantity += float(amount)
        p.update_modified()
        self.save_changes()

        if self.activity_log:
            self.activity_log.add_log(
                user_id,
                "INCREASE_QUANTITY",
                f"Added {amount} units to product ID {product_id}"
            )

        return True

    def decrease_quantity(self, product_id: int, amount: float, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")

        if amount < 0:
            raise ValueError("Количество трябва да е положително.")

        if p.quantity < amount:
            raise ValueError("Недостатъчна наличност.")

        p.quantity -= float(amount)
        p.update_modified()
        self.save_changes()

        if self.activity_log:
            self.activity_log.add_log(
                user_id,
                "DECREASE_QUANTITY",
                f"Removed {amount} units from product ID {product_id}"
            )

        return True

    def remove_by_id(self, product_id: int, user_id: str) -> bool:
        original_len = len(self.products)
        self.products = [p for p in self.products if p.product_id != product_id]

        if len(self.products) < original_len:
            self.save_changes()

            if self.activity_log:
                self.activity_log.add_log(
                    user_id,
                    "DELETE_PRODUCT",
                    f"Deleted product ID {product_id}"
                )

            return True

        return False

    def remove_by_name(self, name: str, user_id: str) -> bool:
        name = name.lower()
        original_len = len(self.products)
        self.products = [p for p in self.products if p.name.lower() != name]

        if len(self.products) < original_len:
            self.save_changes()

            if self.activity_log:
                self.activity_log.add_log(
                    user_id,
                    "DELETE_PRODUCT",
                    f"Deleted product '{name}'"
                )

            return True

        return False

    def search(self, keyword: str) -> List[Product]:
        keyword = (keyword or "").lower()
        return [
            p for p in self.products
            if keyword in (p.name or "").lower()
            or keyword in (p.description or "").lower()
        ]

    def filter_by_multiple_category_ids(self, category_ids: List[int]) -> List[Product]:
        filtered = []
        for p in self.products:
            for c in p.categories:
                if c.category_id in category_ids:
                    filtered.append(p)
                    break
        return filtered

    def average_price(self) -> float:
        if not self.products:
            return 0.0
        return sum(p.price for p in self.products) / len(self.products)

    def check_low_stock(self, threshold: float = 5) -> List[Product]:
        return [p for p in self.products if p.quantity < threshold]

    def total_values(self) -> float:
        return sum(p.price * p.quantity for p in self.products)

    def most_expensive(self) -> Optional[Product]:
        return max(self.products, key=lambda p: p.price, default=None)

    def cheapest(self) -> Optional[Product]:
        return min(self.products, key=lambda p: p.price, default=None)

    def group_by_category(self) -> dict:
        grouped = {}
        for p in self.products:
            for c in p.categories:
                grouped.setdefault(c.category_id, []).append(p)
        return grouped

    def sort_by_name(self) -> List[Product]:
        self.products.sort(key=lambda p: p.name.lower())
        return self.products

    def sort_by_price_desc(self) -> List[Product]:
        return sorted(self.products, key=lambda p: p.price, reverse=True)

    def bubble_sort(self) -> List[Product]:
        sorted_products = self.products[:]
        n = len(sorted_products)
        for i in range(n):
            for j in range(0, n - i - 1):
                if sorted_products[j].price < sorted_products[j + 1].price:
                    sorted_products[j], sorted_products[j + 1] = sorted_products[j + 1], sorted_products[j]
        return sorted_products

    def selection_sort(self) -> List[Product]:
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

            sorted_products[i], sorted_products[max_idx] = sorted_products[max_idx], sorted_products[i]
            i += 1

        return sorted_products


    # ADVANCED SEARCH & FILTERING

    def search_by_price_range(self, min_price: float = None, max_price: float = None) -> List[Product]:
        results = self.products

        if min_price is not None:
            results = [p for p in results if p.price >= min_price]

        if max_price is not None:
            results = [p for p in results if p.price <= max_price]

        return results

    def search_by_quantity_range(self, min_qty: float = None, max_qty: float = None) -> List[Product]:
        results = self.products

        if min_qty is not None:
            results = [p for p in results if p.quantity >= min_qty]

        if max_qty is not None:
            results = [p for p in results if p.quantity <= max_qty]

        return results

    def search_by_category(self, category_id: int) -> List[Product]:
        return [
            p for p in self.products
            if any(c.category_id == category_id for c in p.categories)
        ]

    def search_by_supplier(self, supplier_id: int) -> List[Product]:
        return [p for p in self.products if p.supplier_id == supplier_id]

    def search_combined(
        self,
        name_keyword: str = None,
        category_id: int = None,
        min_price: float = None,
        max_price: float = None,
        min_qty: float = None,
        max_qty: float = None,
        supplier_id: int = None
    ) -> List[Product]:

        results = self.products

        if name_keyword:
            kw = name_keyword.lower()
            results = [
                p for p in results
                if kw in p.name.lower() or kw in p.description.lower()
            ]

        if category_id is not None:
            results = [
                p for p in results
                if any(c.category_id == category_id for c in p.categories)
            ]

        if supplier_id is not None:
            results = [p for p in results if p.supplier_id == supplier_id]

        if min_price is not None:
            results = [p for p in results if p.price >= min_price]

        if max_price is not None:
            results = [p for p in results if p.price <= max_price]

        if min_qty is not None:
            results = [p for p in results if p.quantity >= min_qty]

        if max_qty is not None:
            results = [p for p in results if p.quantity <= max_qty]

        return results


    def save_changes(self) -> None:
        self.repo.save([p.to_dict() for p in self.products])
