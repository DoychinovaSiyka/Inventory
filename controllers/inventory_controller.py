from controllers.abstract_controller import AbstractController

class InventoryController(AbstractController):
    """Инвентарът се пази като речник: {product_id: {warehouses:{}, total:int}}"""
    def __init__(self, repo, product_controller, location_controller):
        super().__init__(repo)
        self.product_controller = product_controller
        self.location_controller = location_controller

        raw = self.load()

        if not raw or isinstance(raw, list):
            self.inventory = {"products": {}}
        else:
            self.inventory = raw

    def from_dict(self, data):
        return data

    def to_dict(self, obj):
        return obj


    def _save_inventory(self):
        self.save(self.inventory)



    def get_stock(self, product_id, location_id):
        product_id = str(product_id)
        location_id = str(location_id)

        product_entry = self.inventory["products"].get(product_id)
        if not product_entry:
            return 0

        return float(product_entry["warehouses"].get(location_id, 0))



    def increase_stock(self, product_id, quantity, location_id):
        product_id = str(product_id)
        location_id = str(location_id)

        if product_id not in self.inventory["products"]:
            product = self.product_controller.get_by_id(product_id)
            self.inventory["products"][product_id] = {"product_name": product.name, "unit": product.unit,
                                                      "warehouses": {}, "total": 0}

        entry = self.inventory["products"][product_id]
        entry["warehouses"][location_id] = entry["warehouses"].get(location_id, 0) + float(quantity)
        entry["total"] = sum(entry["warehouses"].values())

        self._save_inventory()


    def decrease_stock(self, product_id, quantity, location_id):
        product_id = str(product_id)
        location_id = str(location_id)

        entry = self.inventory["products"].get(product_id)
        if not entry:
            raise ValueError("Продуктът няма наличност.")

        current = entry["warehouses"].get(location_id, 0)
        if current < float(quantity):
            raise ValueError("Недостатъчна наличност.")

        entry["warehouses"][location_id] = current - float(quantity)
        entry["total"] = sum(entry["warehouses"].values())

        self._save_inventory()


    def move_stock(self, product_id, quantity, from_loc, to_loc):
        product_id = str(product_id)
        from_loc = str(from_loc)
        to_loc = str(to_loc)

        entry = self.inventory["products"].get(product_id)
        if not entry:
            raise ValueError("Продуктът няма наличност.")

        current = entry["warehouses"].get(from_loc, 0)
        if current < float(quantity):
            raise ValueError("Недостатъчна наличност за преместване.")

        entry["warehouses"][from_loc] = current - float(quantity)
        entry["warehouses"][to_loc] = entry["warehouses"].get(to_loc, 0) + float(quantity)
        entry["total"] = sum(entry["warehouses"].values())

        self._save_inventory()


    def build_inventory(self):
        return self.inventory
