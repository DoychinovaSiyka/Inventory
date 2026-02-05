# views/supplier_view.py

from menus.menu import Menu, MenuItem
from storage.password_utils import format_table
from controllers.supplier_controller import SupplierController
from models.user import User


class SupplierView:
    def __init__(self, controller: SupplierController):
        self.controller = controller

    def show_menu(self, user: User):
        is_admin = user.role == "Admin"

        menu_items = [
            MenuItem("1", "Списък с доставчици", self.show_suppliers)
        ]

        if is_admin:
            menu_items.extend([
                MenuItem("2", "Добавяне на доставчик", self.add_supplier),
                MenuItem("3", "Редактиране на доставчик", self.edit_supplier),
                MenuItem("4", "Изтриване на доставчик", self.delete_supplier)
            ])

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))

        menu = Menu("Меню Доставчици", menu_items)

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # 1. Списък с доставчици
    def show_suppliers(self, user: User):
        suppliers = self.controller.get_all()

        if not suppliers:
            print("Няма налични доставчици.")
            return

        columns = ["ID", "Име", "Контакт", "Адрес"]
        rows = [
            [s.supplier_id, s.name, s.contact, s.address]
            for s in suppliers
        ]

        print("\n" + format_table(columns, rows))

    # 2. Добавяне на доставчик (Admin only)
    def add_supplier(self, user: User):
        name = input("Име на доставчик: ").strip()
        contact = input("Контакт (телефон/имейл): ").strip()
        address = input("Адрес: ").strip()

        try:
            self.controller.add(name=name, contact=contact, address=address)
            print("Доставчикът е добавен успешно!")
        except ValueError as e:
            print("Грешка:", e)

    # 3. Редактиране на доставчик (Admin only)
    def edit_supplier(self, user: User):
        supplier_id = input("Въведете ID на доставчик: ").strip()
        supplier = self.controller.get_by_id(int(supplier_id))

        if not supplier:
            print("Доставчикът не е намерен.")
            return

        print("\nОставете празно, ако не искате да променяте полето.")
        new_name = input(f"Ново име ({supplier.name}): ").strip()
        new_contact = input(f"Нов контакт ({supplier.contact}): ").strip()
        new_address = input(f"Нов адрес ({supplier.address}): ").strip()

        try:
            self.controller.update(
                supplier_id=int(supplier_id),
                name=new_name if new_name else supplier.name,
                contact=new_contact if new_contact else supplier.contact,
                address=new_address if new_address else supplier.address
            )
            print("Доставчикът е обновен успешно!")
        except ValueError as e:
            print("Грешка:", e)

    # 4. Изтриване на доставчик (Admin only)
    def delete_supplier(self, user: User):
        supplier_id = input("Въведете ID на доставчик: ").strip()

        try:
            if self.controller.remove(int(supplier_id)):
                print("Доставчикът е изтрит успешно!")
            else:
                print("Доставчикът не е намерен.")
        except ValueError as e:
            print("Грешка:", e)
