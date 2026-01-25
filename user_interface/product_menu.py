from password import show_products_menu


def product_menu(product_controller,category_controller):
    while True:
        print("\nМеню за продукти")
        print("0.Назад")
        print("1.Създаване на продукт")
        print("2.Премахване на продукт")
        print("3.Промяна на продукт")
        print("4.Покажи всички продукти")
        print("5.Търсене")
        print("6.Сортиране по цена (низходящо): ")
        print("7.Показване на средна цена")
        print("8.Филтриране по категория")

        choice = input("Изберете опция: ")
        if choice == "0":
            break
        elif choice == "1":
            name = input("Име: ")

            categories = category_controller.get_all()
            for i,c in enumerate(categories):
                print(f"{i}. {c.name}")

            category_ids = [int(c) for c in input("Изберете категории (номера разделени със запетайка ):").split(",")]
            selected_categories = [categories[i] for i in category_ids]

            quantity = int(input("Количество: "))
            description = input("Описание: ")
            price = float(input("Цена: "))
            try:
                product_controller.add( name,selected_categories, quantity, description, price)
                print("Продуктът е добавен успешно!")
            except ValueError as e:
                print("Грешка: ",e)

        elif choice == "2":
            name = input("Име на продукта за премахване: ")
            removed = product_controller.remove_by_name(name)
            if removed:
                print("Продуктът е премахнат.")
            else:
                print("Продуктът не е намерен.")


        elif choice == "3":
            name = input("Име на продукта за промяна: ")
            new_price = input("Нова цена: ")
            try:
                new_price = float(new_price)
                updated = product_controller.update_price(name,new_price)
                if updated:
                    print("Продуктът е обновен.")
                else:
                    print("Продуктът не е намерен.")
            except ValueError:
                print("Невалидна цена.")

        elif choice == "4":

            show_products_menu(product_controller)
            return

        elif choice == "5":
            keyword = input("Търси по име или по описание: ").lower()
            results = product_controller.search(keyword)
            if not results:
                print("Няма съвпадения.")

            else:
                print("\nРезултати от търсенето: ")
                for p in results:
                    print(f"-{p.name}| {p.description}")


        elif choice == "6":
            print("Изберете алгоритъм за сортиране:")
            print("1.Вградено сортиране")
            print("2.Bubble Sort")
            print("3.Selection Sort")

            method = input("Избор: ")
            if method == "1":
                sorted_products = product_controller.sort_by_price_desc()
            elif method == "2":
                sorted_products = product_controller.bubble_sort()
            elif method == "3":
                sorted_products = product_controller.selection_sort()
            else:
                print("Невалиден избор.")
                continue
            print("\nСоритрани продукти:")
            for p in sorted_products:
                print(f"-{p.price}| Цена: {p.price:.2f}")


        elif choice == "7":
            avg = product_controller.average_price()
            print(f"Средна цена на продуктите:{avg:.2f} лв")
        elif choice == "8":
            categories = category_controller.get_all()
            for i,c in enumerate(categories):
                print(f"{i}.{c.name}")
            try:
                selected_ids = [int(i) for i in input("Изберете категории по номер (разедлени със запетайка):").split(",")]
                selected_categories = [categories[i] for i in selected_ids]
                results = product_controller.filter_by_multiple_category_ids([c.category_id for c in selected_categories])
                if not results:
                    print("Няма продукти в тази категория.")

                else:
                    print("\nПродукти в категорията: ")
                    for p in results:
                        print(f"-{p.name}| {p.price:.2f} лв")
            except (ValueError,IndexError):
                print("Невалиден избор.")
        else:
            print("Невалидна опция. Опитай пак!")
