"""HTTP 层：把领域结果变成给人看的东西。"""
from src.domain.pricing import order_total


def format_money(cents):
    return f"¥{cents // 100}.{cents % 100:02d}"


def get_order_total(lines):
    return {"total": format_money(order_total(lines))}
