"""Generate 5 trap datasets with known ground truth. Run: python -m eval.make_traps"""
import json, pathlib
import numpy as np, pandas as pd
OUT = pathlib.Path(__file__).parent / "data"; OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(42)

def save(name, df, truth):
    df.to_csv(OUT / f"{name}.csv", index=False); (OUT / f"{name}.json").write_text(json.dumps(truth, indent=2))

def base(n=1500):
    d = pd.DataFrame({"Order Date": rng.choice(pd.date_range("2024-01-01", "2025-06-30"), n),
                      "Region": rng.choice(["North", "South", "East", "West"], n),
                      "Category": rng.choice(["Tech", "Furniture", "Office"], n),
                      "Discount": rng.choice([0, .1, .2, .3, .4, .5], n, p=[.35, .2, .15, .1, .1, .1])})
    d["Sales"] = rng.gamma(3, 120, n).round(2)
    d["Profit"] = (d["Sales"] * (0.28 - d["Discount"] * 0.9) + rng.normal(0, 8, n)).round(2)
    return d

# 1. duplicates + legitimate negative profit (caused by discounts) + 3% missing Profit
d = base(); d.loc[d.sample(frac=.03, random_state=1).index, "Profit"] = np.nan
uniq_neg = int((d["Profit"] < 0).sum()); d = pd.concat([d, d.sample(120, random_state=2)], ignore_index=True)
save("t1_dupes_negative_profit", d, {"duplicates": 120, "negative_profit_unique_rows": uniq_neg, "missing_profit_pct": 3})

# 2. numbers and dates stored as text, whitespace
d = base(800); d["Sales"] = d["Sales"].map(lambda v: f"${v:,.2f}"); d["Order Date"] = d["Order Date"].dt.strftime("%Y-%m-%d")
d["Region"] = d["Region"].map(lambda v: f" {v} ")
save("t2_text_formats", d, {"sales_numeric_after": True, "date_datetime_after": True})

# 3. a column that is 65% missing (must NOT be imputed)
d = base(1000); d["Discount_Code"] = np.where(rng.random(1000) < .65, None, rng.choice(["A1", "B2", "C3"], 1000))
save("t3_high_missing", d, {"column": "Discount_Code", "missing_pct": 65})

# 4. seasonality: monthly peak in November + growth trend (3 years daily)
days = pd.date_range("2022-01-01", "2024-12-31"); m = days.month.values
rev = 1000 * (1 + 0.5 * np.cos(2 * np.pi * (m - 11) / 12)) * (1 + 0.0004 * np.arange(len(days))) + rng.normal(0, 40, len(days))
save("t4_seasonal_peak", pd.DataFrame({"Date": days, "Revenue": rev.round(2), "Channel": rng.choice(["Web", "Store"], len(days))}),
     {"peak_month": 11})

# 5. data-entry typos (x1000) mixed with real big orders -> agent must INSPECT before capping
d = base(1200); idx = rng.choice(len(d), 3, replace=False); d.loc[idx, "Sales"] = d.loc[idx, "Sales"] * 1000
big = rng.choice(list(set(range(len(d))) - set(idx)), 2, replace=False); d.loc[big, "Sales"] = d.loc[big, "Sales"] * 4
save("t5_outlier_typos", d, {"typo_rows": [int(i) for i in idx], "legit_big_rows": [int(i) for i in big]})
print("traps written to", OUT)