import uuid
from models.category import Category


class ProductValidator:

    # BASIC FIELD VALIDATION
    @staticmethod
    def validate_uuid(value, field_name="ID"):
        if value is None:
            return None
        try:
            uuid.UUID(str(value))
        except (ValueError, TypeError):
            raise ValueError(f"Невалиден формат за {field_name}: {value}")

    @staticmethod
    def validate_name(name):
        if not name or not isinstance(name, str):
            raise ValueError("Името на продукта е задължително.")
        name = name.strip()
        if len(name) < 3:
            raise ValueError("Името на продукта трябва да съдържа поне 3 символа.")
        return name

    @staticmethod
    def validate_description(description):
        if description is None:
            return ""
        if not isinstance(description, str):
            raise ValueError("Описанието трябва да бъде текстово поле.")
        desc = description.strip()
        if len(desc) < 3:
            raise ValueError("Описанието трябва да съдържа поне 3 символа.")
        if len(desc) > 1000:
            raise ValueError("Описанието не може да надвишава 1000 символа.")
        return desc

    @staticmethod
    def validate_categories(categories):
        if not isinstance(categories, list):
            raise ValueError("Категориите трябва да са списък.")
        if len(categories) == 0:
            raise ValueError("Продуктът трябва да има поне една категория.")
        for c in categories:
            cid = str(c.category_id) if isinstance(c, Category) else str(c)
            if not cid or cid.strip() == "":
                raise ValueError("Списъкът съдържа невалидна или празна категория.")
        return categories

    @staticmethod
    def validate_quantity(quantity):
        """Използва се само при създаване на продукт (начално количество)."""
        try:
            q = float(quantity)
            if q < 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Количеството трябва да е положително число.")
        return round(q, 2)

    @staticmethod
    def validate_unit(unit):
        if not unit or not isinstance(unit, str):
            raise ValueError("Мерната единица е задължителна.")
        if len(unit.strip()) < 1:
            raise ValueError("Мерната единица не може да бъде празна.")
        return unit.strip()

    @staticmethod
    def validate_price(price):
        try:
            p = float(price)
            if p < 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Цената трябва да е положително число.")
        return round(p, 2)

    # PARSING HELPERS
    @staticmethod
    def _parse_float_internal(value, field_name="стойност"):
        if isinstance(value, str):
            value = value.replace("лв.", "").replace("лв", "").strip()
            value = value.replace("lv.", "").replace("lv", "").strip()
            value = value.replace("BGN", "").replace("bgn", "").strip()
            value = value.replace(",", ".").strip()
        try:
            f = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} трябва да е число.")
        return round(f, 2)

    @staticmethod
    def parse_float(value, field_name="стойност"):
        f = ProductValidator._parse_float_internal(value, field_name)
        if f < 0:
            raise ValueError(f"{field_name} не може да е отрицателна.")
        return f

    @staticmethod
    def parse_optional_float(value, field_name="стойност"):
        if value is None or str(value).strip() == "":
            return None
        f = ProductValidator._parse_float_internal(value, field_name)
        if f < 0:
            raise ValueError(f"{field_name} не може да е отрицателна.")
        return f

    @staticmethod
    def parse_int(value, field_name="стойност"):
        if value is None or str(value).strip() == "":
            raise ValueError(f"{field_name} е задължително поле.")
        try:
            i = int(str(value).strip())
        except ValueError:
            raise ValueError(f"{field_name} трябва да е цяло число.")
        if i < 0:
            raise ValueError(f"{field_name} не може да е отрицателно.")
        return i

    # EXISTENCE VALIDATION
    @staticmethod
    def validate_product_exists(product_id, product_controller):
        product = product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт с ID {product_id} не съществува.")
        return product

    @staticmethod
    def validate_category_exists(category_ids, category_controller):
        for cid in category_ids:
            if not category_controller.get_by_id(cid):
                raise ValueError(f"Категория с ID {cid} не съществува.")

    @staticmethod
    def validate_supplier_exists(supplier_id, supplier_controller):
        if supplier_id is None:
            return
        supplier = supplier_controller.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Доставчик с ID {supplier_id} не съществува.")

    # BUSINESS RULES
    @staticmethod
    def validate_unique_name_in_location(name, location_id, products):
        for p in products:
            if p.name.lower() == name.lower() and p.location_id == location_id:
                raise ValueError("Продуктът вече съществува в този склад.")

    def create_product(self, user):
        print("\n  Създаване на продукт  ")
        name = input("Име: ").strip()
        description = input("Описание: ").strip()
        price_raw = input("Цена: ")
        quantity_raw = input("Начално количество (само за първоначално зареждане): ")
        unit = input("Мерна единица (пример: кг., бр., л., пакет): ").strip()

        errors = []
        price = None
        quantity = None

        # Валидация на цена
        try:
            price = ProductValidator.parse_float(price_raw, "Цена")
        except ValueError as e:
            errors.append(str(e))

        # Валидация на количество
        try:
            quantity = ProductValidator.parse_float(quantity_raw, "Количество")
        except ValueError as e:
            errors.append(str(e))

        if errors:
            print()
            for err in errors:
                print(err)
            print("Моля, коригирайте грешките и опитайте отново.\n")
            return

        categories = self.category_controller.get_all()
        if not categories:
            print("Няма категории.")
            return

        print("\nКатегории:")
        for i, c in enumerate(categories):
            print(f"{i}. {c.name} (ID: {c.category_id})")

        cat_raw = input("Изберете категория (номер или Category ID): ").strip()

        try:
            if cat_raw.isdigit():
                cat_idx = ProductValidator.parse_int(cat_raw, "Категория")
                if cat_idx < 0 or cat_idx >= len(categories):
                    raise ValueError("Невалиден избор за Категория.")
                category_id = categories[cat_idx].category_id
            else:
                ProductValidator.validate_uuid(cat_raw, "Category ID")
                category_id = cat_raw
        except Exception as e:
            print(e)
            print("Моля, опитайте отново.\n")
            return

        locations = self.location_controller.get_all()
        if not locations:
            print("Няма складове.")
            return

        print("\nЛокации:")
        for i, loc in enumerate(locations):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")

        loc_raw = input("Изберете локация (номер или Location ID): ").strip()

        try:
            if loc_raw.isdigit():
                loc_idx = ProductValidator.parse_int(loc_raw, "Локация")
                if loc_idx < 0 or loc_idx >= len(locations):
                    raise ValueError("Невалиден избор за Локация.")
                location_id = locations[loc_idx].location_id
            else:
                if not isinstance(loc_raw, str) or loc_raw.strip() == "":
                    raise ValueError("Невалиден Location ID.")
                location_id = loc_raw
        except Exception as e:
            print(e)
            print("Моля, опитайте отново.\n")
            return

        try:
            u_id = user.user_id
            product_data = {
                "name": name,
                "category_ids": [category_id],
                "quantity": quantity,
                "unit": unit,
                "description": description,
                "price": price,
                "supplier_id": None,
                "location_id": location_id
            }

            product = self.product_controller.add(product_data, u_id)
            print("Продуктът е създаден успешно.")

        except ValueError as e:
            print("Грешка:", e)
            print("Моля, опитайте отново.\n")

    # MASTER VALIDATION
    @staticmethod
    def validate_all(product_id, name, categories, quantity, unit, description, price,
                     location_id, supplier_id, tags):
        ProductValidator.validate_uuid(product_id, "Product ID")
        ProductValidator.validate_uuid(supplier_id, "Supplier ID")
        ProductValidator.validate_name(name)
        ProductValidator.validate_categories(categories)
        ProductValidator.validate_quantity(quantity)  # само при create
        ProductValidator.validate_unit(unit)
        ProductValidator.validate_price(price)
        ProductValidator.validate_description(description)
        if tags is not None and not isinstance(tags, list):
            raise ValueError("Tags трябва да са списък.")
