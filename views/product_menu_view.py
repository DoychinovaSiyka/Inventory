from views.menu import Menu, MenuItem
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from controllers.location_controller import LocationController
from models.user import User
from views.product_sort_view import ProductSortView
from views.password_utils import require_password


def format_lv(value):
    return f"{value:.2f} лв."


def _read_int(prompt):
    try:
        raw = input(prompt).strip()
        return int(raw) if raw else None
    except ValueError:
        print("Стойността трябва да е цяло число.")
        return None


def _read_float(prompt):
    raw = input(prompt)
    raw = raw.replace(",", ".").strip()
    if not raw: return None

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
    def __init__(self, product_controller: ProductController,
                 category_controller: CategoryController,
                 location_controller: LocationController,
                 activity_log_controller=None):
        self.product_controller = product_controller
        self.category_controller = category_controller
        self.location_controller = location_controller
        self.activity_log = activity_log_controller
        self.sort_view = ProductSortView(product_controller)

    def show_menu(self, user: User):
        # Ограничаваме достъпа според ролята
        readonly = user.role in ["Operator", "Anonymous"]

        menu = Menu("МЕНЮ ПРОДУКТИ", [
            MenuItem("1", "Създаване на продукт", self.create_product),
            MenuItem("2", "Премахване на продукт", self.remove_product),
            MenuItem("3", "Редактиране на продукт", self.edit_product),
            MenuItem("4", "Покажи всички продукти",
                     self.show_all_protected if user.role == "Operator" else self.show_all),
            MenuItem("5", "Търсене", self.search),
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
            # Проверка за права
            if readonly and choice in ["1", "2", "3", "9", "10"]:
                print(f"[!] Функцията не е достъпна за роля: {user.role}")
                continue

            result = menu.execute(choice, user)
            if result == "break": break

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
            print("Няма налични категории.")
            return

        print("\nНалични категории:")
        for i, c in enumerate(categories):
            # Показваме дали е подкатегория за яснота
            parent_info = ""
            if hasattr(c, 'parent_id') and c.parent_id:
                parent_info = f" (Подкатегория на {c.parent_id})"
            print(f"{i}. {c.name}{parent_info}")

        cat_idx = _read_int("Изберете категория (номер): ")
        if cat_idx is None or not (0 <= cat_idx < len(categories)):
            return
        category_id = categories[cat_idx].category_id

        locations = self.location_controller.get_all()
        if not locations:
            print("Грешка: Няма налични складове!")
            return

        print("\nНалични локации (складове):")
        for i, loc in enumerate(locations):
            print(f"{i}. [{loc.location_id}] {loc.name}")

        loc_idx = _read_int("Изберете склад (номер): ")
        if loc_idx is None or not (0 <= loc_idx < len(locations)):
            return
        location_id = locations[loc_idx].location_id

        try:
            # Използваме user.user_id (или user.id според твоя модел)
            u_id = getattr(user, 'user_id', getattr(user, 'id', 'unknown'))
            self.product_controller.add(
                name=name, description=description, price=price,
                quantity=quantity, unit=unit, category_ids=[category_id],
                location_id=location_id,
                supplier_id=None, user_id=u_id
            )
            print(f"[Успех] Продуктът е зачислен в {location_id}.")
        except ValueError as e:
            print("Грешка:", e)

    def show_all(self, _):
        products = self.product_controller.get_all()
        if not products:
            print("Няма налични продукти.")
            return

        print("\n=== Списък с продукти ===")
        print(f"{'ID':<3} | {'Име':<15} | {'Склад':<6} | {'Наличност':<10} | {'Цена'}")
        print("-" * 65)
        for p in products:
            print(
                f"{p.product_id:<3} | {p.name[:15]:<15} | {p.location_id:<6} | {p.quantity:>5} {p.unit:<4} | {format_lv(p.price)}")

    @require_password("parola123")
    def show_all_protected(self, user):
        self.show_all(user)

    def remove_product(self, user):
        print("\n=== Премахване на продукт ===")
        pid = input("ID на продукт: ").strip()
        try:
            u_id = getattr(user, 'user_id', getattr(user, 'id', 'unknown'))
            self.product_controller.remove_by_id(pid, u_id)
            print("Продуктът е премахнат.")
        except ValueError as e:
            print("Грешка:", e)

    def edit_product(self, _):
        print("\n=== Редактиране на продукт ===")
        pid = input("ID на продукт: ").strip()
        product = self.product_controller.get_by_id(pid)
        if not product:
            print("Няма такъв продукт.")
            return

        print(f"Редактиране на: {product.name} (в склад {product.location_id})")
        new_name = input(f"Ново име ({product.name}): ").strip() or product.name
        new_description = input(f"Ново описание ({product.description}): ").strip() or product.description

        price_input = input(f"Нова цена ({product.price}): ").strip()
        new_price = float(price_input.replace(",", ".")) if price_input else product.price

        qty_input = input(f"Ново количество ({product.quantity}): ").strip()
        new_quantity = float(qty_input.replace(",", ".")) if qty_input else product.quantity

        try:
            product.name = new_name
            product.description = new_description
            product.price = new_price
            product.quantity = new_quantity
            product.update_modified()
            self.product_controller.save_changes()
            print("Продуктът е обновен успешно.")
        except ValueError as e:
            print("Грешка:", e)

    def search(self, _):
        keyword = input("Търсене (име/описание): ").strip().lower()
        results = self.product_controller.search(keyword)
        if not results:
            print("Няма намерени продукти.")
            return
        for p in results:
            print(f"{p.product_id} | {p.name} | Склад: {p.location_id} | {p.quantity} {p.unit} | {format_lv(p.price)}")

    def sort_menu(self, _):
        self.sort_view.show_menu()

    @require_password("parola123")
    def sort_menu_protected(self, user):
        self.sort_menu(user)

    def average_price(self, _):
        avg = self.product_controller.average_price()
        print(f"Средна цена: {format_lv(avg)}")

    def filter_by_category(self, _):
        categories = self.category_controller.get_all()
        if not categories:
            print("Няма категории.")
            return

        for i, c in enumerate(categories):
            print(f"{i}. {c.name}")

        idx = _read_int("Изберете категория (номер): ")
        if idx is not None and 0 <= idx < len(categories):
            selected_cat = categories[idx]

            # НАДГРАЖДАНЕ: Намираме всички подкатегории, за да филтрираме по цялото "дърво"
            target_ids = [selected_cat.category_id]
            for c in categories:
                if hasattr(c, 'parent_id') and c.parent_id == selected_cat.category_id:
                    target_ids.append(c.category_id)

            results = self.product_controller.filter_by_multiple_category_ids(target_ids)

            if not results:
                print(f"Няма продукти в категория '{selected_cat.name}' (и нейните подкатегории).")
                return

            print(f"\n--- Продукти в {selected_cat.name} ---")
            for p in results:
                print(f"{p.name} | Склад: {p.location_id} | {format_lv(p.price)} | {p.quantity} {p.unit}")

    def increase_quantity(self, user):
        pid = input("ID на продукт: ").strip()
        amount = _read_float("Количество за добавяне: ")
        if amount:
            try:
                u_id = getattr(user, 'user_id', getattr(user, 'id', 'unknown'))
                self.product_controller.increase_quantity(pid, amount, u_id)
                print("Количеството е увеличено.")
            except ValueError as e:
                print("Грешка:", e)

    def decrease_quantity(self, user):
        pid = input("ID на продукт: ").strip()
        amount = _read_float("Количество за изваждане: ")
        if amount:
            try:
                u_id = getattr(user, 'user_id', getattr(user, 'id', 'unknown'))
                self.product_controller.decrease_quantity(pid, amount, u_id)
                print("Количеството е намалено.")
            except ValueError as e:
                print("Грешка:", e)

    def low_stock(self, _):
        low = self.product_controller.check_low_stock()
        if not low: print("Няма продукти с критична наличност.")
        for p in low: print(f"ВНИМАНИЕ: {p.name} ({p.quantity} {p.unit}) в склад {p.location_id}")

    def most_expensive(self, _):
        p = self.product_controller.most_expensive()
        if p: print(f"Най-скъп продукт: {p.name} ({p.location_id}) - {format_lv(p.price)}")

    def cheapest(self, _):
        p = self.product_controller.cheapest()
        if p: print(f"Най-евтин продукт: {p.name} ({p.location_id}) - {format_lv(p.price)}")

    def total_value(self, _):
        print(f"Обща стойност на инвентара: {format_lv(self.product_controller.total_values())}")

    def group_by_category(self, _):
        groups = self.product_controller.group_by_category()
        for cat_id, prods in groups.items():
            cat = self.category_controller.get_by_id(cat_id)
            print(f"\n--- {cat.name if cat else cat_id} ---")
            for p in prods:
                print(f"  {p.name} (Склад: {p.location_id}) - {p.quantity} {p.unit}")

    def advanced_search(self, _):
        print("\n=== Разширено търсене ===")
        keyword = input("Ключова дума: ").strip() or None
        min_p = _read_float("Мин. цена: ")
        max_p = _read_float("Макс. цена: ")

        results = self.product_controller.search_combined(
            name_keyword=keyword, min_price=min_p, max_price=max_p
        )
        for p in results:
            print(f"{p.product_id} | {p.name} | {p.location_id} | {format_lv(p.price)}")