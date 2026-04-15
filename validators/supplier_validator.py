import re


class SupplierValidator:
    # Регулярен израз за имейл
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    # Регулярен израз за телефон - поддържа формати като +359... или 08...
    phone_regex = re.compile(r"^\+?\d{7,15}$")

    @staticmethod
    def validate_name(name):
        """ Валидира и връща изчистеното име. """
        if not name or not str(name).strip():
            raise ValueError("Името на доставчика е задължително.")
        clean_name = str(name).strip()
        if len(clean_name) < 2:
            raise ValueError("Името на доставчика трябва да съдържа поне 2 символа.")
        return clean_name

    @staticmethod
    def validate_contact(contact):
        """ Проверява имейл/телефон и връща изчистения контакт. """
        if not contact or not str(contact).strip():
            raise ValueError("Контактната информация е задължителна.")

        clean_contact = str(contact).strip()
        # Проверка чрез Regex
        is_email = SupplierValidator.email_regex.match(clean_contact)
        is_phone = SupplierValidator.phone_regex.match(clean_contact)

        if not (is_email or is_phone):
            raise ValueError("Контактът трябва да бъде валиден имейл или телефон (напр. +359...).")

        return clean_contact

    @staticmethod
    def validate_address(address):
        """ Валидира и връща изчистения адрес. """
        if not address or not str(address).strip():
            raise ValueError("Адресът е задължителен.")
        clean_address = str(address).strip()
        if len(clean_address) < 3:
            raise ValueError("Адресът трябва да съдържа поне 3 символа.")

        return clean_address

    @staticmethod
    def validate_unique(name, suppliers):
        """ Проверява за дублиращи се имена (case-insensitive). """
        clean_name = str(name).strip().lower()
        for s in suppliers:
            if s.name.lower() == clean_name:
                raise ValueError(f"Доставчик с името '{name}' вече съществува.")

    @staticmethod
    def validate_all(name, contact, address):
        """ Изпълнява всички проверки наведнъж. """
        SupplierValidator.validate_name(name)
        SupplierValidator.validate_contact(contact)
        SupplierValidator.validate_address(address)
        return True