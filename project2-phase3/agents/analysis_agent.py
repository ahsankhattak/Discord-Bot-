"""
Analysis Agent (Phase 3 - domain-aware)
----------------------------------------
Phase 2 version hardcoded column names like "Sales", "Region", "Category".
This version reads the "key_columns" produced by the Domain Config Agent
instead, so it works on any dataset shape - not just Superstore.
"""

import pandas as pd


def analyze_data(df: pd.DataFrame, domain_config: dict) -> dict:
    print(f"[Analysis Agent] Analyzing {df.shape[0]} rows "
          f"(domain: {domain_config.get('domain', 'unknown')})")

    insights = {
        "domain": domain_config.get("domain", "unknown"),
        "total_records": len(df),
    }

    cfg = domain_config.get("key_columns", {})
    value_col = cfg.get("value_col")
    category_col = cfg.get("category_col")
    date_col = cfg.get("date_col")
    id_col = cfg.get("id_col")

    errors = []

    try:
        if value_col and value_col in df.columns:
            insights["total_value"] = round(float(df[value_col].sum()), 2)
            insights["value_col_name"] = value_col
        else:
            errors.append("No value_col found - skipping total value calculation")
    except Exception as e:
        errors.append(f"total_value failed: {e}")

    try:
        if id_col and id_col in df.columns:
            insights["unique_ids"] = int(df[id_col].nunique())
            insights["id_col_name"] = id_col
    except Exception as e:
        errors.append(f"unique_ids failed: {e}")

    try:
        if category_col and value_col and category_col in df.columns and value_col in df.columns:
            by_category = (
                df.groupby(category_col)[value_col]
                .sum()
                .sort_values(ascending=False)
                .head(5)
            )
            insights["top_5_by_category"] = {str(k): float(v) for k, v in by_category.round(2).items()}
            insights["category_col_name"] = category_col
    except Exception as e:
        errors.append(f"category breakdown failed: {e}")

    try:
        if date_col and value_col and date_col in df.columns and value_col in df.columns:
            dates = pd.to_datetime(df[date_col], errors="coerce")

            # Bug found while testing on the inventory dataset (2026-09-09):
            # some datasets store dates as plain numbers like 201712 (YYYYMM).
            # pandas silently misreads a raw number as "nanoseconds since 1970"
            # instead of failing, so every row collapses into a fake 1970-01
            # bucket. Detect that case and re-parse assuming YYYYMM format.
            looks_broken = dates.isna().all() or (dates.dt.year < 1990).mean() > 0.5
            if looks_broken:
                dates = pd.to_datetime(
                    df[date_col].astype(str), format="%Y%m", errors="coerce"
                )

            valid = dates.notna()
            if valid.any():
                trend = (
                    df.loc[valid]
                    .groupby(dates[valid].dt.to_period("M"))[value_col]
                    .sum()
                )
                insights["trend_over_time"] = {str(k): round(float(v), 2) for k, v in trend.items()}
                insights["date_col_name"] = date_col
            else:
                errors.append(f"'{date_col}' could not be parsed as a date in any known format")
    except Exception as e:
        errors.append(f"trend_over_time failed: {e}")

    if errors:
        insights["errors"] = errors

    print("[Analysis Agent] Insights generated:")
    for key, value in insights.items():
        print(f"  {key}: {value}")

    return insights


if __name__ == "__main__":
    import json

    df = pd.read_csv("data/superstore_cleaned.csv")

    with open("data/domain_config.json") as f:
        domain_config = json.load(f)

    result = analyze_data(df, domain_config)

    with open("data/insights.json", "w") as f:
        json.dump(result, f, indent=2)
    print("[Analysis Agent] Saved insights to data/insights.json")
