# Prompt & Pipeline Evolution Log

This log tracks what broke while testing the pipeline across 4 different-domain
datasets, and what was changed to fix it. Each entry is a real failure found
during testing, not a hypothetical.

---

## 1. Domain Config Agent — model name outdated

**Found on:** Superstore (first test run)

**Issue:** The agent was configured to call `llama-3.3-70b-versatile` on Groq.
This model had been retired, so every call failed with a 404 error.

**Fix:** Switched the model to `openai/gpt-oss-120b`, Groq's current
recommended replacement.

**Why it matters:** Even a correctly-designed agent is only as reliable as the
external model it depends on. The fallback error handling caught this cleanly
(the agent logged the failure and returned a safe "unknown" config instead of
crashing), which is exactly the kind of graceful degradation this phase asks for.

---

## 2. Analysis Agent — numeric YYYYMM dates silently misparsed

**Found on:** Inventory dataset

**Issue:** The inventory dataset stores its date column as a plain number,
e.g. `201712` for December 2017, instead of an actual date string. When this
was passed to `pd.to_datetime()`, pandas didn't fail — it silently
interpreted `201712` as *nanoseconds since 1970*, so every row collapsed into
a single fake `1970-01` bucket in the trend chart. No error was raised, which
made this the hardest bug to catch — the pipeline "succeeded" with wrong output.

**Fix:** Added a heuristic check after parsing: if all parsed dates come back
before 1990 (or fail entirely), assume the column is a raw `YYYYMM` code and
re-parse it explicitly with `format="%Y%m"`.

**Why it matters:** This is the core lesson of "production-grade" data
handling — a pipeline that doesn't crash isn't the same as a pipeline that's
correct. Silent misinterpretation is more dangerous than an outright crash,
because it looks fine until someone checks the actual numbers.

---

## 3. Analysis Agent — numpy types breaking JSON export

**Found on:** Inventory dataset (surfaced right after fixing bug #2)

**Issue:** `insights["total_value"]` and similar fields were being computed
with pandas/numpy operations, which return `numpy.int64` / `numpy.float64`
instead of plain Python numbers. `json.dump()` doesn't know how to serialize
these, so the script crashed with `TypeError: Object of type int64 is not
JSON serializable` the moment it tried to save results.

**Fix:** Wrapped every numeric value written into `insights` with an explicit
`float()` or `int()` cast before it gets stored, so the dict going into
`json.dump()` only ever contains plain Python types.

**Why it matters:** This is a common, easy-to-miss failure mode any time
pandas aggregation results get serialized. Worth checking for on any future
dataset, since a domain we haven't tested yet could reintroduce it in a new
column.

---

## 4. Clean Agent — hardcoded Superstore column names

**Found on:** Design review before testing on new datasets (not a runtime
failure, but a planning fix)

**Issue:** The Phase 2 Clean Agent hardcoded column names specific to
Superstore (`Sales`, `Region`, `Product_Name`, `Category`, `Sub_Category`,
`Segment`). This worked fine on Superstore but would have silently done
*nothing* on any other dataset, since none of those columns exist elsewhere.

**Fix:** Rewrote the Clean Agent to accept the `domain_config` produced by
the Domain Config Agent and clean around whichever `value_col` /
`category_col` the config actually found for that dataset - so cleaning
logic (numeric coercion, dropping rows missing the value column, filling
missing categories, removing negative values) applies to any domain.

**Why it matters:** This was the single biggest change required to make the
whole pipeline "reusable instead of hardcoded," which is the stated goal of
this phase.

---

## Observed but not fixed (informational only)

- **E-commerce Orders dataset**: pandas raised a `UserWarning` about
  inconsistent date formats when parsing `Order Date` (some rows use slightly
  different date string formats). It didn't break anything - `errors="coerce"`
  handled it gracefully - but it's a candidate for a future formatting fix if
  more datasets show the same pattern.
- **E-commerce Orders dataset**: the trend chart only shows 2 months
  (`2019-04` and a small sliver of `2019-05`). This is expected -  the source
  file genuinely only contains April 2019 orders with a few late-processed
  entries spilling into early May - not a bug in the pipeline.
