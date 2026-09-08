

import pandas as pd


def analyze_data(df: pd.DataFrame) -> dict:
    print(f"[Analysis Agent] Analyzing {df.shape[0]} rows")

    insights = {}

    insights["total_sales"] = round(df["Sales"].sum(), 2)
    insights["total_orders"] = df["Order_ID"].nunique() if "Order_ID" in df.columns else len(df)
    insights["total_quantity"] = int(df["Quantity"].sum())

    if "Profit" in df.columns:
        insights["total_profit"] = round(df["Profit"].sum(), 2)

    if "Product_Name" in df.columns:
        top_products = (
            df.groupby("Product_Name")["Sales"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )
        insights["top_5_products"] = top_products.round(2).to_dict()

    if "Region" in df.columns:
        sales_by_region = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)
        insights["sales_by_region"] = sales_by_region.round(2).to_dict()

    if "Category" in df.columns:
        sales_by_category = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)
        insights["sales_by_category"] = sales_by_category.round(2).to_dict()

    print("[Analysis Agent] Insights generated:")
    for key, value in insights.items():
        print(f"  {key}: {value}")

    return insights


if __name__ == "__main__":
    # Lets you test this agent completely on its own.
    df = pd.read_csv("data/superstore_cleaned.csv")
    result = analyze_data(df)

    import json
    with open("data/insights.json", "w") as f:
        json.dump(result, f, indent=2)
    print("[Analysis Agent] Saved insights to data/insights.json")
