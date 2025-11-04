import json

from models.product import Product

def save_json(filename,data):

    with open(f"data/{filename}","w",encoding= "utf-8") as file:
        json.dump(data, file,indent= 4)


def load_json(filename,list_ =None):
    with open(f"data/{filename}","r",encoding= "utf-8") as f:
        list_ = json.load(f)
    products = [Product(*item) for item in list_]
    return products















        








