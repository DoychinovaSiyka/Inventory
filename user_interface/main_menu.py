from user_interface.product_menu import product_menu
from user_interface.category_menu import category_menu
from user_interface.supplier_menu import supplier_menu
from user_interface.movement_menu import movement_menu
from user_interface.invoice_menu import invoice_menu
from user_interface.reports_menu import reports_menu
from user_interface.user_menu import user_menu
from user_interface.system_info_menu import system_info_menu
from user_interface.graph_menu import graph_menu   # ← добавено

def main_menu(user, controllers):
    while True:
        print("\n=== Главно меню ===")
        print("1. Продукти")
        print("2. Категории")
        print("3. Доставчици")
        print("4. Движения")
        print("5. Фактури")
        print("6. Справки")
        print("7. Потребители")
        print("8. Най-кратък път между складове (Dijkstra)")
        print("0. Изход")

        choice = input("Избор: ")

        if choice == "1":
            product_menu(user, controllers["product"])
        elif choice == "2":
            category_menu(user, controllers["category"])
        elif choice == "3":
            supplier_menu(user, controllers["supplier"])
        elif choice == "4":
            movement_menu(user, controllers["movement"])
        elif choice == "5":
            invoice_menu(user, controllers["invoice"])
        elif choice == "6":
            reports_menu(user, controllers["report"])
        elif choice == "7":
            user_menu(user, controllers["user"])
        elif choice == "8":
            graph_menu()   # ← ТУК СЕ ИЗВИКВА ДЕЙКСТРА
        elif choice == "0":
            break
        else:
            print("Невалиден избор.")
