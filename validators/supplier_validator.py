import re


class SupplierValidator:
    # Разширен имейл регекс
    email_regex = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    # Регулярен израз за телефон
    phone_regex = re.compile(r"\+?[\d\s\-]{7,15}")

    @staticmethod
    def validate_name(name):
        """Валидира името на фирмата доставчик."""
        if not name or not str(name).strip():
            raise ValueError("Името на доставчика е задължително.")

        clean_name = str(name).strip()
        if len(clean_name) < 2:
            raise ValueError("Името на доставчика трябва да е поне 2 символа.")

        if clean_name.isdigit():
            raise ValueError("Името на фирмата не може да се състои само от цифри.")

        # Добавени „“ за имената на фирмите
        allowed_name = re.compile(r"^[a-zA-Z0-9а-яА-Я\s\.,\-\"\'№°„“\\/]+$")
        if not allowed_name.match(clean_name):
            raise ValueError("Името съдържа невалидни символи.")

        return clean_name

    @staticmethod
    def validate_contact(contact):
        """Проверява контактна информация (имейл, телефон или комбинация)."""
        if not contact or not str(contact).strip():
            raise ValueError("Контактната информация е задължителна.")

        clean_contact = str(contact).strip()

        # Проверяваме дали съдържа поне нещо, което прилича на телефон или имейл
        has_email = SupplierValidator.email_regex.search(clean_contact)
        has_phone = SupplierValidator.phone_regex.search(clean_contact)

        # Позволени символи за разделители и форматиране
        allowed_chars_pattern = re.compile(r"^[a-zA-Z0-9а-яА-Я._%+\-\s\/|@]+$")

        if not (has_email or has_phone) or not allowed_chars_pattern.match(clean_contact):
            raise ValueError(
                "Невалиден контакт. Въведете имейл, телефон или комбинация от двете "
                "(напр. '0888123456 | office@mail.com')."
            )

        return clean_contact

    @staticmethod
    def validate_address(address):
        """Валидира физически адрес."""
        if not address or not str(address).strip():
            raise ValueError("Адресът е задължителен.")

        clean_address = str(address).strip()
        if len(clean_address) < 3:
            raise ValueError("Адресът е твърде кратък.")

        # КОРЕКЦИЯ: Добавени са „ и “ в списъка с позволени символи
        allowed_address = re.compile(r"^[a-zA-Z0-9а-яА-Я\s\.,\-\"\'№°„“\\/]+$")

        if not allowed_address.match(clean_address):
            raise ValueError("Адресът съдържа невалидни символи (проверете кавичките или специалните знаци).")

        return clean_address

    @staticmethod
    def validate_unique(name, suppliers, exclude_id=None):
        """Проверява за дублиране."""
        clean_name = str(name).strip().lower()
        for s in suppliers:
            if exclude_id and str(s.supplier_id) == str(exclude_id):
                continue
            if s.name.lower() == clean_name:
                raise ValueError(f"Доставчик с името '{name}' вече съществува в базата.")

    @staticmethod
    def validate_exists(supplier_id, controller):
        """Позволява избор чрез ID."""
        if not supplier_id:
            raise ValueError("Трябва да въведете ID на доставчик.")

        supplier = controller.get_by_id(str(supplier_id).strip())

        if not supplier:
            raise ValueError(f"Доставчик с код '{supplier_id}' не беше намерен.")

        return supplier

    @staticmethod
    def validate_all(name, contact, address):
        """Пълна проверка на всички полета."""
        SupplierValidator.validate_name(name)
        SupplierValidator.validate_contact(contact)
        SupplierValidator.validate_address(address)