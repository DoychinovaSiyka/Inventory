from views.menu import Menu, MenuItem
from views.password_utils import format_table

from controllers.product_controller import ProductController
from controllers.movement_controller import MovementController
from controllers.user_controller import UserController
from controllers.location_controller import LocationController
from controllers.supplier_controller import SupplierController
from controllers.inventory_controller import InventoryController







class MovementView:
    def __init__(self, product_controller, movement_controller, user_controller,
                 location_controller, supplier_controller, inventory_controller):

        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller
        self.inventory_controller = inventory_controller



    def _float(self, prompt):
        while True:
            value = input(prompt).strip().replace(",", ".")
            try:
                number = float(value)
                if number > 0:
                    return number
                print("Числото трябва да е положително.")
            except:
                print("Невалидно число.")



    def _choose(self, items, label):
        if not items:
            print(f"Няма {label}.")
            return None

        for i, item in enumerate(items, 1):
            print(f"{i}. {item.name}")

        choice = input("Избор: ").strip()
        if not choice.isdigit():
            return None

        index = int(choice) - 1
        return items[index] if 0 <= index < len(items) else None




    def show_menu(self, user):
        menu = Menu("Логистични операции", [
            MenuItem("1", "Доставка (вход)", self.process_delivery),
            MenuItem("2", "Продажба (изход)", self.process_sale),
            MenuItem("3", "Вътрешно преместване", self.process_transfer),
            MenuItem("0", "Назад", lambda u: "break")])

        while True:
            choice = menu.show()
            if choice in ("0", None):
                break
            if menu.execute(choice, user) == "break":
                break





    def process_delivery(self, user):
        print("\nНова доставка")
        product = self._choose(self.product_controller.get_all(), "продукти")
        if not product:
            return

        supplier = self._choose(self.supplier_controller.get_all(), "доставчици")
        if not supplier:
            return

        location = self._choose(self.location_controller.get_all(), "складове")
        if not location:
            return

        qty = self._float("Количество: ")
        price = input(f"Цена (Enter за {product.price}): ").strip() or product.price

        try:
            self.movement_controller.add_in(str(product.product_id), qty, price,
                                            str(location.location_id), str(supplier.supplier_id), str(user.user_id))
            print("Доставката е записана.")
        except Exception as e:
            print("Грешка:", e)







    def process_sale(self, user):
        print("\nНова продажба")

        product = self._choose(self.product_controller.get_all(), "продукти")
        if not product:
            return

        stock_locations = []
        for loc in self.location_controller.get_all():
            if self.inventory_controller.get_stock(str(product.product_id), str(loc.location_id)) > 0:
                stock_locations.append(loc)

        location = self._choose(stock_locations, "складове с наличност")
        if not location:
            return

        max_qty = self.inventory_controller.get_stock(str(product.product_id), str(location.location_id))
        qty = self._float(f"Количество (макс {max_qty}): ")
        if qty > max_qty:
            print("Недостатъчна наличност.")
            return

        price = input(f"Цена (Enter за {product.price}): ").strip() or product.price
        customer = input("Клиент: ").strip() or "Общ клиент"

        try:
            self.movement_controller.add_out(str(product.product_id), qty, customer, str(location.location_id),
                                             str(user.user_id), price)
            print("Продажбата е записана.")
        except Exception as e:
            print("Грешка:", e)







    def process_transfer(self, user):
        print("\nВътрешно преместване")

        product = self._choose(self.product_controller.get_all(), "продукти")
        if not product:
            return

        sources = []
        for loc in self.location_controller.get_all():
            if self.inventory_controller.get_stock(str(product.product_id), str(loc.location_id)) > 0:
                sources.append(loc)

        from_loc = self._choose(sources, "складове с наличност")
        if not from_loc:
            return

        available = self.inventory_controller.get_stock(str(product.product_id), str(from_loc.location_id))
        print(f"Налично: {available}")

        destinations = []
        for loc in self.location_controller.get_all():
            if str(loc.location_id) != str(from_loc.location_id):
                destinations.append(loc)

        to_loc = self._choose(destinations, "други складове")
        if not to_loc:
            return

        qty = self._float(f"Количество (макс {available}): ")
        if qty > available:
            print("Недостатъчна наличност.")
            return

        try:
            self.movement_controller.move_stock(str(product.product_id), qty, str(from_loc.location_id),
                                                str(to_loc.location_id), str(user.user_id))
            print("Преместването е записано.")
        except Exception as e:
            print("Грешка:", e)
