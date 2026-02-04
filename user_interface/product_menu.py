from storage.password_utils import format_table

from controllers.product_controller import ProductController

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


def product_menu(product_controller, category_controller, readonly=False):
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

        # Блокиране на функции за гост
        if readonly and choice in ["1", "2", "3", "9", "10"]:
            print("Тази функция не е достъпна за гост.")
            continue

        if choice == "0":
            break

        # 1. Създаване на продукт
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

            print("\nКатегории:")
            for i, c in enumerate(categories):
                print(f"{i}. {c.name}")

            raw_input = input("Изберете категории (пример: 0,2,3): ").strip()

            try:
                # Премахваме празни елементи
                parts = [x.strip() for x in raw_input.split(",") if x.strip() != ""]

                # Превръщаме в числа
                selected_indexes = [int(x) for x in parts]

                # Проверяваме дали индексите са валидни
                if any(i < 0 or i >= len(categories) for i in selected_indexes):
                    print("Невалиден индекс на категория.")
                    continue

                # Взимаме Category обекти
                selected_categories = [categories[i] for i in selected_indexes]

                # Взимаме UUID
                category_ids = [c.category_id for c in selected_categories]

                if not category_ids:
                    print("Трябва да изберете поне една категория.")
                    continue

            except Exception:
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
                    category_ids,
                    quantity,
                    description,
                    price
                )
                print("Продуктът е добавен!")
            except ValueError as e:
                print("Грешка:", e)


        # 2. Премахване
        elif choice == "2":
            name = input("Име на продукта: ").strip()
            if product_controller.remove_by_name(name):
                print("Премахнат.")
            else:
                print("Не е намерен.")


        # 3. Редактиране
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
                try:
                    product_controller.update_price(product_id, new_price)
                    print("Обновено.")
                except ValueError as e:
                    print("Грешка:", e)

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


        # 4. Покажи всички

        elif choice == "4":
            products = product_controller.products
            if not products:
                print("Няма налични продукти.")
            else:
                print("\n=== Списък с продукти ===")
                for p in products:
                    print(f"{p.product_id} | {p.name} | {p.quantity} бр. | {p.price} лв.")


        # 5. Търсене

        elif choice == "5":
            keyword = input("Търси: ").lower()
            results = product_controller.search(keyword)
            if not results:
                print("Няма резултати.")
            else:
                for p in results:
                    print(f"{p.product_id} | {p.name} | {p.price} лв")


        # 6. Сортиране

        elif choice == "6":
            print("\nСортиране по цена:")
            print("1. Вградено (висока → ниска)")
            print("2. Bubble Sort (ниска → висока)")
            print("3. Selection Sort (висока → ниска)")
            m = input("Избор: ")

            if m == "1":
                sorted_list = product_controller.sort_by_price_desc()
                title = "Цена (висока → ниска) ↓"
                algorithm = "Вградено сортиране"

            elif m == "2":
                sorted_list = product_controller.bubble_sort()
                sorted_list.sort(key=lambda p: p.price)
                title = "Цена (ниска → висока) ↑"
                algorithm = "Bubble Sort"

            elif m == "3":
                sorted_list = product_controller.selection_sort()
                sorted_list.sort(key=lambda p: p.price, reverse=True)
                title = "Цена (висока → ниска) ↓"
                algorithm = "Selection Sort"

            else:
                print("Невалидно.")
                continue

            print(f"\n=== Сортиране по: {title} ===")
            print(f"Алгоритъм: {algorithm}\n")

            rows = [
                [p.name.ljust(20), f"{p.price:.2f} лв.", str(p.quantity)]
                for p in sorted_list
            ]

            print(format_table(["Име", "Цена", "Количество"], rows))


        # 7. Средна цена

        elif choice == "7":
            print("Средна цена:", product_controller.average_price())


        # 8. Филтриране по категория

        elif choice == "8":
            categories = category_controller.get_all()
            for c in categories:
                print(f"{c.category_id}. {c.name}")

            try:
                selected = [int(x) for x in input("Избор: ").split(",")]
                selected_ids = []
                for cat_id in selected:
                    c = category_controller.get_by_id(cat_id)
                    if not c:
                        raise ValueError("Невалидна категория.")
                    selected_ids.append(cat_id)
            except:
                print("Невалидно.")
                continue

            results = product_controller.filter_by_multiple_category_ids(selected_ids)
            for p in results:
                print(f"{p.name} | {p.price} лв")

        # 9. Увеличаване

        elif choice == "9":
            pid = _read_int("ID: ")
            amount = _read_int("Добави: ")
            if pid is None or amount is None:
                continue
            try:
                product_controller.increase_quantity(pid, amount)
                print("Обновено.")
            except ValueError as e:
                print("Грешка:", e)

        # 10. Намаляване

        elif choice == "10":
            pid = _read_int("ID: ")
            amount = _read_int("Извади: ")
            if pid is None or amount is None:
                continue
            try:
                product_controller.decrease_quantity(pid, amount)
                print("Обновено.")
            except ValueError as e:
                print("Грешка:", e)


        # 11. Ниска наличност
        elif choice == "11":
            low = product_controller.check_low_stock()

            if not low:
                print("Няма продукти с ниска наличност.")
            else:
                for p in low:
                    print(f"{p.name} | {p.quantity} бр")


        # 12. Най-скъп

        elif choice == "12":
            p = product_controller.most_expensive()
            if p:
                print(f"{p.name} | {p.price} лв")


        # 13. Най-евтин

        elif choice == "13":
            p = product_controller.cheapest()
            if p:
                print(f"{p.name} | {p.price} лв")


        # 14. Обща стойност

        elif choice == "14":
            print("Обща стойност:", product_controller.total_values(), "лв")


        # 15. Групиране

        elif choice == "15":
            grouped = product_controller.group_by_category()
            for cat_id, products in grouped.items():
                print(f"\nКатегория ID {cat_id}:")
                for p in products:
                    print(f" - {p.name} | {p.price} лв")

        else:
            print("Невалидна опция.")
