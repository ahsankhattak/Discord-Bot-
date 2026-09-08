

import pandas as pd


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    print(f"[Clean Agent] Starting with {df.shape[0]} rows, {df.shape[1]} columns")

    cleaned = df.copy()

    # 1. Drop exact duplicate rows
    before = len(cleaned)
    cleaned = cleaned.drop_duplicates()
    print(f"[Clean Agent] Removed {before - len(cleaned)} duplicate rows")

    # 2. Make sure key numeric columns are actually numeric
    numeric_cols = ["Sales", "Quantity", "Discount", "Profit"]
    for col in numeric_cols:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    # 3. Drop rows missing anything critical to analysis
    critical_cols = [c for c in ["Sales", "Quantity", "Product_Name"] if c in cleaned.columns]
    before = len(cleaned)
    cleaned = cleaned.dropna(subset=critical_cols)
    print(f"[Clean Agent] Removed {before - len(cleaned)} rows missing critical fields")

    # 4. Fill small gaps in non-critical text fields instead of dropping the row
    text_cols = ["Region", "Category", "Sub_Category", "Segment"]
    for col in text_cols:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].fillna("Unknown")

    # 5. Remove obviously broken rows (negative sales/quantity make no sense here)
    before = len(cleaned)
    if "Sales" in cleaned.columns:
        cleaned = cleaned[cleaned["Sales"] >= 0]
    if "Quantity" in cleaned.columns:
        cleaned = cleaned[cleaned["Quantity"] >= 0]
    print(f"[Clean Agent] Removed {before - len(cleaned)} rows with negative sales/quantity")

    print(f"[Clean Agent] Finished with {cleaned.shape[0]} rows, {cleaned.shape[1]} columns")
    return cleaned


if __name__ == "__main__":
    # Lets you test this agent completely on its own, no LangGraph needed yet.
    raw = pd.read_csv("data/superstore.csv")
    result = clean_data(raw)
    result.to_csv("data/superstore_cleaned.csv", index=False)
    print("[Clean Agent] Saved cleaned file to data/superstore_cleaned.csv")
