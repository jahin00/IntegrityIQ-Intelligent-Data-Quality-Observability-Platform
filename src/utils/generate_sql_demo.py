from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "retail_transactions_dirty.csv"
OUT = ROOT / "data" / "sql" / "retail_quality_demo.db"


def main():
    orders = pd.read_csv(RAW, low_memory=False).copy()
    orders["expected_total"] = (
        orders["quantity"] * orders["unit_price"] * (1 - orders["discount"])
    ).round(2)
    orders["actual_total"] = orders["total_amount"]

    customers = (
        orders[["customer_id", "customer_age", "region"]]
        .drop_duplicates("customer_id")
        .rename(columns={"region": "customer_region"})
        .reset_index(drop=True)
    )
    products = pd.DataFrame({
        "product_id": [f"P{i:04d}" for i in range(1, 11)],
        "product_category": [
            "Electronics", "Fashion", "Home", "Sports", "Beauty",
            "Books", "Grocery", "Toys", "Automotive", "Garden"
        ],
    })

    product_map = dict(zip(products["product_category"], products["product_id"]))
    orders["product_id"] = orders["product_category"].map(product_map).fillna("P0001")

    # Inject relational-quality problems deliberately.
    if len(orders) >= 30:
        orders.loc[5, "customer_id"] = "CUST-MISSING-999"
        orders.loc[10, "region"] = None
        orders.loc[15, "actual_total"] = orders.loc[15, "expected_total"] + 25.00
        orders.loc[20, "transaction_id"] = orders.loc[0, "transaction_id"]
        orders.loc[25, "actual_total"] = -100.00

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(OUT) as conn:
        customers.to_sql("customers", conn, if_exists="replace", index=False)
        products.to_sql("products", conn, if_exists="replace", index=False)
        orders[
            [
                "transaction_id", "customer_id", "transaction_date", "region",
                "product_id", "quantity", "unit_price", "discount",
                "payment_method", "customer_age", "expected_total", "actual_total",
            ]
        ].to_sql("orders", conn, if_exists="replace", index=False)

    print(f"Created {OUT}")


if __name__ == "__main__":
    main()
