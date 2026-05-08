from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.supplier_controller import SupplierController
from models.user import User


class SupplierView:
    def __init__(self, controller: SupplierController):
        self.controller = controller

    def show_menu(self, user: User):
        while True:
            menu = self._build_menu(user)
            choice = menu.show()
            if menu.execute(choice, user) == "break":
                break

    def _build_menu(self, user: User):
        is_admin = user.role == "Admin"
        menu_items = [MenuItem("1", "Списък с доставчици", self.show_suppliers)]

        if is_admin:
            menu_items.extend([
                MenuItem("2", "Добавяне на доставчик", self.add_supplier),
                MenuItem("3", "Редактиране на доставчик", self.edit_supplier),
                MenuItem("4", "Изтриване на доставчик", self.delete_supplier)])

        menu_items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Меню Доставчици", menu_items)

    def show_suppliers(self, _):
        suppliers = self.controller.get_all()
        if not suppliers:
            print("\nНяма налични доставчици.")
            return

        columns = ["ID (кратко)", "Име", "Контакт", "Адрес"]
        rows = []
        for s in suppliers:
            rows.append([s.supplier_id[:8], s.name, s.contact, s.address])

        print("\nСписък на доставчици")
        print(format_table(columns, rows))

    def add_supplier(self, _):
        print("\nДобавяне на нов доставчик")
        print("(Напишете 'отказ' за излизане)")

        while True:
            name = input("Име на доставчик: ").strip()
            if name.lower() == "отказ":
                return
            try:
                self.controller.validator.validate_name(name)
                break
            except Exception as e:
                print(f"Грешка: {e}")

        while True:
            contact = input("Контакт (тел/имейл): ").strip()
            if contact.lower() == "отказ":
                return
            try:
                self.controller.validator.validate_contact(contact)
                break
            except Exception as e:
                print(f"Грешка: {e}")

        while True:
            address = input("Адрес: ").strip()
            if address.lower() == "отказ":
                return
            try:
                self.controller.validator.validate_address(address)
                break
            except Exception as e:
                print(f"Грешка: {e}")

        try:
            new_sup = self.controller.add(name=name, contact=contact, address=address)
            print(f"\nДоставчикът е добавен. ID: {new_sup.supplier_id[:8]}")
        except Exception as e:
            print(f"Грешка: {e}")

    def edit_supplier(self, _):
        print("\nРедактиране на доставчик")

        while True:
            supplier_id_input = input("Въведете ID (или 'отказ'): ").strip()
            if supplier_id_input.lower() == 'отказ' or supplier_id_input == "":
                return
            supplier = self.controller.get_by_id(supplier_id_input)
            if supplier:
                break
            print("Доставчикът не е намерен. Опитайте отново.")

        print(f"\nРедактиране на: {supplier.name} [{supplier.supplier_id[:8]}]")
        print("Празно поле запазва старата стойност. 'отказ' за изход.")

        while True:
            new_name = input(f"Ново име ({supplier.name}): ").strip()
            if new_name.lower() == 'отказ':
                return
            if new_name == "":
                new_name = supplier.name
                break
            try:
                self.controller.validator.validate_name(new_name)
                break
            except Exception as e:
                print(f"Грешка: {e}")

        while True:
            new_contact = input(f"Нов контакт ({supplier.contact}): ").strip()
            if new_contact.lower() == 'отказ':
                return
            if new_contact == "":
                new_contact = supplier.contact
                break
            try:
                self.controller.validator.validate_contact(new_contact)
                break
            except Exception as e:
                print(f"Грешка: {e}")

        while True:
            new_address = input(f"Нов адрес ({supplier.address}): ").strip()
            if new_address.lower() == 'отказ':
                return
            if new_address == "":
                new_address = supplier.address
                break
            try:
                self.controller.validator.validate_address(new_address)
                break
            except Exception as e:
                print(f"Грешка: {e}")

        try:
            self.controller.update(supplier_id=supplier.supplier_id, name=new_name,
                                   contact=new_contact, address=new_address)
            print("Данните са обновени.")
        except Exception as e:
            print(f"Грешка: {e}")

    def delete_supplier(self, _):
        print("\nИзтриване на доставчик")

        while True:
            supplier_id_input = input("Въведете ID (или 'отказ'): ").strip()
            if supplier_id_input.lower() == 'отказ' or supplier_id_input == "":
                return
            supplier = self.controller.get_by_id(supplier_id_input)
            if supplier:
                break
            print("Доставчикът не е намерен.")

        confirm = input(f"Изтриване на '{supplier.name}'? (y/n): ").strip().lower()
        if confirm == "y":
            try:
                self.controller.remove(supplier.supplier_id)
                print("Доставчикът е премахнат.")
            except Exception as e:
                print(f"Грешка: {e}")
        else:
            print("Операцията е прекратена.")
