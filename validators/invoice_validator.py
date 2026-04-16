import uuid
from datetime import datetime


class InvoiceValidator:

    @staticmethod
    def parse_float(value, field_name="Стойност"):
        """
        Парсва число, като премахва 'лв', интервали и запетаи.
        Връща None при грешка, без да хвърля traceback.
        """
        if value is None or value == "":
            return None

        cleaned = (str(value)
                   .replace("лв.", "")
                   .replace("лв", "")
                   .replace(" ", "")
                   .replace(",", "."))

        try:
            return float(cleaned)
        except ValueError:
            print(f"\nГрешка: Полето '{field_name}' трябва да бъде валидно число.\n")
            return None

    @staticmethod
    def validate_uuid(value, field_name="ID"):
        """Проверка за валиден UUID."""
        if value is None:
            return
        try:
            uuid.UUID(str(value))
        except:
            print(f"\nГрешка: Невалиден UUID формат за {field_name}: {value}\n")
            return None

    @staticmethod
    def validate_product(product):
        """Проверка за име на продукт."""
        if not product or not isinstance(product, str):
            print("\nГрешка: Името на продукта е задължително.\n")
            return None

    @staticmethod
    def validate_customer(customer):
        """Проверка за име на клиент."""
        if not customer or not isinstance(customer, str):
            print("\nГрешка: Клиентът е задължителен.\n")
            return None

    @staticmethod
    def validate_quantity(quantity):
        """Проверка за количество."""
        try:
            if quantity is None or float(quantity) <= 0:
                print("\nГрешка: Количеството трябва да е положително число.\n")
                return None
        except:
            print("\nГрешка: Количеството трябва да е валидно число.\n")
            return None

    @staticmethod
    def validate_unit_price(unit_price):
        """Проверка за единична цена."""
        try:
            if unit_price is None or float(unit_price) <= 0:
                print("\nГрешка: Единичната цена трябва да е положително число.\n")
                return None
        except:
            print("\nГрешка: Единичната цена трябва да е валидно число.\n")
            return None

    @staticmethod
    def validate_total_price(total_price, quantity, unit_price):
        """
        Проверява дали сметката е вярна.
        При грешка не хвърля traceback, а показва нормално съобщение.
        """
        if total_price is None:
            print("\nГрешка: Общата сума е задължителна.\n")
            return None

        try:
            expected_total = round(float(quantity) * float(unit_price), 2)
            if abs(float(total_price) - expected_total) > 0.01:
                print(f"\nГрешка в сметката! Очаквано: {expected_total}, Получено: {total_price}\n")
                return None
        except:
            print("\nГрешка: Невалидни стойности за изчисляване на общата сума.\n")
            return None

    @staticmethod
    def validate_date(date_str):
        """Проверка за валидна дата."""
        if not date_str:
            print("\nГрешка: Датата е задължителна.\n")
            return None

        formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return
            except ValueError:
                continue

        print("\nГрешка: Невалидна дата. Използвайте YYYY-MM-DD.\n")
        return None

    @staticmethod
    def validate_all(product, customer, quantity, unit, unit_price, movement_id, total_price, date=None):
        """
        Главен метод за проверка на всички полета.
        Всички грешки се прихващат и се показват нормално.
        """
        InvoiceValidator.validate_product(product)
        InvoiceValidator.validate_customer(customer)
        InvoiceValidator.validate_quantity(quantity)
        InvoiceValidator.validate_unit_price(unit_price)
        InvoiceValidator.validate_total_price(total_price, quantity, unit_price)
        InvoiceValidator.validate_uuid(movement_id, "Movement ID")

        if not unit:
            print("\nГрешка: Мерната единица е задължителна.\n")

        if date:
            InvoiceValidator.validate_date(date)

    @staticmethod
    def validate_movement_for_invoice(movement):
        """Проверява дали стоковото движение е изходящо."""
        m_type = str(movement.movement_type).upper()
        if "OUT" not in m_type:
            print("\nГрешка: Фактура може да се генерира само при продажба (OUT).\n")
            return None

    @staticmethod
    def validate_search_filters(start_date, end_date, min_total, max_total):
        """
        Валидира параметрите за разширено търсене.
        Всички грешки се прихващат.
        """
        if start_date:
            InvoiceValidator.validate_date(start_date)
        if end_date:
            InvoiceValidator.validate_date(end_date)

        if min_total is not None:
            InvoiceValidator.parse_float(min_total, "Минимална сума")

        if max_total is not None:
            InvoiceValidator.parse_float(max_total, "Максимална сума")
