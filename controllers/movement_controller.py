import uuid
from datetime import datetime
from models.movement import Movement, MovementType
from models.invoice import Invoice
from validators.movement_validator import MovementValidator


class MovementController:
    def __init__(self, repo, product_controller, user_controller, location_controller, stocklog_controller, invoice_controller):
        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.stocklog_controller = stocklog_controller
        self.invoice_controller = invoice_controller

        # Зареждаме движенията от JSON
        self.movements = [Movement.from_dict(m) for m in self.repo.load()]

    # ---------------------------------------------------------
    # Генериране на UUID за movement_id
    # ---------------------------------------------------------
    def _generate_id(self):
        return str(uuid.uuid4())

    # ---------------------------------------------------------
    # Създаване на движение (IN / OUT / MOVE)
    # ---------------------------------------------------------
    def add(self, product_id, user_id, location_id, movement_type, quantity, description, price):

        # 1. Валидации
        MovementValidator.validate_movement_type(movement_type)
        MovementValidator.validate_description(description)
        quantity = MovementValidator.parse_quantity(quantity)
        price = MovementValidator.parse_price(price)

        # 2. Проверка за потребител
        user = self.user_controller.get_by_id(user_id)
        if not user:
            raise ValueError(f"Потребител с ID {user_id} не съществува.")

        # 3. Проверка за продукт
        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт с ID {product_id} не съществува.")

        # 4. Проверка за локация
        location = self.location_controller.get_by_id(location_id)
        if not location:
            raise ValueError(f"Локация с ID {location_id} не съществува.")

        # 5. movement_type → MovementType
        if isinstance(movement_type, int):
            if movement_type == 0:
                movement_type = MovementType.IN
            elif movement_type == 1:
                movement_type = MovementType.OUT
            elif movement_type == 2:
                movement_type = MovementType.MOVE
            else:
                raise ValueError("Невалиден тип движение.")

        # ---------------------------------------------------------
        # 6. Логика за IN / OUT / MOVE
        # ---------------------------------------------------------
        if movement_type == MovementType.IN:
            product.quantity += quantity
            action = "add"

        elif movement_type == MovementType.OUT:
            if product.quantity < quantity:
                raise ValueError("Недостатъчна наличност за продажба.")
            product.quantity -= quantity
            action = "remove"

        elif movement_type == MovementType.MOVE:
            action = "move"
            # MOVE не променя quantity, но може да променя location
            product.location_id = location_id

        # Обновяване на продукта
        product.update_modified()
        self.product_controller._save()

        # ---------------------------------------------------------
        # 7. Създаване на Movement
        # ---------------------------------------------------------
        movement = Movement(
            movement_id=self._generate_id(),
            product_id=product_id,
            user_id=user_id,
            location_id=location_id,
            movement_type=movement_type,
            quantity=quantity,
            description=description,
            price=price,
            date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        self.movements.append(movement)
        self._save()

        # ---------------------------------------------------------
        # 8. Запис в StockLog
        # ---------------------------------------------------------
        self.stocklog_controller.add_log(
            product_id=product_id,
            location_id=location_id,
            quantity=quantity,
            action=action
        )

        # ---------------------------------------------------------
        # 9. Генериране на Invoice при OUT движение
        # ---------------------------------------------------------
        if movement_type == MovementType.OUT:
            invoice = Invoice(
                movement_id=movement.movement_id,
                product=product.name,
                quantity=quantity,
                unit_price=price,
                customer=user.username
            )
            self.invoice_controller.add(invoice)

        return movement

    # ---------------------------------------------------------
    # Запис в JSON
    # ---------------------------------------------------------
    def _save(self):
        self.repo.save([m.to_dict() for m in self.movements])

    # ---------------------------------------------------------
    # GETTERS
    # ---------------------------------------------------------
    def get_all(self):
        return self.movements

    def get_by_id(self, movement_id):
        for m in self.movements:
            if m.movement_id == movement_id:
                return m
        return None

    def search(self, keyword):
        return [m for m in self.movements if keyword in (m.description or "").lower()]
