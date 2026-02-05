

class MenuItem:
    def __init__(self, key, text, action):
        self.key = key
        self.text = text
        self.action = action


class Menu:
    def __init__(self, title, items):
        self.title = title
        self.items = items

    def show(self):
        print(f"\n   {self.title}   ")
        for item in self.items:
            print(f"{item.key}.{item.text}")
        return input("Избор: ")

    def execute(self, choice, user):
        for item in self.items:
            if item.key == choice:
                return item.action(user)
        print("Невалиден избор.")
        return None
