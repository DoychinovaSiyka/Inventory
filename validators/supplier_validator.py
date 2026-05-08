import re


class SupplierValidator:
    # Имейл регекс
    email_regex = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    # Телефон регекс
    phone_regex = re.compile(r"\+?[\d\s\-]{7,15}")

    @staticmethod
    def validate_name(name):
        if not name or not str(name).strip():
            raise ValueError("Името на доставчика е задължително.")

        clean = str(name).strip()
        if len(clean) < 2:
            raise ValueError("Името трябва да е поне 2 символа.")

        if clean.isdigit():
            raise ValueError("Името не може да е само цифри.")
        return clean

    @staticmethod
    def validate_contact(contact):
        if not contact or not str(contact).strip():
            raise ValueError("Контактната информация е задължителна.")

        clean = str(contact).strip()
        has_email = SupplierValidator.email_regex.search(clean)
        has_phone = SupplierValidator.phone_regex.search(clean)
        if not (has_email or has_phone):
            raise ValueError("Контактът трябва да съдържа телефон или имейл.")
        return clean

    @staticmethod
    def validate_address(address):
        if not address or not str(address).strip():
            raise ValueError("Адресът е задължителен.")

        clean = str(address).strip()
        if len(clean) < 3:
            raise ValueError("Адресът е твърде кратък.")
        return clean

    @staticmethod
    def validate_unique(name, suppliers, exclude_id=None):
        clean = str(name).strip().lower()
        for s in suppliers:
            if exclude_id and str(s.supplier_id) == str(exclude_id):
                continue
            if s.name.lower() == clean:
                raise ValueError(f"Доставчик '{name}' вече съществува.")

    @staticmethod
    def validate_exists(supplier_id, controller):
        if not supplier_id:
            raise ValueError("Трябва да въведете ID.")

        supplier = controller.get_by_id(str(supplier_id).strip())
        if not supplier:
            raise ValueError(f"Доставчик с код '{supplier_id}' не е намерен.")

        return supplier

    @staticmethod
    def validate_all(name, contact, address):
        SupplierValidator.validate_name(name)
        SupplierValidator.validate_contact(contact)
        SupplierValidator.validate_address(address)
