from menus.menu import Menu, MenuItem
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from models.user import User
from views.product_sort_view import ProductSortView


# Четене на цяло число
def _read_int(prompt):
    try:
        return int(input(prompt))
    except ValueError:
        print("Стойността трябва да е цяло число.")
        return None


# Четене на float (поддържа 5,5 → 5.5 и игнорира мерни единици след числото)
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

    # Главно меню
    def show_menu(self, user: User):
        readonly = user.role != "Admin"

        menu = Menu("МЕНЮ ПРОДУКТИ", [
            MenuItem("1", "Създаване на продукт", self.create_product),
            MenuItem("2", "Премахване на продукт", self.remove_product),
            MenuItem("3", "Редактиране на продукт", self.edit_product),
            MenuItem("4", "Покажи всички продукти", self.show_all),
            MenuItem("5", "Търсене", self.search),
            MenuItem("6", "Сортиране", self.sort_menu),
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

    # 1. Създаване на продукт
    def create_product(self, user):
        name = input("Име: ").strip()
        if not name:
            print("Името не може да е празно.")
            return

        if self.product_controller.exists_by_name(name):
            print("Продукт с това име вече съществува.")
            return

        categories = self.category_controller.get_all()
        if not categories:
            print("Няма категории.")
            return

        print("\nКатегории:")
        for i, c in enumerate(categories):
            print(f"{i}. {c.name}")

        raw_input = input("Изберете категории (пример: 0,2,3): ").strip()

        try:
            parts = [x.strip() for x in raw_input.split(",") if x.strip()]
            selected_indexes = [int(x) for x in parts]

            if any(i < 0 or i >= len(categories) for i in selected_indexes):
                print("Невалиден индекс на категория.")
                return

            selected_categories = [categories[i] for i in selected_indexes]
            category_ids = [c.category_id for c in selected_categories]

        except Exception:
            print("Невалиден избор.")
            return

        quantity = _read_float("Количество: ")
        if quantity is None or quantity < 0:
            print("Невалидно количество.")
            return

        unit = input("Мерна единица (бр., кг, л, г, мл): ").strip()
        if not unit:
            print("Мерната единица е задължителна.")
            return

        description = input("Описание: ")

        price = _read_float("Цена: ")
        if price is None or price < 0:
            print("Невалидна цена.")
            return

        try:
            self.product_controller.add(
                name,
                category_ids,
                quantity,
                unit,
                description,
                price,
                None,
                user.id   # ← ДОБАВЕНО
            )
            print("Продуктът е добавен!")

            # ЛОГВАНЕ
            if self.activity_log:
                self.activity_log.add_log(user.id, "ADD_PRODUCT", f"Added product: {name}")

        except ValueError as e:
            print("Грешка:", e)

    # 2. Премахване
    def remove_product(self, user):
        name = input("Име на продукта за премахване: ").strip()
        if not name:
            print("Името е задължително.")
            return

        if self.product_controller.remove_by_name(name, user.id):   # ← ДОБАВЕНО user.id
            print("Продуктът е премахнат.")

            if self.activity_log:
                self.activity_log.add_log(user.id, "DELETE_PRODUCT", f"Deleted product: {name}")

        else:
            print("Продуктът не е намерен.")

    # 3. Редактиране на продукт
    def edit_product(self, user):
        products = self.product_controller.get_all()
        if not products:
            print("Няма продукти за редактиране.")
            return

        print("\n=== Списък с продукти ===")
        for p in products:
            print(f"{p.product_id} | {p.name} | {p.quantity} {p.unit} | {p.price} лв.")

        pid = _read_int("\nВъведете ID на продукт за редакция: ")
        if pid is None:
            return

        product = self.product_controller.get_by_id(pid)
        if not product:
            print("Продуктът не е намерен.")
            return

        is_admin = user.role == "Admin"

        while True:
            print("\n=== Редактиране на продукт ===")
            print(f"Продукт: {product.name}")

            if is_admin:
                print("1. Промяна на име")
                print("2. Промяна на описание")
                print("3. Промяна на категории")
                print("4. Промяна на количество")
                print("5. Промяна на мерна единица")
                print("6. Промяна на цена")
                print("7. Промяна на доставчик")
                print("0. Назад")
            else:
                print("1. Промяна на количество")
                print("2. Промяна на цена")
                print("3. Промяна на описание")
                print("0. Назад")

            choice = input("Избор: ").strip()

            # Оператор
            if not is_admin:
                if choice == "1":
                    amount = _read_float("Ново количество: ")
                    if amount is not None:
                        diff = amount - product.quantity
                        try:
                            if diff > 0:
                                self.product_controller.increase_quantity(pid, diff, user.id)
                            else:
                                self.product_controller.decrease_quantity(pid, abs(diff), user.id)
                            print("Количество обновено.")

                            if self.activity_log:
                                self.activity_log.add_log(user.id, "EDIT_PRODUCT", f"Updated quantity of product ID {pid}")

                        except ValueError as e:
                            print("Грешка:", e)

                elif choice == "2":
                    price = _read_float("Нова цена: ")
                    if price is not None:
                        try:
                            self.product_controller.update_price(pid, price, user.id)
                            print("Цена обновена.")

                            if self.activity_log:
                                self.activity_log.add_log(user.id, "EDIT_PRODUCT", f"Updated price of product ID {pid}")

                        except ValueError as e:
                            print("Грешка:", e)

                elif choice == "3":
                    desc = input("Ново описание: ").strip()
                    try:
                        self.product_controller.update_description(pid, desc, user.id)
                        print("Описание обновено.")

                        if self.activity_log:
                            self.activity_log.add_log(user.id, "EDIT_PRODUCT", f"Updated description of product ID {pid}")

                    except ValueError as e:
                        print("Грешка:", e)

                elif choice == "0":
                    return

                else:
                    print("Невалиден избор.")
                continue

            # Администратор
            if choice == "1":
                new_name = input("Ново име: ").strip()
                try:
                    self.product_controller.update_name(pid, new_name, user.id)
                    print("Името е обновено.")

                    if self.activity_log:
                        self.activity_log.add_log(user.id, "EDIT_PRODUCT", f"Updated name of product ID {pid}")

                except ValueError as e:
                    print("Грешка:", e)

            elif choice == "2":
                desc = input("Ново описание: ").strip()
                try:
                    self.product_controller.update_description(pid, desc, user.id)
                    print("Описание обновено.")

                    if self.activity_log:
                        self.activity_log.add_log(user.id, "EDIT_PRODUCT", f"Updated description of product ID {pid}")

                except ValueError as e:
                    print("Грешка:", e)

            elif choice == "3":
                categories = self.category_controller.get_all()
                print("\nКатегории:")
                for i, c in enumerate(categories):
                    print(f"{i}. {c.name}")

                raw = input("Изберете категории (пример: 0,2,3): ").strip()
                try:
                    indexes = [int(x) for x in raw.split(",") if x.strip()]
                    new_ids = [categories[i].category_id for i in indexes]
                    self.product_controller.update_categories(pid, new_ids, user.id)
                    print("Категориите са обновени.")

                    if self.activity_log:
                        self.activity_log.add_log(user.id, "EDIT_PRODUCT", f"Updated categories of product ID {pid}")

                except Exception:
                    print("Невалиден избор.")

            elif choice == "4":
                amount = _read_float("Ново количество: ")
                if amount is not None:
                    diff = amount - product.quantity
                    try:
                        if diff > 0:
                            self.product_controller.increase_quantity(pid, diff, user.id)
                        else:
                            self.product_controller.decrease_quantity(pid, abs(diff), user.id)
                        print("Количество обновено.")

                        if self.activity_log:
                            self.activity_log.add_log(user.id, "EDIT_PRODUCT", f"Updated quantity of product ID {pid}")

                    except ValueError as e:
                        print("Грешка:", e)

            elif choice == "5":
                unit = input("Нова мерна единица: ").strip()
                product.unit = unit
                product.update_modified()
                self.product_controller.save_changes()

                print("Мерната единица е обновена.")

                if self.activity_log:
                    self.activity_log.add_log(user.id, "EDIT_PRODUCT", f"Updated unit of product ID {pid}")

            elif choice == "6":
                price = _read_float("Нова цена: ")
                if price is not None:
                    try:
                        self.product_controller.update_price(pid, price, user.id)
                        print("Цена обновена.")

                        if self.activity_log:
                            self.activity_log.add_log(user.id, "EDIT_PRODUCT", f"Updated price of product ID {pid}")

                    except ValueError as e:
                        print("Грешка:", e)

            elif choice == "7":
                sid = _read_int("ID на доставчик: ")
                if sid is not None:
                    try:
                        self.product_controller.update_supplier(pid, sid, user.id)
                        print("Доставчик обновен.")

                        if self.activity_log:
                            self.activity_log.add_log(user.id, "EDIT_PRODUCT", f"Updated supplier of product ID {pid}")

                    except ValueError as e:
                        print("Грешка:", e)

            elif choice == "0":
                return

            else:
                print("Невалиден избор.")

    # 4. Покажи всички продукти
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

    # 6. Сортиране
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

    # 9. Увеличаване
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

    # 10. Намаляване
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

    # 11. Ниска наличност
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

    # 14. Обща стойност
    def total_value(self, _):
        value = self.product_controller.total_values()
        print(f"Обща стойност на склада: {value:.2f} лв.")

    # 15. Групиране по категории (показва името на категорията, не UUID)
    def group_by_category(self, _):
        groups = self.product_controller.group_by_category()

        for category_id, products in groups.items():
            cat_obj = self.category_controller.get_by_id(category_id)
            cat_name = cat_obj.name if cat_obj else category_id

            print(f"\nКатегория: {cat_name}")
            for p in products:
                print(f" - {p.name} | {p.quantity} {p.unit} | {p.price} лв.")


    # 16. РАЗШИРЕНО ТЪРСЕНЕ

    def advanced_search(self, _):
        print("\n=== Разширено търсене на продукти ===")

        # 1) Търсене по ключова дума
        keyword = input("Ключова дума (име/описание) или Enter за пропуск: ").strip()

        # 2) Категория
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

        # 3) Цена (диапазон)
        min_price = _read_float("Минимална цена (или Enter): ")
        max_price = _read_float("Максимална цена (или Enter): ")

        # 4) Количество (диапазон)
        min_qty = _read_float("Минимално количество (или Enter): ")
        max_qty = _read_float("Максимално количество (или Enter): ")

        # 5) Доставчик
        raw_sup = input("ID на доставчик или Enter за пропуск: ").strip()
        supplier_id = int(raw_sup) if raw_sup.isdigit() else None

        # ИЗВИКВАНЕ НА КОМБИНИРАНО ТЪРСЕНЕ
        results = self.product_controller.search_combined(
            name_keyword=keyword if keyword else None,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            min_qty=min_qty,
            max_qty=max_qty,
            supplier_id=supplier_id
        )

        # ПОКАЗВАНЕ НА РЕЗУЛТАТИТЕ
        if not results:
            print("\nНяма намерени продукти.")
            return

        print("\n=== Резултати ===")
        for p in results:
            print(f"{p.product_id} | {p.name} | {p.quantity} {p.unit} | {p.price} лв.")


