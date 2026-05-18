import uuid
from typing import Optional, List
from datetime import datetime
from models.movement import Movement, MovementType
from validators.movement_validator import MovementValidator


class MovementController:

    def __init__(self, repo, product_controller, user_controller, location_controller, supplier_controller, invoice_controller):

        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller
        self.invoice_controller = invoice_controller

        raw = self.repo.load() or []
        self.movements: List[Movement] = []

        for m in raw:
            try:
                obj = Movement.from_dict(m)
                if obj:
                    self.movements.append(obj)
            except Exception:
                continue

        self.inventory_controller = None



    def _save_movements(self):
        """Записва всички движения в JSON файла."""
        self.repo.save([m.to_dict() for m in self.movements])


    def set_inventory_controller(self, inventory_controller):
        self.inventory_controller = inventory_controller




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




    def search_movements(self, product_id=None, movement_type=None, date=None, location_id=None, customer=None, supplier_id=None) -> List[Movement]:
        results = []

        for m in self.movements:
            ok = True

            if product_id is not None and str(m.product_id) != str(product_id):
                ok = False

            if movement_type is not None and m.movement_type.name != movement_type:
                ok = False


            if date is not None and str(m.date)[:10] != str(date):
                ok = False


            if location_id is not None:
                is_in_loc = (str(m.location_id) == str(location_id) or
                             str(m.from_location_id) == str(location_id) or
                             str(m.to_location_id) == str(location_id))
                if not is_in_loc:
                    ok = False


            if customer is not None and m.customer != customer:
                ok = False


            if supplier_id is not None and str(m.supplier_id) != str(supplier_id):
                ok = False


            if ok:
                results.append(m)

        return results



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


        if m_type_str == "MOVE":
            resolved_loc = None
            resolved_from = self._location_id(from_location_id)
            resolved_to = self._location_id(to_location_id)

            MovementValidator.validate_move_rules(product, qty, self.inventory_controller, resolved_from, resolved_to)
            prc = 0.0

        else:

            resolved_loc = self._location_id(location_id)
            resolved_from = None
            resolved_to = None

            if m_type_str == "OUT":
                MovementValidator.validate_out_rules(product, qty, customer, self.inventory_controller, resolved_loc)



            if price is not None and str(price).strip() != "":
                prc = float(price)
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