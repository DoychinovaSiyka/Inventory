from functools import wraps
import pwinput # Hides the password input


# Decorator to require a password
def require_password(correct_password):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                password = pwinput.pwinput(prompt ="Въведете парола: ",mask = "$")
            except Exception:
                # Fallback if getpass cannot hide input
                password = input("Въведете парола (ще се вижда): ")

            if password == correct_password:
                print("Достъп разрешен!\n")
                return func(*args,**kwargs)
            else:
                print("Достъп отказан! Невалидна парола.\n")
                return None


        return wrapper

    return decorator


# Protected products menu
@require_password("parola123")  # Set your password here
def show_products_menu(product_controller):
    products = product_controller.get_all()
    if not products:
        print("Няма налични продукти.")
    else:
        print("\nСписъкът с продукти:")
        for p in products:
            categories_names = ", ".join([c.name for c in p.categories])
            print(
                f"- {p.name} | Категории: {categories_names} | "
                f"Количество: {p.quantity}бр. | Цена: {p.price:.2f} лв."
            )