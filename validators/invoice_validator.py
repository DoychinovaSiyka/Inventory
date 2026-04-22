import uuid
from datetime import datetime


class InvoiceValidator:

    # Парсване на числа от текст (пример: "12,50 лв")
    @staticmethod
    def parse_float(value, field_name="Стойност"):
        if value is None or str(value).strip() == "":
            raise ValueError(f"{field_name} е задължително поле.")

        cleaned = (str(value).replace("лв.", "").replace("лв", "")
                   .replace(" ", "").replace(",", "."))

        try:
            number = float(cleaned)
        except ValueError:
            raise ValueError(f"{field_name} трябва да бъде валидно число.")

        return number


    @staticmethod
    def validate_uuid(value, field_name="ID"):
        if value is None:
            return
        try:
            uuid.UUID(str(value))
        except:
            raise ValueError(f"Невалиден UUID формат за {field_name}: {value}")

    # Основни проверки за полета
    @staticmethod
    def validate_product(product):
        if not product or not isinstance(product, str):
            raise ValueError("Името на продукта е задължително.")

    @staticmethod
    def validate_customer(customer):
        if not customer or not isinstance(customer, str):
            raise ValueError("Клиентът е задължителен.")

    @staticmethod
    def validate_quantity(quantity):
        try:
            q = float(quantity)
        except:
            raise ValueError("Количеството трябва да е валидно число.")
        if q <= 0:
            raise ValueError("Количеството трябва да е положително.")

    @staticmethod
    def validate_unit_price(unit_price):
        try:
            p = float(unit_price)
        except:
            raise ValueError("Единичната цена трябва да е валидно число.")
        if p <= 0:
            raise ValueError("Единичната цена трябва да е положителна.")

    # Проверка - total = quantity * unit_price
    @staticmethod
    def validate_total_price(total_price, quantity, unit_price):
        try:
            total = float(total_price)
        except:
            raise ValueError("Общата сума трябва да е валидно число.")

        try:
            expected = round(float(quantity) * float(unit_price), 2)
        except:
            raise ValueError("Невалидни стойности за изчисляване на общата сума.")

        if abs(expected - total) > 0.01:
            raise ValueError(f"Грешка в сметката! Очаквано: {expected}, Получено: {total}")

    @staticmethod
    def validate_unit(unit):
        if not unit or not isinstance(unit, str):
            raise ValueError("Мерната единица е задължителна.")


    @staticmethod
    def validate_date(date_str):
        if not date_str:
            raise ValueError("Датата е задължителна.")

        formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return
            except ValueError:
                pass

        raise ValueError("Невалидна дата. Използвайте YYYY-MM-DD.")

    # Пълна проверка на фактура
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

    # Фактура може да се прави само при OUT движение
    @staticmethod
    def validate_movement_for_invoice(movement):
        m_type = str(movement.movement_type.name).upper()
        if m_type != "OUT":
            raise ValueError("Фактура може да се генерира само при продажба (OUT).")

    # Проверки за филтри при търсене
    @staticmethod
    def validate_search_filters(start_date, end_date, min_total, max_total):
        if start_date:
            InvoiceValidator.validate_date(start_date)
        if end_date:
            InvoiceValidator.validate_date(end_date)

        if min_total is not None:
            InvoiceValidator.parse_float(min_total, "Минимална сума")
        if max_total is not None:
            InvoiceValidator.parse_float(max_total, "Максимална сума")
