from typing import Optional, List
from models.movement import Movement, MovementType
from storage.json_repository import JSONRepository
from validators.movement_validator import MovementValidator
from filters.movement_filters import filter_by_description, filter_advanced


class MovementController:
    """Контролер за движенията."""
    def __init__(self, repo: JSONRepository, product_controller, user_controller,
                 location_controller, invoice_controller, activity_log_controller=None,
                 inventory_controller=None, supplier_controller=None):

        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.invoice_controller = invoice_controller
        self.activity_log = activity_log_controller
        self.inventory_controller = inventory_controller
        self.supplier_controller = supplier_controller

        self.movements: List[Movement] = []
        self._load_movements()

        # Инвентарът се пресмята само в паметта
        self._sync_inventory_only_in_memory()


    def _load_movements(self) -> None:
        raw = self.repo.load() or []
        self.movements = [Movement.from_dict(m) for m in raw]


    def _sync_inventory_only_in_memory(self) -> None:
        """Обновява инвентара в RAM паметта без да записва във файловете."""
        if not self.inventory_controller:
            return

        safe_movements = self._inventory_safe_movements()
        safe_movements.sort(key=lambda m: m.date)

        try:
            self.inventory_controller.rebuild_inventory_from_movements(safe_movements)
        except Exception:
            pass


    def save_changes(self) -> None:
        """Записва на диска само при реална промяна."""
        self.repo.save([m.to_dict() for m in self.movements])


    def _inventory_safe_movements(self) -> List[Movement]:
        return [m for m in self.movements
                if self.product_controller.get_by_id(m.product_id)]


    def get_by_id(self, movement_id: str) -> Optional[Movement]:
        movement_id = str(movement_id).strip()
        for m in self.movements:
            if m.movement_id == movement_id:
                return m
        return None


    def move_product(self, product_id: str, user_id: str,
                     from_loc: str, to_loc: str,
                     quantity: str, description: str) -> Movement:
        """Преместване между локации (MOVE)."""

        qty = MovementValidator.parse_quantity(quantity)
        MovementValidator.validate_movement_type("MOVE")

        product = self.product_controller.get_by_id(product_id)

        # Актуализиране на инвентара (в RAM)
        self.inventory_controller.decrease_stock(product_id, from_loc, qty, product.unit)
        self.inventory_controller.increase_stock(product_id, product.name, to_loc, qty, product.unit)

        # Моделът Movement сам генерира ID и дати
        movement = Movement(movement_id=None, product_id=product_id, product_name=product.name,
                            user_id=user_id, location_id=None, movement_type=MovementType.MOVE,
                            quantity=qty, unit=product.unit, description=description, price=None,
                            supplier_id=None, customer=None, from_location_id=from_loc, to_location_id=to_loc)

        self.movements.append(movement)
        self.save_changes()

        return movement


    def add(self, product_data: dict, user_id: str) -> Product:
        ProductValidator.validate_category_exists(product_data['category_ids'], self.category_controller)
        ProductValidator.validate_supplier_exists(product_data.get('supplier_id'), self.supplier_controller)
        ProductValidator.validate_name(product_data['name'])

        now = Product.now()
        categories = [self.category_controller.get_by_id(cid) for cid in product_data['category_ids']]

        product = Product(product_id=self._generate_id(), name=product_data['name'],
                          categories=categories, unit=product_data['unit'],
                          description=product_data['description'], price=float(product_data['price']),
                          supplier_id=product_data.get('supplier_id'), tags=product_data.get('tags', []),
                          location_id=product_data.get('location_id'), created=now, modified=now)

        self.products.append(product)
        self.save_changes()
        self._log(user_id, "ADD_PRODUCT", f"Добавен продукт: {product.name}")

        quantity = product_data.get("quantity")
        location_id = product_data.get("location_id")

        if quantity and location_id and self.movement_controller:
            qty = float(quantity)
            if qty > 0:
                self.movement_controller.add(product_id=product.product_id, user_id=user_id,
                                             location_id=location_id, movement_type="IN",
                                             quantity=str(qty), description="Начално зареждане при създаване на продукт",
                                             price=str(product.price), supplier_id=product.supplier_id or "system")

        return product


    def search_by_description(self, keyword: str) -> List[Movement]:
        keyword = keyword.strip().lower()
        if len(keyword) < 3:
            return []
        return [m for m in self.movements if keyword in m.description.lower()]


    def advanced_filter(self, **criteria) -> List[Movement]:
        return filter_advanced(self.movements, **criteria)


    def rebuild_inventory(self) -> None:
        """Ръчно преизчисляване на всичко."""
        if not self.inventory_controller:
            return

        safe_movements = self._inventory_safe_movements()
        safe_movements.sort(key=lambda m: m.date)
        self.inventory_controller.rebuild_inventory_from_movements(safe_movements)
