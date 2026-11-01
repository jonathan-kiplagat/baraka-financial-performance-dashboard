"""Reproduce the report's DAX measures in pandas.

Run ``python analysis/checkpoints.py`` to print the values the Power BI report should
show after a refresh, and to regenerate ``docs/checkpoint_values.md``. Use it to check
the model: if a card or chart disagrees with these numbers, a relationship or measure
is wrong.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BANDS = ["None", "Low", "Medium", "High"]


def load() -> dict[str, pd.DataFrame]:
    # keep_default_na=False: the discount band "None" is a real value, not a missing one.
    sales = pd.read_csv(DATA / "baraka-sales.csv", parse_dates=["month"], keep_default_na=False)
    targets = pd.read_csv(DATA / "baraka-targets.csv", parse_dates=["month"])
    products = pd.read_csv(DATA / "baraka-products.csv")
    markets = pd.read_csv(DATA / "baraka-markets.csv")
    sales = sales.merge(markets, on="market", how="left").merge(products, on="product", how="left")
    sales["year"] = sales["month"].dt.year
    targets["year"] = targets["month"].dt.year
    return {"sales": sales, "targets": targets, "products": products, "markets": markets}


def kpis(sales: pd.DataFrame) -> dict[str, float]:
    total = sales[["gross_sales_kes", "discounts_kes", "sales_kes", "cogs_kes", "profit_kes", "units_sold"]].sum()
    return {
        "Total Sales": total["sales_kes"],
        "Gross Sales": total["gross_sales_kes"],
        "Total Discounts": total["discounts_kes"],
        "Discount %": total["discounts_kes"] / total["gross_sales_kes"],
        "Total COGS": total["cogs_kes"],
        "Total Profit": total["profit_kes"],
        "Profit Margin": total["profit_kes"] / total["sales_kes"],
        "Units Sold": total["units_sold"],
    }


def by(sales: pd.DataFrame, keys) -> pd.DataFrame:
    out = sales.groupby(keys)[["sales_kes", "profit_kes", "discounts_kes", "gross_sales_kes"]].sum()
    out["margin"] = out["profit_kes"] / out["sales_kes"]
    out["discount_pct"] = out["discounts_kes"] / out["gross_sales_kes"]
    return out


def yearly_vs_plan(sales: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "sales": sales.groupby("year")["sales_kes"].sum(),
        "target": targets.groupby("year")["target_sales_kes"].sum(),
    })
    out["variance"] = out["sales"] - out["target"]
    out["variance_pct"] = out["variance"] / out["target"]
    out["growth_pct"] = out["sales"].pct_change()
    return out


def monthly_vs_plan(sales: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "sales": sales.groupby("month")["sales_kes"].sum(),
        "target": targets.groupby("month")["target_sales_kes"].sum(),
    })
    out["variance"] = out["sales"] - out["target"]
    return out


def market_target(sales: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Mirror of [Target Sales (Market)]: segment-month plan x market's share a year earlier."""
    seg_mkt = sales.groupby(["month", "segment", "market"])["sales_kes"].sum().unstack(fill_value=0)
    share = seg_mkt.div(seg_mkt.sum(axis=1), axis=0)
    share.index = pd.MultiIndex.from_arrays(
        [share.index.get_level_values(0) + pd.DateOffset(years=1), share.index.get_level_values(1)]
    )
    plan = targets.set_index(["month", "segment"])["target_sales_kes"]
    alloc = share.mul(plan, axis=0).dropna(how="all")
    actual = seg_mkt.reindex(alloc.index)
    year = alloc.index.get_level_values(0).year
    target_y = alloc.groupby(year).sum().T
    actual_y = actual.groupby(year).sum().T
    target_y["Total"], actual_y["Total"] = target_y.sum(axis=1), actual_y.sum(axis=1)
    return (actual_y - target_y) / target_y


def main() -> str:
    d = load()
    s, t = d["sales"], d["targets"]
    lines = ["# Checkpoint values", "",
             "Values the report should show after **Refresh**, computed independently in pandas by "
             "`analysis/checkpoints.py`. KES figures are whole shillings.", ""]

    lines += ["## Whole period, no filters", "", "| Measure | Value |", "|---|---|"]
    for k, v in kpis(s).items():
        lines.append(f"| {k} | {v:.1%} |" if "%" in k or k == "Profit Margin" else f"| {k} | {v:,.0f} |")
    yv = yearly_vs_plan(s, t)
    lines += [f"| Target Sales | {yv['target'].sum():,.0f} |",
              f"| Variance to Target | {yv['variance'].sum():,.0f} |", ""]

    lines += ["## By year", "", "| Year | Total Sales | Sales Growth % | Target Sales | Variance to Target | Variance % |",
              "|---|---|---|---|---|---|"]
    for y, r in yv.iterrows():
        g = "" if pd.isna(r.growth_pct) else f"{r.growth_pct:.1%}"
        lines.append(f"| {y} | {r.sales:,.0f} | {g} | {r.target:,.0f} | {r.variance:,.0f} | {r.variance_pct:.1%} |")

    seg = by(s, "segment").sort_values("profit_kes", ascending=False)
    lines += ["", "## By segment", "", "| Segment | Total Sales | Total Profit | Profit Margin | Discount % | Share of all discounts |",
              "|---|---|---|---|---|---|"]
    for k, r in seg.iterrows():
        lines.append(f"| {k} | {r.sales_kes:,.0f} | {r.profit_kes:,.0f} | {r.margin:.1%} | {r.discount_pct:.1%} | "
                     f"{r.discounts_kes / seg.discounts_kes.sum():.1%} |")

    band = by(s, "discount_band").loc[BANDS]
    lines += ["", "## Profit margin by discount band", "", "| Segment | " + " | ".join(BANDS) + " |",
              "|---|" + "---|" * len(BANDS)]
    lines.append("| **All segments** | " + " | ".join(f"{band.loc[b, 'margin']:.1%}" for b in BANDS) + " |")
    sb = by(s, ["segment", "discount_band"])["margin"].unstack()[BANDS]
    for k, r in sb.iterrows():
        lines.append(f"| {k} | " + " | ".join(f"{r[b]:.1%}" for b in BANDS) + " |")

    prod = s.groupby(["product", "year"])["sales_kes"].sum().unstack()
    prod["vs2023"] = prod[2025] / prod[2023] - 1
    pm = by(s, "product")
    lines += ["", "## By product", "", "| Product | Sales 2023 | Sales 2025 | 2025 vs 2023 | Total Profit | Profit Margin |",
              "|---|---|---|---|---|---|"]
    for k, r in prod.sort_values("vs2023", ascending=False).iterrows():
        lines.append(f"| {k} | {r[2023]:,.0f} | {r[2025]:,.0f} | {r.vs2023:+.1%} | "
                     f"{pm.loc[k, 'profit_kes']:,.0f} | {pm.loc[k, 'margin']:.1%} |")

    mt = by(s, ["market_type", "year"])
    lines += ["", "## Domestic vs export", "", "| Market type | Year | Total Sales | Profit Margin |", "|---|---|---|---|"]
    for (k, y), r in mt.iterrows():
        lines.append(f"| {k} | {y} | {r.sales_kes:,.0f} | {r.margin:.1%} |")

    mv = market_target(s, t)
    lines += ["", "## Variance to Market Target % (segment plan allocated by prior-year share)", "",
              "| Market | 2024 | 2025 | Total (2024–2025) |", "|---|---|---|---|"]
    for k, r in mv.sort_values(2025).iterrows():
        lines.append(f"| {k} | {r[2024]:+.1%} | {r[2025]:+.1%} | {r['Total']:+.1%} |")

    mm = s.groupby(["year", s["month"].dt.month])["sales_kes"].sum()
    lines += ["", "## Strongest and weakest months (Total Sales)", "", "| Year | Strongest | Weakest |", "|---|---|---|"]
    for y in sorted(s["year"].unique()):
        m = mm.loc[y]
        lines.append(f"| {y} | {pd.Timestamp(2000, m.idxmax(), 1):%B} ({m.max():,.0f}) | "
                     f"{pd.Timestamp(2000, m.idxmin(), 1):%B} ({m.min():,.0f}) |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    text = main()
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "checkpoint_values.md").write_text(text, encoding="utf-8")
    print(text)
