from functools import wraps

# Декоратор за защита с парола (видима при въвеждане)
def require_password(correct_password):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Тук паролата ще се вижда при въвеждане
            password = input("Въведете парола: ")

            if password == correct_password:
                print("Достъп разрешен!\n")
                return func(*args, **kwargs)
            else:
                print("Достъп отказан! Невалидна парола.\n")
                return None

        return wrapper
    return decorator


# Protected products menu
@require_password("parola123")  # Задай паролата тук
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
