import json

from models.product import Product

def save_json(filename,data):

    with open(f"data/{filename}","w",encoding= "utf-8") as file:
        json.dump(data, file,ensure_ascii= False,indent= 4)


def load_json(filename,list_ =None):
    with open(f"data/{filename}","r",encoding= "utf-8") as f:
        list_ = json.load(f)
    products = [Product(*item) for item in list_]
    return products





# Тук имам списък от речници (list of dicts).
# Всеки речник описва продукт със свойства: name, price, quantity, description, category_id, supplier_id.
# Някои ключове (например "categories") съдържат вложен списък от речници за категориите.
# Затова при десериализация използвам Product.from_dict(item),
# защото item е речник и ключовете му съвпадат с параметрите на конструктора.










        








