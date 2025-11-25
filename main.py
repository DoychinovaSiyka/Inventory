from controller.product_controller import ProductController
from controller.movement_controller import MovementController
from controller.category_controller import CategoryController
from models.movement import MovementType
from models.product import Product
from models.category import Category
from storage.json_repository import JSONRepository


from password import require_password
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
            if not name:
                print("Името е задължително !")
                continue

            categories = category_controller.get_all()
            for i,c in enumerate(categories):
                print(f"{i}. {c.name}")

            try:
                category_ids = [int(c) for c in input("Изберете категории (номера разделени със запетайка ):").split(",")]

            except ValueError:
                print("Избрана е навалидна категория.")
                continue
            ids_valid = True
            for c in category_ids:
                if  c < 0 or c >= len(categories):
                    ids_valid = False
            if not ids_valid:
                print("Избран е невалиден номер на категория.")
                continue

            selected_categories = [categories[i] for i in category_ids]

            quantity = input("Количество: ")
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    print("Количеството трябва да е положително число.")
                    continue
            except ValueError:
                print("Невалидно количество")
                continue

            description = input("Описание: ")
            if not description:
                print("Описанието е задължително !")
                continue

            price = input("Цена: ")
            try:
                price = float(price)
                if price <= 0:
                    print("Цената трябва да е положително число.")
                    continue
            except ValueError:
                print("Невалидна цена.")
                continue

            product_controller.add( name,selected_categories, quantity, description, price)


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
            break


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
                print(f"-{p.price}| Цена: {p.price}")


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


def category_menu(category_controller):
    while True:
        print("\nМеню за категории")
        print("0.Назад")
        print("1.Създаване на категория")
        print("2.Премахване на категория")
        print("3.Промяна на категория")
        print("4.Покажи всички категории")

        choice = input("Изберете опция: ")
        if choice == "0":
            break
        elif choice == "1":
            name = input("Име: ")
            if not name:
                print("Името е задължително !")
                continue
            existing = [c for c in category_controller.get_all() if c.name == name]
            if existing:
                print("Категория с това име вече съществува.")
                continue
            category = category_controller.add(name) # взимам всички категории
            print(f"Категорията '{name}' е създадена.")


        elif choice == "2":
            category_id = input("Въведи ID на категорията за изтриване: ")
            removed = category_controller.remove(category_id)
            if removed:
                print("Категорията е премахната.")
            else:
                print("Категорията не е намерена.")

        elif choice == "3":
            category_id = input("Въведи ID на категорията за промяна: ")
            new_name = input("Ново име: ")
            updated =  category_controller.update_name(category_id,new_name)
            if updated:
                print("Категорията е обновена.")
            else:
                print("Категорията не е намерена.")

        elif choice == "4":
            categories = category_controller.get_all()
            if not categories:
                print("Няма налични категории.")
            else:
                print("\nСписък с категории: ")
                for c in categories:
                    print(f"-{c.name} (ID:{c.category_id})")



def show_menu():
    print("\nНачално меню")
    print("0.Назад")
    print("1.Управление на продукт")
    print("2.Управление на категория")
    print("3.Управление на доставки/продажби")


def main():
    category_repo = JSONRepository("data/categories.json")
    product_repo = JSONRepository("data/products.json")
    movement_repo = JSONRepository("data/movements.json")

    category_controller = CategoryController(category_repo)
    product_controller = ProductController(product_repo)
    movement_controller = MovementController(movement_repo)
    while True:
        show_menu()
        choice = input("Изберете опция: ")
        if choice == "0":
            break
        elif choice == "1":
            product_menu(product_controller,category_controller)
        elif choice == "2":
            category_menu(category_controller)
        elif choice == "3":
            movement_menu(product_controller,movement_controller)



def movement_menu(product_controller:ProductController,movement_controller:MovementController):
    while True:
        print("\nМеню за Доставки/Продажби")
        print("0.Назад")
        print("1.Създаване на доставка/продажба")
        print("2.Търсене на доставки/продажби")
        print("3.Покажи всички доставки/продажби")



        choice = input("Изберете опция: ")
        if choice == "0":
            break
        elif choice == "1":

            products = product_controller.get_all()
            for i, c in enumerate(products):
                print(f"{i}. {c.name}")

            try:
                product_idx = int(input("Изберете един от продуктите:"))
                if product_idx < 0 or product_idx>= len(products):
                    raise ValueError()
                product_id = products[product_idx].product_id
            except ValueError:
                print("Избран е навалиден продукт.")
                continue
            try:
                movement_type_num = int(input("Въведете 0 за доставка или 1 за продажба: "))
                if movement_type_num not in [0,1]:
                    raise ValueError()
                movement_type = MovementType.DELIVERY if movement_type_num == 0 else MovementType.SALE

            except ValueError:
                print("Невалиден избор.")
                continue

            quantity = input("Количество: ")
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    print("Количеството трябва да е положително число.")
                    continue
            except ValueError:
                print("Невалидно количество")
                continue

            description = input("Описание: ")
            if not description:
                print("Описанието е задължително !")
                continue

            price = input("Цена: ")
            try:
                price = float(price)
                if price <= 0:
                    print("Цената трябва да е положително число.")
                    continue
            except ValueError:
                print("Невалидна цена.")
                continue
            movement_controller.add(product_id,movement_type,quantity,description,price)



        elif choice == "2":
            keyword = input("Въведи дума за търсене в описанието: ").lower()
            results = [m for m in movement_controller.get_all() if keyword in m.description.lower()]
            if not results:
                print("Няма съвпадения.")
            else:
                print("\nНамерени двежения:")
                for m in results:
                    print(f"-{m.movement_type.name} | Продукт ID: {m.product_id} | Количество: {m.quantity}| Цена:{m.price} | Дата:{m.created}")


        elif choice == "3":
            movements = movement_controller.get_all()
            if not movements:
                print("Няма доставки или продажби.")
            else:
                print("\nСписък с двежения:")
                for m in movements:
                    print(f"-{m.movement_type.name} | Продукт ID: {m.product_id} | Количество: {m.quantity}| Цена:{m.price} | Дата:{m.created}")






if __name__  == "__main__":

    main()



