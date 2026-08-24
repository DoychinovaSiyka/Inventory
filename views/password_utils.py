from functools import wraps




def format_table(columns, rows):
    if not rows:
        return "\nНяма налични данни.\n"

    col_widths = [len(str(c)) for c in columns]

    for row in rows:
        for i, val in enumerate(row):
            val_str = str(val)
            if len(val_str) > col_widths[i]:
                col_widths[i] = len(val_str)

    col_widths = [w + 2 for w in col_widths]
    separator = "+" + "+".join("-" * w for w in col_widths) + "+"

    header_cells = [col.center(col_widths[i]) for i, col in enumerate(columns)]
    header_row = "|" + "|".join(header_cells) + "|"

    data_lines = []
    for row in rows:
        row_cells = []
        for i, val in enumerate(row):
            val_str = str(val)
            if val_str.replace(".", "", 1).isdigit():
                cell = val_str.rjust(col_widths[i])
            else:
                cell = val_str.ljust(col_widths[i])
            row_cells.append(cell)
        data_lines.append("|" + "|".join(row_cells) + "|")

    return "\n" + "\n".join([separator, header_row, separator] + data_lines + [separator]) + "\n"





# Роли - админ / оператор / наблюдател
def require_role(role):
    """Декоратор за ограничаване на достъпа по роля."""
    def decorator(func):
        @wraps(func)
        def wrapper(user, *args, **kwargs):
            if user.role != role:
                print(f"Нямате права за тази операция (нужна роля: {role}).")
                return
            return func(user, *args, **kwargs)
        return wrapper
    return decorator






def require_password(password_required):
    def decorator(func):
        @wraps(func)
        def wrapper(user, *args, **kwargs):
            password = input("Въведете парола: ").strip()
            if password == password_required:
                print("Достъп разрешен!\n")
                return func(user, *args, **kwargs)
            else:
                print("Достъп отказан! Невалидна парола.\n")
                return None
        return wrapper
    return decorator



# Показване на продукти - само за админ
@require_role("admin")
@require_password("parola123")
def show_products_menu(user, product_controller):
    products = product_controller.get_all()
    if not products:
        print("Няма продукти.")
        return

    columns = ["ID", "Име", "Цена", "Количество", "Категории"]
    rows = []

    for p in products:
        categories = ", ".join([c.name for c in p.categories])
        rows.append([p.product_id, p.name, p.price, p.quantity, categories])

    print("\n" + format_table(columns, rows))
