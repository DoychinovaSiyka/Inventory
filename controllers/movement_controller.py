import uuid
from typing import Optional, List
from models.movement import Movement, MovementType
from validators.movement_validator import MovementValidator
from controllers.abstract_controller import AbstractController


class MovementController(AbstractController):

    def __init__(self, repo, product_controller, user_controller,
                 location_controller, supplier_controller):

        super().__init__(repo)

        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller

        self.invoice_controller = None
        self.inventory_controller = None

        self.movements: List[Movement] = self.load() or []



    def set_invoice_controller(self, invoice_controller):
        self.invoice_controller = invoice_controller

    def set_inventory_controller(self, inventory_controller):
        self.inventory_controller = inventory_controller



    def from_dict(self, data):
        return Movement.from_dict(data)

    def to_dict(self, obj):
        return obj.to_dict()

    def _save_movements(self):
        self.save(self.movements)



    def _location_id(self, loc_id: Optional[str]) -> Optional[str]:
        if not loc_id:
            raise ValueError("Не е избран склад.")

        loc = self.location_controller.get_by_id(str(loc_id))
        if not loc:
            raise ValueError(f"Невалиден склад: {loc_id}")

        return str(loc.location_id)



    def get_all(self) -> List[Movement]:
        return self.movements





    def add_in(self, product_id, quantity, price, location_id, supplier_id, user_id):
        movement = self.create_movement(product_id=product_id, user_id=user_id, movement_type="IN",
                                        quantity=quantity, price=price, location_id=location_id, supplier_id=supplier_id)

        if self.inventory_controller:
            self.inventory_controller.increase_stock(product_id, quantity, location_id)

        return movement



    def add_out(self, product_id, quantity, customer, location_id, user_id, price):

        resolved_loc = self._location_id(location_id)

        MovementValidator.validate_out_rules(self.product_controller.get_by_id(product_id), float(quantity),
                                             customer, self.inventory_controller, resolved_loc)

        movement = self.create_movement(product_id=product_id, user_id=user_id, movement_type="OUT",
                                        quantity=quantity, price=price, location_id=location_id, customer=customer)

        if self.inventory_controller:
            self.inventory_controller.decrease_stock(product_id, quantity, location_id)

        # Фактура
        if self.invoice_controller:
            self.invoice_controller.create_from_movement(movement=movement, product=self.product_controller.get_by_id(product_id),
                                                         customer=customer or "Общ клиент", user_id=user_id)

        return movement





    def move_stock(self, product_id, quantity, from_loc, to_loc, user_id):
        movement = self.create_movement(product_id=product_id, user_id=user_id, movement_type="MOVE",
                                        quantity=quantity, price="0", from_location_id=from_loc, to_location_id=to_loc)

        if self.inventory_controller:
            self.inventory_controller.move_stock(product_id, quantity, from_loc, to_loc)

        return movement



    def create_movement(self, product_id: str, user_id: str, movement_type: str,
                        quantity: str, price: Optional[str], location_id: Optional[str] = None,
                        customer: Optional[str] = None, supplier_id: Optional[str] = None,
                        from_location_id: Optional[str] = None, to_location_id: Optional[str] = None) -> Movement:

        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError("Продуктът не съществува.")

        user = self.user_controller.get_by_id(user_id)
        if not user:
            raise ValueError("Потребителят не е намерен.")

        m_type_str = MovementValidator.normalize_movement_type(movement_type)
        qty = MovementValidator.parse_quantity(quantity)

        # MOVE
        if m_type_str == "MOVE":
            resolved_loc = None
            resolved_from = self._location_id(from_location_id)
            resolved_to = self._location_id(to_location_id)

            MovementValidator.validate_move_rules(product, qty, self.inventory_controller, resolved_from, resolved_to)
            prc = 0.0

        # IN / OUT
        else:
            resolved_loc = self._location_id(location_id)
            resolved_from = None
            resolved_to = None

            if m_type_str == "OUT":
                MovementValidator.validate_out_rules(product, qty, customer, self.inventory_controller, resolved_loc)



            if price:
                clean = str(price).lower()
                clean = clean.replace("лв.", "").replace("лв", "")
                clean = clean.replace(",", ".").replace(" ", "").strip()
                if clean.endswith("."):
                    clean = clean[:-1]
                prc = float(clean)
            else:
                prc = float(product.price)

        movement_id = str(uuid.uuid4())

        movement = Movement(movement_id=movement_id, product_id=product.product_id, product_name=product.name,
                            user_id=user.user_id, location_id=resolved_loc, movement_type=MovementType[m_type_str],
                            quantity=qty, unit=product.unit, price=prc, supplier_id=supplier_id,
                            customer=customer or "Общ клиент", from_location_id=resolved_from, to_location_id=resolved_to)



        self.movements.append(movement)
        self._save_movements()

        return movement
