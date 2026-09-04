import uuid
from typing import Optional, List, Union

from models.movement import Movement, MovementType
from validators.movement_validator import MovementValidator
from controllers.abstract_controller import AbstractController
from controllers.product_controller import ProductController
from controllers.user_controller import UserController
from controllers.location_controller import LocationController
from controllers.supplier_controller import SupplierController






class MovementController(AbstractController):

    def __init__(self, repo, product_controller: ProductController, user_controller: UserController,
                 location_controller: LocationController, supplier_controller: SupplierController):
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
        if self.inventory_controller:
            self.inventory_controller.update_inventory_from_movements(self.movements)



    def _location_id(self, loc_id: Optional[str]) -> Optional[str]:
        if not loc_id:
            raise ValueError("Не е избран склад.")

        loc = self.location_controller.get_by_id(str(loc_id))
        if not loc:
            raise ValueError(f"Невалиден склад: {loc_id}")

        return str(loc.location_id)




    def get_all(self) -> List[Movement]:
        return self.movements




    def add_in(self, product_id: str, quantity: Union[float, str], price: Optional[str], location_id: str,
               supplier_id: str, user_id: str):
        movement = self.create_movement(product_id=product_id, user_id=user_id, movement_type="IN", quantity=quantity,
                                        price=price, location_id=location_id, supplier_id=supplier_id)
        self._save_movements()
        return movement





    def add_out(self, product_id: str, quantity: Union[float, str], customer: str,
                location_id: str, user_id: str, price: Optional[str] = None):

        resolved_loc = self._location_id(location_id)
        available = self.inventory_controller.get_stock(product_id, resolved_loc)
        product = self.product_controller.get_by_id(product_id)

        parsed_qty = MovementValidator.parse_quantity(quantity)
        MovementValidator.validate_out_rules(product=product, quantity=parsed_qty, customer=customer, available_stock=available)

        movement = self.create_movement(product_id=product_id, user_id=user_id, movement_type="OUT",
                                        quantity=parsed_qty, price=price, location_id=location_id, customer=customer)

        if self.invoice_controller:
            self.invoice_controller.create_from_movement(movement=movement, product=product,
                                                         customer=customer or "Общ клиент", user_id=user_id)

        self._save_movements()
        return movement






    def move_stock(self, product_id: str, quantity: Union[float, str], from_loc: str, to_loc: str, user_id: str):
        resolved_from = self._location_id(from_loc)
        resolved_to = self._location_id(to_loc)

        available = self.inventory_controller.get_stock(product_id, resolved_from)
        product = self.product_controller.get_by_id(product_id)

        parsed_qty = MovementValidator.parse_quantity(quantity)
        MovementValidator.validate_move_rules(product=product, quantity=parsed_qty, available_stock=available,
                                              from_location_id=resolved_from, to_location_id=resolved_to)

        movement = self.create_movement(product_id=product_id, user_id=user_id, movement_type="MOVE", quantity=parsed_qty,
                                        price="0", from_location_id=from_loc, to_location_id=to_loc)

        self._save_movements()
        return movement







    def create_movement(self, product_id: str, user_id: str, movement_type: str, quantity: Union[float, str],
                        price: Optional[str] = None, location_id: Optional[str] = None, customer: Optional[str] = None,
                        supplier_id: Optional[str] = None, from_location_id: Optional[str] = None,
                        to_location_id: Optional[str] = None) -> Movement:

        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError("Продуктът не съществува.")




        if isinstance(product.status, bool) and not product.status:
            raise ValueError("Продуктът е неактивен и не може да участва в движения.")

        user = self.user_controller.get_by_id(user_id)
        if not user:
            raise ValueError("Потребителят не е намерен.")

        m_type_str = MovementValidator.normalize_movement_type(movement_type)
        qty = MovementValidator.parse_quantity(quantity)

        if m_type_str == "MOVE":
            resolved_loc = None
            resolved_from = self._location_id(from_location_id)
            resolved_to = self._location_id(to_location_id)
            prc = 0.0

        else:  # "IN" или "OUT"
            resolved_loc = self._location_id(location_id)
            resolved_from = None
            resolved_to = None

            if price is not None and str(price).strip() != "":
                try:
                    clean_price = str(price).lower().replace("лв", "").replace(",", ".").strip()
                    prc = float(clean_price)
                except (ValueError, TypeError):
                    raise ValueError("Невалидна цена.")
            else:
                prc = float(product.price)

        movement_id = str(uuid.uuid4())

        movement = Movement(movement_id=movement_id, product_id=product.product_id, product_name=product.name,
                            user_id=user.user_id, location_id=resolved_loc, movement_type=MovementType[m_type_str],
                            quantity=qty, unit=product.unit, price=prc, supplier_id=supplier_id,
                            customer=customer or "Общ клиент", from_location_id=resolved_from, to_location_id=resolved_to)



        self.movements.append(movement)
        return movement
