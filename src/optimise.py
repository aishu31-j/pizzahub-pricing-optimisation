"""Profit optimisation under constant-elasticity demand.

Contribution per order = (food price - food cost) + (delivery fee - delivery cost)
Daily profit           = orders * contribution   (fixed costs don't move the optimum)

Elasticities come from ONE 5% price change, so anything far from the observed price
is extrapolation. The optimiser is therefore limited to a 'trust region' (max
discount) and, optionally, a capacity ceiling on daily orders.
"""
import numpy as np
import pandas as pd
from .data import BASE_PRICE, FOOD_COST, DELIVERY_COST_PER_MILE


def demand(price, base_price, base_qty, eta, capacity=None):
    q = base_qty * (price / base_price) ** eta
    return np.minimum(q, capacity) if capacity else q


def margin_per_order(food_price, fee, distance):
    return (food_price - FOOD_COST) + (fee - DELIVERY_COST_PER_MILE * distance)


def effective_mc(lever, distance):
    """Marginal cost of the lever's own price once the other margin is netted out.
    Food: $4. Fee: delivery cost minus the (food price - food cost) earned on the
    extra pizza, so it can be negative."""
    if lever == "food":
        return FOOD_COST
    return DELIVERY_COST_PER_MILE * distance - (BASE_PRICE - FOOD_COST)


def ier_price(mc, eta):
    """Inverse-elasticity rule P* = MC / (1 + 1/eta). None if no finite optimum."""
    if eta >= -1:
        return None
    return mc / (1 + 1 / eta)


def profit_curve(lever, base_qty, eta, distance, discounts, capacity=None):
    """Daily contribution profit at each discount on `lever` ('food' or 'fee')."""
    base_fee = DELIVERY_COST_PER_MILE * distance
    rows = []
    for d in discounts:
        food = BASE_PRICE * (1 - d) if lever == "food" else BASE_PRICE
        fee = base_fee * (1 - d) if lever == "fee" else base_fee
        p, p0 = (food, BASE_PRICE) if lever == "food" else (fee, base_fee)
        q = demand(p, p0, base_qty, eta, capacity)
        rows.append((d, food, fee, q, q * margin_per_order(food, fee, distance)))
    return pd.DataFrame(rows, columns=["discount", "food_price", "fee", "orders", "profit"])


def best_in_trust_region(lever, base_qty, eta, distance, max_discount=0.15,
                         capacity=None, n=151):
    grid = np.linspace(-max_discount, max_discount, n)   # negative = price increase
    c = profit_curve(lever, base_qty, eta, distance, grid, capacity)
    return c.loc[c["profit"].idxmax()]