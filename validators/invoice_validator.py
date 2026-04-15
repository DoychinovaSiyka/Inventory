import uuid
from datetime import datetime


class InvoiceValidator:

    @staticmethod
    def parse_float(value, field_name):
        """Превръща текст в число безопасно. Използва се в контролера."""
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Полето '{field_name}' трябва да бъде валидно число.")

    @staticmethod
    def validate_uuid(value, field_name="ID"):
        if value is None: return
        try:
            uuid.UUID(str(value))
        except:
            raise ValueError(f"Невалиден UUID формат за {field_name}: {value}")

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
        if quantity is None or not isinstance(quantity, (int, float)) or quantity <= 0:
            raise ValueError("Количеството трябва да е положително число.")

    @staticmethod
    def validate_unit_price(unit_price):
        if unit_price is None or not isinstance(unit_price, (int, float)) or unit_price <= 0:
            raise ValueError("Единичната цена трябва да е положително число.")

    @staticmethod
    def validate_total_price(total_price, quantity, unit_price):
        """Проверява дали сметката е вярна."""
        if total_price is None:
            raise ValueError("Общата сума е задължителна.")

        # Проверка за математическа точност (до 2-рия знак)
        expected_total = round(float(quantity) * float(unit_price), 2)
        if abs(float(total_price) - expected_total) > 0.01:
            raise ValueError(f"Грешка в сметката! Очаквано: {expected_total}, Получено: {total_price}")

    @staticmethod
    def validate_date(date_str):
        if not date_str:
            raise ValueError("Дадата е задължителна.")
        formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return
            except ValueError:
                continue
        raise ValueError("Невалидна дата. Използвайте YYYY-MM-DD.")

    @staticmethod
    def validate_all(product, customer, quantity, unit, unit_price, movement_id, total_price, date=None):
        """Главен метод за проверка на всички полета."""
        InvoiceValidator.validate_product(product)
        InvoiceValidator.validate_customer(customer)
        InvoiceValidator.validate_quantity(quantity)
        InvoiceValidator.validate_unit_price(unit_price)
        InvoiceValidator.validate_total_price(total_price, quantity, unit_price)
        InvoiceValidator.validate_uuid(movement_id, "Movement ID")

        if not unit: raise ValueError("Мерната единица е задължителна.")
        if date: InvoiceValidator.validate_date(date)

    @staticmethod
    def validate_movement_for_invoice(movement):
        """Проверява дали стоковото движение е изходящо."""
        # Проверка дали типът е "OUT" (в зависимост от имплементация)
        m_type = str(movement.movement_type).upper()
        if "OUT" not in m_type:
            raise ValueError("Фактура може да се генерира само при продажба (OUT).")

    @staticmethod
    def validate_search_filters(start_date, end_date, min_total, max_total):
        """Валидира параметрите за разширено търсене."""
        if start_date: InvoiceValidator.validate_date(start_date)
        if end_date: InvoiceValidator.validate_date(end_date)
        if min_total is not None: InvoiceValidator.parse_float(min_total, "Минимална сума")
        if max_total is not None: InvoiceValidator.parse_float(max_total, "Максимална сума")