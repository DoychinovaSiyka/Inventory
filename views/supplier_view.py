from views.menu import Menu, MenuItem
from views.password_utils import format_table


class SupplierView:
    def __init__(self, controller):
        self.controller = controller

    def show_menu(self, user):
        while True:
            is_admin = False
            if user and hasattr(user, 'role'):
                if user.role == "Admin":
                    is_admin = True

            menu = self._build_menu(is_admin)
            choice = menu.show()
            if menu.execute(choice, user) == "break":
                break

    def _build_menu(self, is_admin):
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
            print("\nНяма доставчици.")
            return

        columns = ["ID", "Име", "Контакт", "Адрес"]
        rows = []
        for s in suppliers:
            rows.append([s.supplier_id[:8], s.name, s.contact, s.address])

        print("\nСписък с доставчици")
        print(format_table(columns, rows))
        input("\nEnter за продължение...")

    def add_supplier(self, _):
        print("\nНов доставчик")
        print("(Напишете 'отказ' за изход)")

        while True:
            name = input("Име: ").strip()
            if name.lower() == "отказ":
                return
            if not name:
                print("Името е празно.")
                continue
            break

        while True:
            contact = input("Контакт: ").strip()
            if contact.lower() == "отказ":
                return
            if not contact:
                print("Контактът е задължителен.")
                continue
            break

        while True:
            address = input("Адрес: ").strip()
            if address.lower() == "отказ":
                return
            if not address:
                print("Адресът е празен.")
                continue
            break

        try:
            new_sup = self.controller.add(name=name, contact=contact, address=address)
            print(f"\nДоставчикът е добавен. ID: {new_sup.supplier_id[:8]}")
        except Exception as e:
            print(f"Проблем при запис: {e}")

    def edit_supplier(self, _):
        print("\nРедактиране на доставчик")

        while True:
            supplier_id_input = input("ID (или 'отказ'): ").strip()
            if not supplier_id_input or supplier_id_input.lower() == 'отказ':
                return

            supplier = self.controller.get_by_id(supplier_id_input)
            if supplier:
                break
            print("Няма такъв доставчик.")

        print(f"\nРедакция на: {supplier.name}")
        print("(Enter запазва старата стойност)")

        new_name = input(f"Ново име [{supplier.name}]: ").strip() or supplier.name
        new_contact = input(f"Нов контакт [{supplier.contact}]: ").strip() or supplier.contact
        new_address = input(f"Нов адрес [{supplier.address}]: ").strip() or supplier.address

        try:
            self.controller.update(
                supplier_id=supplier.supplier_id,
                name=new_name,
                contact=new_contact,
                address=new_address
            )
            print("Данните са обновени.")
        except Exception as e:
            print(f"Проблем при обновяване: {e}")

    def delete_supplier(self, _):
        print("\nИзтриване на доставчик")

        while True:
            supplier_id_input = input("ID (или 'отказ'): ").strip()
            if not supplier_id_input or supplier_id_input.lower() == 'отказ':
                return

            supplier = self.controller.get_by_id(supplier_id_input)
            if supplier:
                break
            print("Няма такъв доставчик.")

        confirm = input(f"Искате ли да изтрием '{supplier.name}'? (y/n): ").strip().lower()
        if confirm == "y":
            try:
                self.controller.remove(supplier.supplier_id)
                print("Доставчикът е изтрит.")
            except Exception as e:
                print(f"Проблем при изтриване: {e}")
        else:
            print("Операцията е прекратена.")
