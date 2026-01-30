from functools import wraps



def format_table(columns, rows):
    all_rows = [columns] + rows
    col_widths = [max(len(str(row[i])) for row in all_rows) + 2 for i in range(len(columns))]

    top_border = "+" + "+".join("-" * w for w in col_widths) + "+"
    header = "|" + "|".join(columns[i].center(col_widths[i]) for i in range(len(columns))) + "|"
    separator = "+" + "+".join("-" * w for w in col_widths) + "+"

    data = []
    for row in rows:
        line = "|"
        for i, cell in enumerate(row):
            cell_str = f"{cell:.2f}" if isinstance(cell, float) else str(cell)
            if isinstance(cell, (int, float)):
                line += cell_str.rjust(col_widths[i]) + "|"
            else:
                line += cell_str.ljust(col_widths[i]) + "|"
        data.append(line)

    bottom_border = top_border
    return "\n".join([top_border, header, separator] + data + [bottom_border])

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



@require_password("parola123")  # защита с парола
def show_products_menu(product_controller):
    products = product_controller.get_all()

    if not products:
        print("Няма продукти.")
        return

    columns = ["ID", "Име", "Цена", "Количество", "Категории"]

    rows = []
    for p in products:
        categories = ", ".join([c.name for c in p.categories])
        rows.append([
            p.product_id,
            p.name,
            p.price,
            p.quantity,
            categories
        ])

    print("\n" + format_table(columns, rows))

