from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.supplier_controller import SupplierController
from models.user import User


class SupplierView:
    def __init__(self, controller: SupplierController):
        self.controller = controller

    def show_menu(self, user: User):
        menu = self._build_menu(user)
        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # Създаване на менюто отделно
    def _build_menu(self, user: User):
        is_admin = user.role == "Admin"
        menu_items = [MenuItem("1", "Списък с доставчици", self.show_suppliers)]
        if is_admin:
            menu_items.extend([MenuItem("2", "Добавяне на доставчик", self.add_supplier),
                               MenuItem("3", "Редактиране на доставчик", self.edit_supplier),
                               MenuItem("4", "Изтриване на доставчик", self.delete_supplier)])

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Меню Доставчици", menu_items)

    # списък с доставчици
    def show_suppliers(self, _):
        suppliers = self.controller.get_all()
        if not suppliers:
            print("\nНяма налични доставчици.")
            return
        columns = ["ID", "Име", "Контакт", "Адрес"]
        rows = [[s.supplier_id, s.name, s.contact, s.address] for s in suppliers]
        print("\n" + format_table(columns, rows))

    # добавяне на доставчик - admin only
    def add_supplier(self, _):
        print("\n--- Добавяне на доставчик ---")
        name = input("Име на доставчик (Enter за отказ): ").strip()
        if not name:
            print("Операцията е отказана.\n")
            return

        contact = input("Контакт (телефон/имейл, Enter за отказ): ").strip()
        if not contact:
            print("Операцията е отказана.\n")
            return
        address = input("Адрес (Enter за отказ): ").strip()
        if not address:
            print("Операцията е отказана.\n")
            return
        try:
            self.controller.add(name=name, contact=contact, address=address)
            print("[Успех] Доставчикът е добавен успешно!")
        except ValueError as e:
            print(f"[Грешка] {e}")

    # редактиране на доставчик - admin only
    def edit_supplier(self, _):
        print("\n--- Редактиране на доставчик ---")
        # цикъл докато не въведем валидно ID
        while True:
            supplier_id = input("Въведете ID на доставчик (Enter за отказ): ").strip()
            if not supplier_id:
                print("Операцията е отказана.\n")
                return
            try:
                supplier = self.controller.get_by_id(supplier_id)
                if not supplier:
                    print(f"Доставчик с ID '{supplier_id}' не е намерен. Моля, опитайте отново.\n")
                    continue
                # имаме валиден доставчик
                break
            except ValueError as e:
                print(f"[Грешка] {e}. Моля, опитайте отново.\n")

        print("\n* Оставете празно, ако не желаете промяна на текущата стойност.")
        new_name = input(f"Ново име ({supplier.name}): ").strip()
        new_contact = input(f"Нов контакт ({supplier.contact}): ").strip()
        new_address = input(f"Нов адрес ({supplier.address}): ").strip()

        try:
            self.controller.update(supplier_id=supplier_id, name=new_name or supplier.name,
                                   contact=new_contact or supplier.contact, address=new_address or supplier.address)
            print("Доставчикът е обновен успешно!")
        except ValueError as e:
            print(f"[Грешка] {e}")


    def delete_supplier(self, _):
        print("\n--- Изтриване на доставчик ---")
        while True:
            supplier_id = input("Въведете ID на доставчик (Enter за отказ): ").strip()
            if not supplier_id:
                print("Операцията е отказана.\n")
                return
            try:
                supplier = self.controller.get_by_id(supplier_id)
                if not supplier:
                    print(f"Доставчик с ID '{supplier_id}' не е намерен. Моля, опитайте отново.\n")
                    continue
                break
            except ValueError as e:
                print(f"[Грешка] {e}. Моля, опитайте отново.\n")

        confirm = input(f"Сигурни ли сте, че искате да изтриете '{supplier.name}'? (y/n): ").strip().lower()
        if confirm != "y":
            print("Операцията е отказана.")
            return
        try:
            self.controller.remove(supplier_id)
            print(f"[Успех] Доставчик '{supplier.name}' беше изтрит.")
        except ValueError as e:
            print(f"[Грешка] {e}")