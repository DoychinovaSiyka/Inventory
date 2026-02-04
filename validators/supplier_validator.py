import re

class SupplierValidator:

    # Регулярен израз за имейл
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    # Регулярен израз за телефон (международен формат)
    phone_regex = re.compile(r"^\+?\d{7,15}$")

    @staticmethod
    def validate_name(name):
        if not name or not name.strip():
            raise ValueError("Името на доставчика е задължително.")

        if len(name.strip()) < 2:
            raise ValueError("Името на доставчика трябва да съдържа поне 2 символа.")

    @staticmethod
    def validate_contact(contact):
        if not contact or not contact.strip():
            raise ValueError("Контактната информация е задължителна.")

        contact = contact.strip()

        # Валиден имейл?
        if SupplierValidator.email_regex.match(contact):
            return True

        # Валиден телефон?
        if SupplierValidator.phone_regex.match(contact):
            return True

        raise ValueError("Контактът трябва да бъде валиден имейл или телефон.")

    @staticmethod
    def validate_address(address):
        if not address or not address.strip():
            raise ValueError("Адресът е задължителен.")

        if len(address.strip()) < 3:
            raise ValueError("Адресът трябва да съдържа поне 3 символа.")

    @staticmethod
    def validate_unique(name, suppliers):
        for s in suppliers:
            if s.name.lower() == name.lower():
                raise ValueError("Доставчик с това име вече съществува.")

    @staticmethod
    def validate_all(name, contact, address):
        SupplierValidator.validate_name(name)
        SupplierValidator.validate_contact(contact)
        SupplierValidator.validate_address(address)
