from password_utils import show_products_menu
from password_utils import format_table



def _read_int(prompt):
    try:
        return int(input(prompt))
    except ValueError:
        print("Стойността трябва да е цяло число.")
        return None


def _read_float(prompt):
    try:
        return float(input(prompt))
    except ValueError:
        print("Стойността трябва да е число.")
        return None


def product_menu(product_controller, category_controller):
    while True:
        print("\n=== МЕНЮ ПРОДУКТИ ===")
        print("0. Назад")
        print("1. Създаване на продукт")
        print("2. Премахване на продукт")
        print("3. Редактиране на продукт")
        print("4. Покажи всички продукти")
        print("5. Търсене")
        print("6. Сортиране по цена")
        print("7. Средна цена")
        print("8. Филтриране по категория")
        print("9. Увеличаване на количество")
        print("10. Намаляване на количество")
        print("11. Продукти с ниска наличност")
        print("12. Най-скъп продукт")
        print("13. Най-евтин продукт")
        print("14. Обща стойност на склада")
        print("15. Групиране по категории")

        choice = input("Избор: ")

        if choice == "0":
            break

        elif choice == "1":
            name = input("Име: ").strip()
            if not name:
                print("Името не може да е празно.")
                continue

            if product_controller.exists_by_name(name):
                print("Продукт с това име вече съществува.")
                continue

            categories = category_controller.get_all()
            if not categories:
                print("Няма категории.")
                continue

            for i, c in enumerate(categories):
                print(f"{i}. {c.name}")

            try:
                selected = [int(x) for x in input("Изберете категории: ").split(",")]
                selected_categories = [categories[i] for i in selected]
            except:
                print("Невалиден избор.")
                continue

            quantity = _read_int("Количество: ")
            if quantity is None or quantity < 0:
                print("Невалидно количество.")
                continue

            description = input("Описание: ")

            price = _read_float("Цена: ")
            if price is None or price < 0:
                print("Невалидна цена.")
                continue

            try:
                product_controller.add(
                    name,
                    [c.category_id for c in selected_categories],
                    quantity,
                    description,
                    price
                )
                print("Продуктът е добавен!")
            except ValueError as e:
                print("Грешка:", e)

        elif choice == "2":
            name = input("Име на продукта: ").strip()
            if product_controller.remove_by_name(name):
                print("Премахнат.")
            else:
                print("Не е намерен.")

        elif choice == "3":
            product_id = _read_int("ID на продукта: ")
            if product_id is None:
                continue

            print("1. Промяна на цена")
            print("2. Промяна на описание")
            print("3. Промяна на име")

            sub = input("Избор: ")

            if sub == "1":
                new_price = _read_float("Нова цена: ")
                if new_price is None or new_price < 0:
                    print("Невалидна цена.")
                    continue
                if product_controller.update_price(product_id, new_price):
                    print("Обновено.")
                else:
                    print("Не е намерен.")

            elif sub == "2":
                new_desc = input("Ново описание: ")
                p = product_controller.get_by_id(product_id)
                if p:
                    p.description = new_desc
                    p.update_modified()
                    product_controller._save()
                    print("Обновено.")
                else:
                    print("Не е намерен.")

            elif sub == "3":
                new_name = input("Ново име: ").strip()
                p = product_controller.get_by_id(product_id)
                if p:
                    p.name = new_name
                    p.update_modified()
                    product_controller._save()
                    print("Обновено.")
                else:
                    print("Не е намерен.")

        elif choice == "4":
            show_products_menu(product_controller)

        elif choice == "5":
            keyword = input("Търси: ").lower()
            results = product_controller.search(keyword)
            if not results:
                print("Няма резултати.")
            else:
                for p in results:
                    print(f"{p.product_id} | {p.name} | {p.price} лв")

        elif choice == "6":
            print("1. Вградено")
            print("2. Bubble Sort")
            print("3. Selection Sort")
            m = input("Избор: ")

            if m == "1":
                sorted_list = product_controller.sort_by_price_desc()
            elif m == "2":
                sorted_list = product_controller.bubble_sort()
            elif m == "3":
                sorted_list = product_controller.selection_sort()
            else:
                print("Невалидно.")
                continue

            for p in sorted_list:
                print(f"{p.name} | {p.price} лв")

        elif choice == "7":
            print("Средна цена:", product_controller.average_price())

        elif choice == "8":
            categories = category_controller.get_all()
            for i, c in enumerate(categories):
                print(f"{i}. {c.name}")

            try:
                selected = [int(x) for x in input("Избор: ").split(",")]
                selected_ids = [categories[i].category_id for i in selected]
            except:
                print("Невалидно.")
                continue

            results = product_controller.filter_by_multiple_category_ids(selected_ids)
            for p in results:
                print(f"{p.name} | {p.price} лв")

        elif choice == "9":
            pid = _read_int("ID: ")
            amount = _read_int("Добави: ")
            if pid is None or amount is None:
                continue
            if product_controller.increase_quantity(pid, amount):
                print("Обновено.")
            else:
                print("Не е намерен.")

        elif choice == "10":
            pid = _read_int("ID: ")
            amount = _read_int("Извади: ")
            if pid is None or amount is None:
                continue
            try:
                if product_controller.decrease_quantity(pid, amount):
                    print("Обновено.")
                else:
                    print("Не е намерен.")
            except ValueError as e:
                print("Грешка:", e)

        elif choice == "11":
            low = product_controller.check_low_stock()
            for p in low:
                print(f"{p.name} | {p.quantity} бр")

        elif choice == "12":
            p = product_controller.most_expensive()
            if p:
                print(f"{p.name} | {p.price} лв")

        elif choice == "13":
            p = product_controller.cheapest()
            if p:
                print(f"{p.name} | {p.price} лв")

        elif choice == "14":
            print("Обща стойност:", product_controller.total_values(), "лв")

        elif choice == "15":
            grouped = product_controller.group_by_category()
            for cat_id, products in grouped.items():
                print(f"\nКатегория ID {cat_id}:")
                for p in products:
                    print(f" - {p.name} | {p.price} лв")

        else:
            print("Невалидна опция.")
