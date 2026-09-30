from pathlib import Path
import numpy as np
import pandas as pd


RNG = np.random.default_rng(42)


def generate_clean_data(n_rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    regions = np.array(["Dhaka", "Chattogram", "Sylhet", "Rajshahi", "Khulna"])
    categories = np.array(["Electronics", "Grocery", "Fashion", "Home", "Beauty"])
    payments = np.array(["Cash", "Card", "Mobile Banking", "Bank Transfer"])

    transaction_ids = [f"TXN-{i:06d}" for i in range(1, n_rows + 1)]
    customer_ids = [f"CUST-{rng.integers(1, 1800):05d}" for _ in range(n_rows)]
    dates = pd.date_range("2026-01-01", periods=210, freq="D").strftime("%Y-%m-%d").to_numpy()

    df = pd.DataFrame(
        {
            "transaction_id": transaction_ids,
            "customer_id": customer_ids,
            "transaction_date": rng.choice(dates, n_rows),
            "region": rng.choice(regions, n_rows),
            "product_category": rng.choice(categories, n_rows),
            "quantity": rng.integers(1, 11, n_rows),
            "unit_price": np.round(rng.uniform(50, 5000, n_rows), 2),
            "discount": np.round(rng.uniform(0, 0.30, n_rows), 2),
            "payment_method": rng.choice(payments, n_rows),
            "customer_age": rng.integers(18, 71, n_rows),
        }
    )
    df["total_amount"] = np.round(
        df["quantity"] * df["unit_price"] * (1 - df["discount"]), 2
    )
    return df


def generate_data(n_rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Generate a deliberately dirty current-period retail dataset."""
    rng = np.random.default_rng(seed)
    df = generate_clean_data(n_rows=n_rows, seed=seed)

    # Distribution shift: a later batch has systematically higher unit prices.
    shift_start = int(len(df) * 0.70)
    shifted_idx = df.index[shift_start:]
    df.loc[shifted_idx, "unit_price"] = np.round(df.loc[shifted_idx, "unit_price"] * 1.45, 2)
    df.loc[shifted_idx, "total_amount"] = np.round(
        df.loc[shifted_idx, "quantity"]
        * df.loc[shifted_idx, "unit_price"]
        * (1 - df.loc[shifted_idx, "discount"]),
        2,
    )

    # Missing values
    for col, fraction in {"customer_age": 0.02, "region": 0.01, "total_amount": 0.005}.items():
        idx = rng.choice(df.index, int(len(df) * fraction), replace=False)
        df.loc[idx, col] = np.nan

    # Exact duplicate rows
    duplicate_rows = df.sample(12, random_state=42)
    df = pd.concat([df, duplicate_rows], ignore_index=True)

    # Primary-key duplicates
    key_idx = rng.choice(df.index, 10, replace=False)
    df.loc[key_idx, "transaction_id"] = df.loc[key_idx, "transaction_id"].iloc[0]

    # Category inconsistencies
    variant_idx = rng.choice(df.index, 80, replace=False)
    variants = ["dhaka", "DHAKA", "Dhaka ", "chattogram", "CHATTOGRAM"]
    df.loc[variant_idx, "region"] = rng.choice(variants, len(variant_idx))

    # Numeric outliers
    outlier_idx = rng.choice(df.index, 15, replace=False)
    df.loc[outlier_idx, "quantity"] = rng.choice([100, 250, 999], len(outlier_idx))

    # Invalid values
    invalid_discount_idx = rng.choice(df.index, 8, replace=False)
    df.loc[invalid_discount_idx, "discount"] = rng.choice([1.2, 1.5, -0.2], len(invalid_discount_idx))

    invalid_age_idx = rng.choice(df.index, 8, replace=False)
    df.loc[invalid_age_idx, "customer_age"] = rng.choice([-5, 0, 150, 190], len(invalid_age_idx))

    # Date anomalies: invalid strings and future dates
    invalid_date_idx = rng.choice(df.index, 7, replace=False)
    df.loc[invalid_date_idx, "transaction_date"] = "2026-15-45"

    future_date_idx = rng.choice(df.index, 10, replace=False)
    df.loc[future_date_idx, "transaction_date"] = "2028-01-15"

    return df


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    raw_dir = root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    reference = generate_clean_data()
    current = generate_data()

    reference_path = raw_dir / "retail_transactions_reference.csv"
    current_path = raw_dir / "retail_transactions_dirty.csv"
    reference.to_csv(reference_path, index=False)
    current.to_csv(current_path, index=False)

    print(f"Reference dataset: {len(reference):,} rows -> {reference_path}")
    print(f"Current dirty dataset: {len(current):,} rows -> {current_path}")
