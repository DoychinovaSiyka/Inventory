from views.menu import Menu, MenuItem
from views.password_utils import format_table
from validators.supplier_validator import SupplierValidator


class SupplierView:
    def __init__(self, controller):
        self.controller = controller

    def show_menu(self, user):
        while True:
            is_admin = (user and user.role == "Admin")
            menu = self._build_menu(is_admin)
            choice = menu.show()
            if choice in ("0", None):
                break
            if menu.execute(choice, user) == "break":
                break

    def _build_menu(self, is_admin):
        items = [
            MenuItem("1", "Списък с доставчици", self.show_suppliers),
            MenuItem("2", "Търсене на доставчик", self.search_supplier)]

        if is_admin:
            items.extend([
                MenuItem("3", "Добавяне на доставчик", self.add_supplier),
                MenuItem("4", "Редактиране на доставчик", self.edit_supplier),
                MenuItem("5", "Изтриване на доставчик", self.delete_supplier)])

        items.append(MenuItem("0", "Назад", lambda u: "break"))
        return Menu("Меню Доставчици", items)

    def show_suppliers(self, _):
        suppliers = self.controller.get_all()
        if not suppliers:
            print("\nНяма налични доставчици.")
            return

        print("\nСПИСЪК С ДОСТАВЧИЦИ")
        columns = ["ID", "Име", "Контакт", "Адрес"]
        rows = [[s.supplier_id[:8], s.name, s.contact, s.address] for s in suppliers]
        print(format_table(columns, rows))

    def search_supplier(self, _):
        print("\nТърсене на доставчик")
        query = input("Въведете кратко ID или име: ").strip()
        if not query:
            print("Празно търсене.")
            return

        results = self.controller.search(query)
        if not results:
            print("Няма намерени резултати.")
            return

        print("\nНамерени доставчици:")
        columns = ["ID", "Име", "Контакт", "Адрес"]
        rows = [[s.supplier_id[:8], s.name, s.contact, s.address] for s in results]
        print(format_table(columns, rows))

    def add_supplier(self, _):
        print("\nНов доставчик ")

        # --- ИМЕ ---
        while True:
            name = input("Име: ").strip()
            if not name:
                return

            error = self.controller.validate_field("name", name)
            if error:
                print(f"Грешка: {error}")
                continue

            try:
                SupplierValidator.validate_unique_name(name, self.controller.suppliers)
            except ValueError as e:
                print(f"Грешка: {e}")
                continue

            break


        while True:
            contact = input("Контакт (тел/имейл): ").strip()
            if not contact:
                return

            error = self.controller.validate_field("contact", contact)
            if not error:
                break
            print(f"Грешка: {error}")


        while True:
            address = input("Адрес: ").strip()
            if not address:
                return

            error = self.controller.validate_field("address", address)
            if not error:
                break
            print(f"Грешка: {error}")

        try:
            new_s = self.controller.add(name=name, contact=contact, address=address)
            print(f"\nДоставчикът е добавен успешно. ID: {new_s.supplier_id[:8]}")
        except Exception as e:
            print(f"Грешка при запис: {e}")

    def edit_supplier(self, _):
        print("\nРедактиране на доставчик")
        sid = input("Въведете ID: ").strip()
        if not sid:
            return

        supplier = self.controller.get_by_id(sid)
        if not supplier:
            print("Не е намерен доставчик.")
            return

        print(f"\nРедакция на: {supplier.name}")


        while True:
            n = input(f"Ново име [{supplier.name}]: ").strip()
            new_name = n if n else supplier.name

            error = self.controller.validate_field("name", new_name)
            if error:
                print(f"Грешка: {error}")
                continue

            try:
                SupplierValidator.validate_unique_name(
                    new_name,
                    self.controller.suppliers,
                    exclude_id=supplier.supplier_id
                )
            except ValueError as e:
                print(f"Грешка: {e}")
                continue

            break


        while True:
            c = input(f"Нов контакт [{supplier.contact}]: ").strip()
            new_contact = c if c else supplier.contact

            error = self.controller.validate_field("contact", new_contact)
            if not error:
                break
            print(f"Грешка: {error}")


        while True:
            a = input(f"Нов адрес [{supplier.address}]: ").strip()
            new_address = a if a else supplier.address

            error = self.controller.validate_field("address", new_address)
            if not error:
                break
            print(f"Грешка: {error}")

        try:
            self.controller.update(supplier_id=supplier.supplier_id, name=new_name, contact=new_contact, address=new_address)
            print("Данните са обновени успешно.")
        except Exception as e:
            print(f"Проблем при обновяване: {e}")

    def delete_supplier(self, _):
        print("\nИзтриване на доставчик")
        sid = input("ID на доставчик: ").strip()
        if not sid:
            return

        supplier = self.controller.get_by_id(sid)
        if not supplier:
            print("Няма доставчик с такова ID.")
            return

        try:
            if self.controller.remove(supplier.supplier_id):
                print(f"Доставчикът '{supplier.name}' е премахнат успешно.")
        except Exception as e:
            print(f"Грешка при изтриване: {e}")
