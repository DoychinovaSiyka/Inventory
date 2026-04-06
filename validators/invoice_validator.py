class InvoiceValidator:

    @staticmethod
    def validate_product(product):
        if not product:
            raise ValueError("продуктът е задължителен.")

    @staticmethod
    def validate_customer(customer):
        if not customer:
            raise ValueError("клиентът е задължителен.")

    @staticmethod
    def validate_quantity(quantity):
        if quantity <= 0:
            raise ValueError("quantity трябва да е > 0.")


    @staticmethod
    def validate_unit(unit):
        if not unit or not unit.strip():
            raise ValueError("мерната единица е задължителна.")

    @staticmethod
    def validate_unit_price(unit_price):
        if unit_price <= 0:
            raise ValueError("unit price трябва да е > 0.")

    @staticmethod
    def validate_movement_id(movement_id):
        if movement_id is None:
            raise ValueError("movement_id е задължителен.")

    @staticmethod
    def validate_all(product, customer, quantity, unit, unit_price, movement_id):
        InvoiceValidator.validate_product(product)
        InvoiceValidator.validate_customer(customer)
        InvoiceValidator.validate_quantity(quantity)
        InvoiceValidator.validate_unit(unit)
        InvoiceValidator.validate_unit_price(unit_price)
        InvoiceValidator.validate_movement_id(movement_id)
