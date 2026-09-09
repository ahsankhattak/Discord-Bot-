"""
Domain Configuration Agent
--------------------------
Runs BEFORE the orchestrator's clean/analyze nodes. Looks at whatever dataset
comes in (columns, dtypes, a sample of rows) and figures out:
1. What domain/type of data this is (retail_sales, inventory, ecommerce_orders,
   restaurant_sales, subscription_saas, etc.)
2. Which real column names map to generic roles (date_col, value_col,
   category_col, id_col) so downstream agents don't have to hardcode
   "Sales" / "Region" / "Category" like Phase 2 did.
3. What "success metrics" make sense to compute for this domain.

This is what makes the pipeline reusable across different-shaped datasets
instead of only working on the Superstore CSV.
"""

import json
import os
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

DOMAIN_CONFIG_PROMPT = """You are a data domain classification expert.

Given a dataset's columns, dtypes, and a small sample of rows, do the following:

1. Identify the most likely business domain. Choose from: retail_sales,
   ecommerce_orders, inventory_stock, restaurant_sales, subscription_saas,
   or "unknown" if it genuinely does not fit any of these.
2. Map the dataset's ACTUAL column names (use exact names from the columns list,
   or null if no good match exists) to these logical roles:
   - date_col: a date/time column, if any
   - value_col: the main numeric metric to sum/analyze (revenue, sales, price, etc.)
   - category_col: a column to group the value_col by (category, region, product type)
   - id_col: a unique identifier column (order id, customer id, etc.)
3. Propose 3-5 "success_metrics" (short strings) that make sense for THIS domain
   given the columns actually available.
4. If the data looks malformed or ambiguous, say so honestly in "notes" instead
   of guessing wildly.

Columns: {columns}
Dtypes: {dtypes}
Sample rows: {sample}

Respond with ONLY valid JSON, no markdown fences, matching exactly this schema:
{{
  "domain": string,
  "confidence": float between 0 and 1,
  "key_columns": {{
    "date_col": string or null,
    "value_col": string or null,
    "category_col": string or null,
    "id_col": string or null
  }},
  "success_metrics": [string, ...],
  "notes": string
}}
"""


def detect_domain_config(df: pd.DataFrame) -> dict:
    print(f"[Domain Config Agent] Inspecting {df.shape[0]} rows, {df.shape[1]} columns")

    try:
        columns = list(df.columns)
        dtypes = {c: str(df[c].dtype) for c in df.columns}
        sample = df.head(5).to_dict(orient="records")

        llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0,
            api_key=os.environ["GROQ_API_KEY"],
        )
        prompt = ChatPromptTemplate.from_template(DOMAIN_CONFIG_PROMPT)
        chain = prompt | llm
        response = chain.invoke(
            {"columns": columns, "dtypes": dtypes, "sample": sample}
        )

        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.replace("json", "", 1).strip()

        config = json.loads(raw)

        print(f"[Domain Config Agent] Detected domain: {config['domain']} "
              f"(confidence: {config['confidence']})")
        print(f"[Domain Config Agent] Key columns: {config['key_columns']}")

        return config

    except Exception as e:
        print(f"[Domain Config Agent] Failed to detect domain: {e}")
        return {
            "domain": "unknown",
            "confidence": 0.0,
            "key_columns": {
                "date_col": None,
                "value_col": None,
                "category_col": None,
                "id_col": None,
            },
            "success_metrics": [],
            "notes": f"Domain detection failed: {e}",
        }


if __name__ == "__main__":
    raw = pd.read_csv("data/superstore.csv")
    config = detect_domain_config(raw)

    with open("data/domain_config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("[Domain Config Agent] Saved config to data/domain_config.json")
