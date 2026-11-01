# Data

Four CSV files from Baraka Manufacturing's finance system, January 2023 – December 2025. All money is in whole Kenyan shillings (KES). The data is synthetic (Baraka is fictional), generated to follow the layout of Microsoft's Financial Sample workbook, from the DSEAfrica Data Lab project *Financial Performance Dashboard in Power BI*. The files are unmodified (SHA-256 below).

| File | Rows | One row is | SHA-256 |
|---|---|---|---|
| `baraka-sales.csv` | 6,264 | Sales of one product to one segment in one market in one month, at one discount band | `fbafaf1c…c436a558a5` |
| `baraka-products.csv` | 6 | One product | `59ea1b99…f1bf27a4` |
| `baraka-markets.csv` | 7 | One market city | `d5a2a077…4129519a` |
| `baraka-targets.csv` | 180 | Planned sales for one segment in one month | `4fabcdf6…fa4149f0` |

## How the money columns relate

```
gross_sales_kes = units_sold × sale_price_kes
discounts_kes   = gross_sales_kes × band rate   (None 0%, Low 3%, Medium 7%, High 15%; rounded to the shilling)
sales_kes       = gross_sales_kes − discounts_kes
profit_kes      = sales_kes − cogs_kes          (negative = loss)
```

Checked on row 1 (Supermarkets, Nairobi, Cooking Oil, January 2023, Medium band): 849 × 347 = **294,603** gross; 7% discount = **20,622**; sales = **273,981**; COGS = 849 × 228 = **193,572**; profit = **80,409**. The tests check these identities on all 6,264 rows.

COGS per unit depends on product, year (it rises each year) and whether the market is domestic or export (exports cost about 8% more).

> pandas tip: read the sales file with `keep_default_na=False`. Otherwise pandas turns the discount band **"None"** into a missing value. Power BI reads it correctly as text.
