import re


class SupplierValidator:
    email_regex = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    phone_regex = re.compile(r"\+?[\d\s\-]{7,15}")

    @staticmethod
    def validate_name(name):
        clean = str(name).strip()
        if not clean or len(clean) < 2:
            raise ValueError("Името трябва да е поне 2 символа.")
        if clean.isdigit():
            raise ValueError("Името не може да е само цифри.")
        return clean


    @staticmethod
    def validate_unique_name(name, suppliers, exclude_id=None):
        clean = str(name).strip().lower()
        for s in suppliers:
            if s.name.lower() == clean and str(s.supplier_id) != str(exclude_id):
                raise ValueError(f"Доставчик с име '{name}' вече съществува.")
        return name



    @staticmethod
    def validate_contact(contact):
        clean = str(contact).strip()
        if not (SupplierValidator.email_regex.search(clean) or SupplierValidator.phone_regex.search(clean)):
            raise ValueError("Контактът трябва да съдържа валиден телефон или имейл.")
        return clean



    @staticmethod
    def validate_address(address):
        clean = str(address).strip()
        if len(clean) < 3:
            raise ValueError("Адресът е твърде кратък.")
        return clean