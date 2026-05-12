from datetime import datetime

class InvoiceValidator:

    @staticmethod
    def validate_movement_for_invoice(movement):
        try:
            m_type = movement.movement_type.name.upper()
        except AttributeError:
            m_type = str(movement.movement_type).upper()

        if m_type != "OUT":
            raise ValueError(f"Не може да се издаде фактура за движение тип '{m_type}'. "
                f"Фактури се генерират само при продажби (OUT).")

    @staticmethod
    def validate_date(date_str):
        if not date_str:
            raise ValueError("Датата е задължителна за генериране на документ.")

        formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]
        for fmt in formats:
            try:
                datetime.strptime(str(date_str), fmt)
                return True
            except ValueError:
                continue
        raise ValueError("Невалиден формат на датата. Очаква се ГГГГ-ММ-ДД.")

    @staticmethod
    def validate_cancellation(invoice):
        if not invoice.is_active:
            raise ValueError("Тази фактура вече е анулирана.")
        return True