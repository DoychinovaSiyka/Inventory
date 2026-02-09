

from views.product_menu_view import ProductView
from views.category_view import CategoryView
from views.supplier_view import SupplierView
from views.movement_view import MovementView
from views.invoice_view import InvoiceView
from views.user_view import UserView
from views.reports_view import ReportsView
from views.graph_view import GraphView


class MainMenuView:
    def __init__(self, controllers):
        self.controllers = controllers

    def show_menu(self, user):
        while True:
            print("\n Главно меню ")
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
                ProductView(self.controllers["product"], self.controllers["category"]).show_menu(user)

            elif choice == "2":
                CategoryView(self.controllers["category"]).show_menu(user)

            elif choice == "3":
                SupplierView(self.controllers["supplier"]).show_menu(user)

            elif choice == "4":
                MovementView(self.controllers["product"],
                    self.controllers["movement"],self.controllers["user"]).show_menu()

            elif choice == "5":
                InvoiceView(self.controllers["invoice"]).show_menu(user)

            elif choice == "6":
                ReportsView(self.controllers["report"]).show_menu(user)

            elif choice == "7":
                UserView(self.controllers["user"]).show_menu(user)

            elif choice == "8":
                GraphView(self.controllers["graph"]).show_menu()

            elif choice == "0":
                break

            else:
                print("Невалиден избор.")
