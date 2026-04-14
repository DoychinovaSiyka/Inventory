from datetime import datetime
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
        from datetime import datetime
        # Приемаме само дата: YYYY-MM-DD
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return
        except ValueError:
            pass
        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return
        except ValueError:
            pass

        # Ако и двата формата са невалидни → грешка
        raise ValueError("Невалидна дата. Позволени формати: YYYY-MM-DD или YYYY-MM-DD HH:MM:SS.")

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

    # MOVEMENT VALIDATION FOR INVOICE CREATION
    @staticmethod
    def validate_movement_for_invoice(movement):
        if movement.movement_type.name != "OUT":
            raise ValueError("Фактура може да се генерира само при OUT движение.")

    # INVOICE EXISTS
    @staticmethod
    def validate_invoice_exists(invoice_id, invoices):
        exists = any(inv.invoice_id == invoice_id for inv in invoices)
        if not exists:
            raise ValueError("Фактурата не е намерена.")

    # DATE RANGE FILTERING
    @staticmethod
    def filter_by_date_range(invoices, start_date, end_date):


        def parse(d):
            try:
                return datetime.strptime(d, "%Y-%m-%d")
            except:
                return None

        start = parse(start_date) if start_date else None
        end = parse(end_date) if end_date else None

        results = invoices

        if start:
            results = [inv for inv in results if parse(inv.date[:10]) and parse(inv.date[:10]) >= start]

        if end:
            results = [inv for inv in results if parse(inv.date[:10]) and parse(inv.date[:10]) <= end]

        return results

    # TOTAL RANGE FILTERING
    @staticmethod
    def filter_by_total_range(invoices, min_total, max_total):
        results = invoices

        if min_total is not None:
            min_total = float(min_total)
            results = [inv for inv in results if inv.total_price >= min_total]

        if max_total is not None:
            max_total = float(max_total)
            results = [inv for inv in results if inv.total_price <= max_total]

        return results
