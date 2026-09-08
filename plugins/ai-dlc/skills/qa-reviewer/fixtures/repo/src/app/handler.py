from src.domain import order


def handle(req):
    return order.total(req)
