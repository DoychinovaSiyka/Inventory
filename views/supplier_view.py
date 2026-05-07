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

    def _build_menu(self, user: User):
        is_admin = user.role == "Admin"
        menu_items = [MenuItem("1", "Списък с доставчици", self.show_suppliers)]

        if is_admin:
            menu_items.extend([
                MenuItem("2", "Добавяне на доставчик", self.add_supplier),
                MenuItem("3", "Редактиране на доставчик", self.edit_supplier),
                MenuItem("4", "Изтриване на доставчик", self.delete_supplier)
            ])

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Меню Доставчици", menu_items)

    def show_suppliers(self, _):
        suppliers = self.controller.get_all()
        if not suppliers:
            print("\n[!] Няма налични доставчици.")
            return

        columns = ["ID (кратко)", "Име", "Контакт", "Адрес"]
        rows = [[s.supplier_id[:8], s.name, s.contact, s.address] for s in suppliers]
        print("\n--- СПИСЪК НА ПАРТНЬОРИ / ДОСТАВЧИЦИ ---")
        print(format_table(columns, rows))

    def add_supplier(self, _):
        print("\n--- ДОБАВЯНЕ НА НОВА ФИРМА ДОСТАВЧИК ---")
        name = input("Име на доставчик (Enter за отказ): ").strip()
        if not name:
            return

        contact = input("Контакт (тел/имейл): ").strip() or "-"
        address = input("Адрес: ").strip() or "-"
        try:
            new_sup = self.controller.add(name=name, contact=contact, address=address)
            print(f"Доставчикът е добавен с ID: {new_sup.supplier_id[:8]}")
        except ValueError as e:
            print(f"[Грешка] {e}")

    def edit_supplier(self, _):
        print("\n--- РЕДАКТИРАНЕ НА ДОСТАВЧИК ---")
        while True:
            supplier_id_input = input("Въведете ID (кратко или пълно, Enter за отказ): ").strip()
            if not supplier_id_input:
                return
            supplier = self.controller.get_by_id(supplier_id_input)
            if not supplier:
                print(f"[Грешка] Доставчик с ID '{supplier_id_input}' не е намерен. Опитайте пак.")
                continue
            break

        print(f"\nРедактиране на: {supplier.name} [{supplier.supplier_id[:8]}]")
        print("* Празно поле = запазване на старата стойност.")
        new_name = input(f"Ново име ({supplier.name}): ").strip() or supplier.name
        new_contact = input(f"Нов контакт ({supplier.contact}): ").strip() or supplier.contact
        new_address = input(f"Нов адрес ({supplier.address}): ").strip() or supplier.address
        try:
            self.controller.update(supplier_id=supplier.supplier_id, name=new_name,
                                   contact=new_contact, address=new_address)
            print("Данните са обновени успешно.")
        except ValueError as e:
            print(f"[Грешка] {e}")

    def delete_supplier(self, _):
        print("\n--- ИЗТРИВАНЕ НА ДОСТАВЧИК ---")
        while True:
            supplier_id_input = input("Въведете ID за изтриване (Enter за отказ): ").strip()
            if not supplier_id_input:
                return

            supplier = self.controller.get_by_id(supplier_id_input)
            if not supplier:
                print(f"[Грешка] Доставчик с ID '{supplier_id_input}' не е намерен.")
                continue
            break

        confirm = input(f"Сигурни ли сте, че искате да изтриете '{supplier.name}'? (y/n): ").strip().lower()
        if confirm == "y":
            try:
                self.controller.remove(supplier.supplier_id)
                print(f"Доставчик '{supplier.name}' беше премахнат.")
            except ValueError as e:
                print(f"[Грешка] {e}")
        else:
            print("Операцията е отказана.")
