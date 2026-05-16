from datetime import datetime

class InvoiceValidator:
    """Валидатор за бизнес правилата при работа с фактури."""

    @staticmethod
    def validate_movement_for_invoice(movement):
        """
        Проверява дали складовото движение е подходящо за фактуриране.
        Фактури се издават САМО при продажби (OUT).
        """
        try:
            # Опит за достъп чрез Enum име
            m_type = movement.movement_type.name.upper()
        except AttributeError:
            # Ако е подадено като низ
            m_type = str(movement.movement_type).upper()

        if m_type != "OUT":
            raise ValueError(
                f"Критична грешка: Не може да се издаде фактура за движение тип '{m_type}'. "
                f"Системата позволява фактуриране само на продажби към клиенти (OUT)."
            )

    @staticmethod
    def validate_date(date_str):
        """Валидира формата на датата на документа."""
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
        """Проверява дали фактурата подлежи на анулиране."""
        if not invoice.is_active:
            raise ValueError("Операцията е отказана: Тази фактура вече е анулирана.")
        return True