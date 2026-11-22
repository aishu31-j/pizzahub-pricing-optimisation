"""Data loading and feature engineering for the PizzaHub pricing analysis."""
from pathlib import Path
import numpy as np
import pandas as pd

POLICY_DATE = pd.Timestamp("2023-03-01")
ROOT = Path(__file__).resolve().parents[1]   # repo root
DISCOUNT = 0.05
BASE_PRICE = 16.0
FOOD_COST = 4.0          # variable cost per pizza ($)
DELIVERY_COST_PER_MILE = 0.5
FIXED_COST_PER_YEAR = 5000.0

RENAME = {
    "Date": "date", "Region": "region", "Unit Price": "price",
    "Quantity Ordered": "qty", "Distance": "distance",
    "Delivery Fees": "fee", "Discount Applied": "discount",
}


def load_orders(path=ROOT / "data" / "pizzahub_orders.csv") -> pd.DataFrame:
    df = pd.read_csv(Path(path), parse_dates=["Date"]).rename(columns=RENAME)
    df["post"] = (df["date"] >= POLICY_DATE).astype(int)
    assert (df["qty"] > 0).all(), "log model requires strictly positive quantities"
    df["log_q"] = np.log(df["qty"])
    return df.sort_values(["region", "date"]).reset_index(drop=True)


def did_sample(df: pd.DataFrame, treated_region: int, controls=(1, 2)) -> pd.DataFrame:
    """Treated region + controls, with a `treat` indicator."""
    out = df[df["region"].isin([*controls, treated_region])].copy()
    out["treat"] = (out["region"] == treated_region).astype(int)
    return out