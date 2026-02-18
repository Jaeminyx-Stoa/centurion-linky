from decimal import Decimal


def calculate_discount(regular_price: Decimal, event_price: Decimal | None) -> tuple[Decimal | None, bool]:
    """Calculate discount rate and warning flag.

    Returns:
        (discount_rate, discount_warning)
    """
    if not event_price or not regular_price or regular_price <= 0:
        return None, False

    discount_rate = (regular_price - event_price) / regular_price * 100
    discount_rate = round(discount_rate, 2)
    discount_warning = discount_rate > Decimal("49.0")
    return Decimal(str(discount_rate)), discount_warning
