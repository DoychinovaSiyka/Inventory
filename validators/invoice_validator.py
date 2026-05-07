import uuid
from datetime import datetime


class InvoiceValidator:

    @staticmethod
    def parse_float(value, field_name="Стойност"):
        if value is None or str(value).strip() == "":
            raise ValueError(f"{field_name} е задължително поле.")

        # Премахваме валути и оправяме запетаите
        cleaned = (str(value).replace("лв.", "").replace("лв", "")
                   .replace(" ", "").replace(",", "."))

        try:
            number = float(cleaned)
            return number
        except ValueError:
            raise ValueError(f"{field_name} трябва да бъде валидно число (напр. 12.50).")

    @staticmethod
    def validate_uuid(value, field_name="ID"):
        if value is None:
            return

        val_str = str(value).strip()

        # Ако е пълно UUID, го проверяваме по стандарт
        if len(val_str) == 36:
            try:
                uuid.UUID(val_str)
            except:
                raise ValueError(f"Невалиден пълен UUID формат за {field_name}.")
        # Ако е кратко ID, проверяваме само дали е от позволени символи
        elif len(val_str) >= 4:
            if not all(c.isalnum() or c == "-" for c in val_str):
                raise ValueError(f"ID-то съдържа невалидни символи.")
        else:
            raise ValueError(f"{field_name} трябва да е поне 4 символа (кратък код) или пълен UUID.")

    @staticmethod
    def validate_product(product):
        if not product or not isinstance(product, str) or len(product.strip()) < 2:
            raise ValueError("Името на продукта е задължително и трябва да е поне 2 символа.")

    @staticmethod
    def validate_customer(customer):
        if not customer or not isinstance(customer, str) or len(customer.strip()) < 2:
            raise ValueError("Името на клиента е задължително.")

    @staticmethod
    def validate_quantity(quantity):
        try:
            q = float(quantity)
            if q <= 0:
                raise ValueError("Количеството трябва да е положително число.")
        except (ValueError, TypeError):
            raise ValueError("Количеството трябва да е валидно число.")

    @staticmethod
    def validate_unit_price(unit_price):
        try:
            p = float(unit_price)
            if p <= 0:
                raise ValueError("Единичната цена трябва да е положителна.")
        except (ValueError, TypeError):
            raise ValueError("Единичната цена трябва да е валидно число.")

    @staticmethod
    def validate_total_price(total_price, quantity, unit_price):
        """Проверка на математическата логика на фактурата."""
        try:
            total = float(total_price)
            expected = round(float(quantity) * float(unit_price), 2)

            # Позволяваме разлика до 1 стотинка заради евентуални закръгляния
            if abs(expected - total) > 0.01:
                raise ValueError(f"Грешка в сметката! {quantity} x {unit_price} = {expected}, а е записано {total}")
        except (ValueError, TypeError):
            raise ValueError("Грешка при изчисляване на сумите.")

    @staticmethod
    def validate_unit(unit):
        if not unit or not isinstance(unit, str):
            raise ValueError("Мерната единица е задължителна.")

    @staticmethod
    def validate_date(date_str):
        if not date_str:
            raise ValueError("Датата е задължителна.")

        # Поддържаме двата основни формата в системата
        formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]
        for fmt in formats:
            try:
                datetime.strptime(str(date_str), fmt)
                return
            except ValueError:
                pass

        raise ValueError("Невалидна дата. Моля, използвайте формат ГГГГ-ММ-ДД.")

    @staticmethod
    def validate_all(product, customer, quantity, unit, unit_price, movement_id, total_price, date=None):
        InvoiceValidator.validate_product(product)
        InvoiceValidator.validate_customer(customer)
        InvoiceValidator.validate_quantity(quantity)
        InvoiceValidator.validate_unit(unit)
        InvoiceValidator.validate_unit_price(unit_price)
        InvoiceValidator.validate_total_price(total_price, quantity, unit_price)
        InvoiceValidator.validate_uuid(movement_id, "Movement ID")
        if date:
            InvoiceValidator.validate_date(date)

    @staticmethod
    def validate_movement_for_invoice(movement):
        m_type = str(movement.movement_type.name).upper()
        if m_type != "OUT":
            raise ValueError(f"Не може да се издаде фактура за движение тип '{m_type}'. Трябва да е продажба (OUT).")

    @staticmethod
    def validate_search_filters(start_date, end_date, min_total, max_total):
        if start_date:
            InvoiceValidator.validate_date(start_date)
        if end_date:
            InvoiceValidator.validate_date(end_date)
        if min_total is not None and str(min_total).strip() != "":
            InvoiceValidator.parse_float(min_total, "Минимална сума")
        if max_total is not None and str(max_total).strip() != "":
            InvoiceValidator.parse_float(max_total, "Максимална сума")