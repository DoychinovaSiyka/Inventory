from views.menu import Menu, MenuItem
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from models.user import User
from views.product_sort_view import ProductSortView
from views.password_utils import require_password


# Четене на цяло число от потребителя
def _read_int(prompt):
    try:
        return int(input(prompt))
    except ValueError:
        print("Стойността трябва да е цяло число.")
        return None


# Четене на число с плаваща запетая (позволява 5,5 → 5.5 и игнорира текст след числото)
def _read_float(prompt):
    raw = input(prompt)
    raw = raw.replace(",", ".").strip()

    cleaned = ""
    for ch in raw:
        if ch.isdigit() or ch in ".-":
            cleaned += ch
        else:
            break

    try:
        return float(cleaned)
    except ValueError:
        print("Стойността трябва да е число.")
        return None


class ProductView:
    def __init__(self, product_controller: ProductController, category_controller: CategoryController, activity_log_controller=None):
        self.product_controller = product_controller
        self.category_controller = category_controller
        self.activity_log = activity_log_controller
        self.sort_view = ProductSortView(product_controller)

    # Основно меню за работа с продукти
    def show_menu(self, user: User):
        readonly = user.role != "Admin"

        menu = Menu("МЕНЮ ПРОДУКТИ", [
            MenuItem("1", "Създаване на продукт", self.create_product),
            MenuItem("2", "Премахване на продукт", self.remove_product),
            MenuItem("3", "Редактиране на продукт", self.edit_product),

            # За оператор показването на всички продукти е защитено с парола
            MenuItem("4", "Покажи всички продукти",
                     self.show_all_protected if user.role == "Operator" else self.show_all),

            MenuItem("5", "Търсене", self.search),

            # Сортирането също е защитено за оператор
            MenuItem("6", "Сортиране на продукти",
                     self.sort_menu_protected if user.role == "Operator" else self.sort_menu),

            MenuItem("7", "Средна цена", self.average_price),
            MenuItem("8", "Филтриране по категория", self.filter_by_category),
            MenuItem("9", "Увеличаване на количество", self.increase_quantity),
            MenuItem("10", "Намаляване на количество", self.decrease_quantity),
            MenuItem("11", "Продукти с ниска наличност", self.low_stock),
            MenuItem("12", "Най-скъп продукт", self.most_expensive),
            MenuItem("13", "Най-евтин продукт", self.cheapest),
            MenuItem("14", "Обща стойност на склада", self.total_value),
            MenuItem("15", "Групиране по категории", self.group_by_category),
            MenuItem("16", "Разширено търсене", self.advanced_search),
            MenuItem("0", "Назад", lambda u: "break")
        ])

        while True:
            choice = menu.show()

            # Ограничения за оператор
            if readonly and choice in ["1", "2", "3", "9", "10"]:
                print("Тази функция не е достъпна за оператор.")
                continue

            result = menu.execute(choice, user)
            if result == "break":
                break

    # Показване на всички продукти (за оператор е защитено с парола)
    @require_password("parola123")
    def show_all_protected(self, _):
        products = self.product_controller.get_all()
        if not products:
            print("Няма налични продукти.")
            return

        print("\n=== Списък с продукти ===")
        for p in products:
            print(f"{p.product_id} | {p.name} | {p.quantity} {p.unit} | {p.price} лв.")

    # 1. Създаване на продукт
    def create_product(self, user):
        print("\n=== Създаване на продукт ===")
        name = input("Име: ").strip()
        description = input("Описание: ").strip()
        price = _read_float("Цена: ")
        quantity = _read_float("Количество: ")
        unit = input("Мерна единица (бр., кг, л...): ").strip()

        if price is None or quantity is None:
            print("Невалидни стойности.")
            return

        categories = self.category_controller.get_all()
        if not categories:
            print("Няма категории. Създайте категория първо.")
            return

        print("\nКатегории:")
        for i, c in enumerate(categories):
            print(f"{i}. {c.name}")

        raw = input("Изберете категория (номер): ").strip()
        if not raw.isdigit():
            print("Невалиден избор.")
            return

        idx = int(raw)
        if idx < 0 or idx >= len(categories):
            print("Невалиден индекс.")
            return

        category_id = categories[idx].category_id

        try:
            self.product_controller.add(
                name=name,
                description=description,
                price=price,
                quantity=quantity,
                unit=unit,
                category_ids=[category_id],
                supplier_id=None,
                user_id=user.id
            )
            print("Продуктът е създаден успешно.")
        except ValueError as e:
            print("Грешка:", e)

    # 2. Премахване на продукт
    def remove_product(self, user):
        print("\n=== Премахване на продукт ===")
        pid = _read_int("ID на продукт: ")
        if pid is None:
            return

        try:
            self.product_controller.remove_by_id(pid, user.id)
            print("Продуктът е премахнат.")
        except ValueError as e:
            print("Грешка:", e)

    # 3. Редактиране на продукт
    def edit_product(self, user):
        print("\n=== Редактиране на продукт ===")
        pid = _read_int("ID на продукт: ")
        if pid is None:
            return

        product = self.product_controller.get_by_id(pid)
        if not product:
            print("Няма такъв продукт.")
            return

        print(f"Редактиране на: {product.name}")

        new_name = input(f"Ново име ({product.name}): ").strip() or product.name
        new_description = input(f"Ново описание ({product.description}): ").strip() or product.description
        new_price = _read_float(f"Нова цена ({product.price}): ") or product.price
        new_quantity = _read_float(f"Ново количество ({product.quantity}): ") or product.quantity

        try:
            product.name = new_name
            product.description = new_description
            product.price = new_price
            product.quantity = new_quantity
            product.update_modified()
            self.product_controller.save_changes()

            print("Продуктът е обновен.")
        except ValueError as e:
            print("Грешка:", e)

    # Показване на всички продукти (за администратор)
    def show_all(self, _):
        products = self.product_controller.get_all()
        if not products:
            print("Няма налични продукти.")
            return

        print("\n=== Списък с продукти ===")
        for p in products:
            print(f"{p.product_id} | {p.name} | {p.quantity} {p.unit} | {p.price} лв.")

    # 5. Търсене
    def search(self, _):
        keyword = input("Търси по име или описание: ").strip().lower()
        if not keyword:
            print("Моля въведете ключова дума.")
            return

        results = self.product_controller.search(keyword)

        if not results:
            print("Няма намерени продукти.")
            return

        print("\n=== Резултати от търсенето ===")
        for p in results:
            print(f"{p.product_id} | {p.name} | {p.quantity} {p.unit} | {p.price} лв.")

    # Защитено сортиране за оператор
    @require_password("parola123")
    def sort_menu_protected(self, _):
        self.sort_view.show_menu()

    # Нормално сортиране за администратор
    def sort_menu(self, _):
        self.sort_view.show_menu()

    # 7. Средна цена
    def average_price(self, _):
        avg = self.product_controller.average_price()
        print(f"Средна цена: {avg:.2f} лв.")

    # 8. Филтриране по категория
    def filter_by_category(self, _):
        categories = self.category_controller.get_all()
        if not categories:
            print("Няма категории.")
            return

        print("\nКатегории:")
        for i, c in enumerate(categories):
            print(f"{i}. {c.name}")

        raw = input("Изберете категория (номер): ").strip()
        if not raw.isdigit():
            print("Невалиден избор.")
            return

        idx = int(raw)
        if idx < 0 or idx >= len(categories):
            print("Невалиден индекс.")
            return

        category_id = categories[idx].category_id
        results = self.product_controller.filter_by_multiple_category_ids([category_id])

        if not results:
            print("Няма продукти в тази категория.")
            return

        print("\n=== Продукти в категорията ===")
        for p in results:
            print(f"{p.product_id} | {p.name} | {p.quantity} {p.unit} | {p.price} лв.")

    # 9. Увеличаване на количество
    def increase_quantity(self, user):
        pid = _read_int("ID: ")
        amount = _read_float("Добави: ")
        if pid is None or amount is None:
            return
        try:
            self.product_controller.increase_quantity(pid, amount, user.id)
            print("Обновено.")

            if self.activity_log:
                self.activity_log.add_log(user.id, "INCREASE_QUANTITY", f"Added {amount} to product ID {pid}")

        except ValueError as e:
            print("Грешка:", e)

    # 10. Намаляване на количество
    def decrease_quantity(self, user):
        pid = _read_int("ID: ")
        amount = _read_float("Извади: ")
        if pid is None or amount is None:
            return
        try:
            self.product_controller.decrease_quantity(pid, amount, user.id)
            print("Обновено.")

            if self.activity_log:
                self.activity_log.add_log(user.id, "DECREASE_QUANTITY", f"Removed {amount} from product ID {pid}")

        except ValueError as e:
            print("Грешка:", e)

    # 11. Продукти с ниска наличност
    def low_stock(self, _):
        low = self.product_controller.check_low_stock()
        if not low:
            print("Няма продукти с ниска наличност.")
        else:
            for p in low:
                print(f"{p.name} | {p.quantity} {p.unit}")

    # 12. Най-скъп продукт
    def most_expensive(self, _):
        p = self.product_controller.most_expensive()
        if not p:
            print("Няма продукти.")
        else:
            print(f"Най-скъп продукт: {p.name} – {p.price} лв.")

    # 13. Най-евтин продукт
    def cheapest(self, _):
        p = self.product_controller.cheapest()
        if not p:
            print("Няма продукти.")
        else:
            print(f"Най-евтин продукт: {p.name} – {p.price} лв.")

    # 14. Обща стойност на склада
    def total_value(self, _):
        value = self.product_controller.total_values()
        print(f"Обща стойност на склада: {value:.2f} лв.")

    # 15. Групиране по категории
    def group_by_category(self, _):
        groups = self.product_controller.group_by_category()

        for category_id, products in groups.items():
            cat_obj = self.category_controller.get_by_id(category_id)
            cat_name = cat_obj.name if cat_obj else category_id

            print(f"\nКатегория: {cat_name}")
            for p in products:
                print(f" - {p.name} | {p.quantity} {p.unit} | {p.price} лв.")

    # 16. Разширено търсене
    def advanced_search(self, _):
        print("\n=== Разширено търсене на продукти ===")

        keyword = input("Ключова дума (име/описание) или Enter за пропуск: ").strip()

        categories = self.category_controller.get_all()
        print("\nКатегории:")
        for i, c in enumerate(categories):
            print(f"{i}. {c.name}")
        raw_cat = input("Изберете категория (номер) или Enter за пропуск: ").strip()
        category_id = None
        if raw_cat.isdigit():
            idx = int(raw_cat)
            if 0 <= idx < len(categories):
                category_id = categories[idx].category_id

        min_price = _read_float("Минимална цена (или Enter): ")
        max_price = _read_float("Максимална цена (или Enter): ")

        min_qty = _read_float("Минимално количество (или Enter): ")
        max_qty = _read_float("Максимално количество (или Enter): ")

        raw_sup = input("ID на доставчик или Enter за пропуск: ").strip()
        supplier_id = int(raw_sup) if raw_sup.isdigit() else None

        results = self.product_controller.search_combined(
            name_keyword=keyword if keyword else None,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            min_qty=min_qty,
            max_qty=max_qty,
            supplier_id=supplier_id
        )

        if not results:
            print("\nНяма намерени продукти.")
            return

        print("\n=== Резултати ===")
        for p in results:
            print(f"{p.product_id} | {p.name} | {p.quantity} {p.unit} | {p.price} лв.")
