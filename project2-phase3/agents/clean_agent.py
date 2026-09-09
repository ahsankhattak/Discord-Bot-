"""
Clean Agent (Phase 3 - domain-aware)
--------------------------------------
Phase 2 version hardcoded column names like "Sales", "Region", "Product_Name".
This version accepts the domain_config produced by the Domain Config Agent and
cleans around whichever columns actually matter for THIS dataset - so it works
on retail, restaurant, inventory, or ecommerce data without being rewritten.

If no domain_config is passed, it falls back to basic generic cleaning only
(dedupe + drop fully blank rows) so it never crashes on an unexpected shape.
"""

import pandas as pd


def clean_data(df: pd.DataFrame, domain_config: dict = None) -> pd.DataFrame:
    print(f"[Clean Agent] Starting with {df.shape[0]} rows, {df.shape[1]} columns")

    cleaned = df.copy()

    before = len(cleaned)
    cleaned = cleaned.dropna(how="all")
    print(f"[Clean Agent] Removed {before - len(cleaned)} fully blank rows")

    before = len(cleaned)
    cleaned = cleaned.drop_duplicates()
    print(f"[Clean Agent] Removed {before - len(cleaned)} duplicate rows")

    cfg = (domain_config or {}).get("key_columns", {})
    value_col = cfg.get("value_col")
    category_col = cfg.get("category_col")
    id_col = cfg.get("id_col")

    if value_col and value_col in cleaned.columns:
        cleaned[value_col] = pd.to_numeric(cleaned[value_col], errors="coerce")

    critical_cols = [c for c in [value_col] if c and c in cleaned.columns]
    if critical_cols:
        before = len(cleaned)
        cleaned = cleaned.dropna(subset=critical_cols)
        print(f"[Clean Agent] Removed {before - len(cleaned)} rows missing {critical_cols}")

    if category_col and category_col in cleaned.columns:
        cleaned[category_col] = cleaned[category_col].fillna("Unknown")

    if value_col and value_col in cleaned.columns:
        before = len(cleaned)
        cleaned = cleaned[cleaned[value_col] >= 0]
        print(f"[Clean Agent] Removed {before - len(cleaned)} rows with negative {value_col}")

    print(f"[Clean Agent] Finished with {cleaned.shape[0]} rows, {cleaned.shape[1]} columns")
    return cleaned


if __name__ == "__main__":
    import json

    raw = pd.read_csv("data/superstore.csv")

    with open("data/domain_config.json") as f:
        domain_config = json.load(f)

    result = clean_data(raw, domain_config)
    result.to_csv("data/superstore_cleaned.csv", index=False)
    print("[Clean Agent] Saved cleaned file to data/superstore_cleaned.csv")
