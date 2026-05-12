class InventoryValidator:
    """
    Валидатор за инвентара и справките.
    Осигурява интегритет на данните преди показване в отчетите.
    """

    @staticmethod
    def validate_string(text, field_name, min_len=2):
        if not text or not isinstance(text, str):
            raise ValueError(f"{field_name} трябва да бъде текстово поле.")
        clean_text = text.strip()
        if len(clean_text) < min_len:
            raise ValueError(f"{field_name} трябва да е поне {min_len} символа.")
        return clean_text

    @staticmethod
    def parse_and_validate_number(value, field_name="Количество"):
        """
        Приема числа или стрингове (напр. '10.5 лв', '5 бр'), изчиства ги
        и проверява дали са валидни. Преместено тук от ReportController.
        """
        if value is None:
            return 0.0

        if isinstance(value, (int, float)):
            val = float(value)
        else:
            # Изчистване на стринга от мерни единици и интервали
            cleaned = "".join(ch for ch in str(value) if ch.isdigit() or ch == "." or ch == ",")
            cleaned = cleaned.replace(",", ".")
            try:
                val = float(cleaned)
            except ValueError:
                val = 0.0

        if val < 0:
            raise ValueError(f"{field_name} не може да бъде отрицателно.")
        return val

    @staticmethod
    def validate_stock_availability(product_name, requested_qty, available_qty, location_name):
        """Проверява дали има достатъчно наличност за операция."""
        if requested_qty > available_qty:
            raise ValueError(
                f"Недостатъчна наличност на '{product_name}'! "
                f"В {location_name} има {available_qty}, а се изискват {requested_qty}.")

    @staticmethod
    def validate_report_result(data):
        """Гарантира, че данните за отчета са в правилен формат преди показване."""
        if not isinstance(data, list):
            raise ValueError("Грешка при генериране на справката: Невалиден формат на данните.")
        return True

    @staticmethod
    def validate_move_locations(from_wh_id, to_wh_id):
        if not from_wh_id or not to_wh_id:
            raise ValueError("MOVE операцията изисква изходен и целеви склад.")
        if str(from_wh_id) == str(to_wh_id):
            raise ValueError("Изходният и целевият склад не могат да бъдат еднакви.")