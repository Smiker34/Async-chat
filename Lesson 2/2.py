import json


def write_order_to_json(item, quantity, price, buyer, date):
    order = {"item": item,
             "quantity": quantity,
             "price": price,
             "buyer": buyer,
             "date": date}

    with open('orders.json', 'r+') as f:
        data = json.load(f)
        data["orders"].append(order)
        f.seek(0)
        json.dump(data, f, indent=4)


write_order_to_json("test", 1, 10, "test", "10-10-2020")
