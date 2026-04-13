class InvoiceValidator:

    # PRODUCT
    @staticmethod
    def validate_product(product):
        if not product or not isinstance(product, str):
            raise ValueError("продуктът е задължителен.")

    # CUSTOMER
    @staticmethod
    def validate_customer(customer):
        if not customer or not isinstance(customer, str):
            raise ValueError("клиентът е задължителен.")

    # QUANTITY
    @staticmethod
    def validate_quantity(quantity):
        if quantity is None:
            raise ValueError("quantity е задължително поле.")
        if not isinstance(quantity, (int, float)):
            raise ValueError("quantity трябва да е число.")
        if quantity <= 0:
            raise ValueError("quantity трябва да е > 0.")

    # UNIT
    @staticmethod
    def validate_unit(unit):
        if not unit or not isinstance(unit, str) or not unit.strip():
            raise ValueError("мерната единица е задължителна.")

    # UNIT PRICE
    @staticmethod
    def validate_unit_price(unit_price):
        if unit_price is None:
            raise ValueError("unit price е задължително поле.")
        if not isinstance(unit_price, (int, float)):
            raise ValueError("unit price трябва да е число.")
        if unit_price <= 0:
            raise ValueError("unit price трябва да е > 0.")

    # MOVEMENT ID
    @staticmethod
    def validate_movement_id(movement_id):
        if movement_id is None or movement_id == "":
            raise ValueError("movement_id е задължителен.")

    # DATE VALIDATION
    @staticmethod
    def validate_date(date_str):
        """Приема само формата от JSON: YYYY-MM-DD HH:MM:SS"""
        from datetime import datetime

        if not date_str:
            raise ValueError("датата е задължителна.")

        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except:
            raise ValueError("Невалидна дата. Форматът трябва да е YYYY-MM-DD HH:MM:SS.")

    # TOTAL PRICE VALIDATION
    @staticmethod
    def validate_total_price(total_price):
        if total_price is None:
            raise ValueError("total price е задължително поле.")
        if not isinstance(total_price, (int, float)):
            raise ValueError("total price трябва да е число.")
        if total_price < 0:
            raise ValueError("total price не може да е отрицателно.")

    # ADVANCED SEARCH FILTERS
    @staticmethod
    def validate_search_filters(start_date, end_date, min_total, max_total):
        """Валидации за разширено търсене (View вече не ги прави)."""
        from datetime import datetime

        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except:
                raise ValueError("Невалидна начална дата.")

        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except:
                raise ValueError("Невалидна крайна дата.")

        if min_total is not None:
            try:
                float(min_total)
            except:
                raise ValueError("Минималната стойност трябва да е число.")

        if max_total is not None:
            try:
                float(max_total)
            except:
                raise ValueError("Максималната стойност трябва да е число.")

    # MASTER VALIDATION
    @staticmethod
    def validate_all(product, customer, quantity, unit, unit_price,
                     movement_id, date=None, total_price=None):

        InvoiceValidator.validate_product(product)
        InvoiceValidator.validate_customer(customer)
        InvoiceValidator.validate_quantity(quantity)
        InvoiceValidator.validate_unit(unit)
        InvoiceValidator.validate_unit_price(unit_price)
        InvoiceValidator.validate_movement_id(movement_id)

        if date is not None:
            InvoiceValidator.validate_date(date)

        if total_price is not None:
            InvoiceValidator.validate_total_price(total_price)
