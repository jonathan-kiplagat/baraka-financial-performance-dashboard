# Measure library

All measures live in the `Key Measures` table. They are generated from (and identical to) `BarakaFinance.SemanticModel/definition/tables/Key Measures.tmdl`.

## Sales & profit

### Total Sales

What customers paid after discounts (KES). Format: `#,0`.

```dax
Total Sales = SUM ( Sales[sales_kes] )
```

### Gross Sales

Units x sale price, before discounts (KES). Format: `#,0`.

```dax
Gross Sales = SUM ( Sales[gross_sales_kes] )
```

## Discounts

### Total Discounts

Value of discounts given (KES). Format: `#,0`.

```dax
Total Discounts = SUM ( Sales[discounts_kes] )
```

### Discount %

Discounts as a share of gross sales. Format: `0.0%`.

```dax
Discount % = DIVIDE ( [Total Discounts], [Gross Sales] )
```

### Share of All Discounts

This item's discounts as a share of all discounts in the current selection. Format: `0.0%`.

```dax
Share of All Discounts = DIVIDE ( [Total Discounts], CALCULATE ( [Total Discounts], ALLSELECTED () ) )
```

## Sales & profit

### Total COGS

Cost of goods sold (KES). Format: `#,0`.

```dax
Total COGS = SUM ( Sales[cogs_kes] )
```

### Total Profit

Sales minus COGS (KES). Format: `#,0`.

```dax
Total Profit = SUM ( Sales[profit_kes] )
```

### Profit Margin

Profit as a share of sales. Format: `0.0%`.

```dax
Profit Margin = DIVIDE ( [Total Profit], [Total Sales] )
```

### Units Sold

Units sold. Format: `#,0`.

```dax
Units Sold = SUM ( Sales[units_sold] )
```

## Time intelligence

### Sales Last Year

Total Sales for the same period one year earlier. Format: `#,0`.

```dax
Sales Last Year = CALCULATE ( [Total Sales], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )
```

### Sales Growth %

Change in Total Sales versus the same period last year (within a single year). Format: `0.0%`.

```dax
Sales Growth % =
-- Only meaningful within one year: across several years the comparison overlaps.
VAR SalesLY = [Sales Last Year]
RETURN
    IF (
        HASONEVALUE ( 'Date'[Year] ) && NOT ISBLANK ( SalesLY ),
        DIVIDE ( [Total Sales] - SalesLY, SalesLY )
    )
```

### Profit Last Year

Total Profit for the same period one year earlier. Format: `#,0`.

```dax
Profit Last Year = CALCULATE ( [Total Profit], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )
```

### Sales YTD

Total Sales from 1 January to the end of the current period. Format: `#,0`.

```dax
Sales YTD = TOTALYTD ( [Total Sales], 'Date'[Date] )
```

### Sales vs 2023 %

Change versus calendar 2023 (use with a single year selected). Format: `0.0%`.

```dax
Sales vs 2023 % =
VAR Base2023 =
    CALCULATE ( [Total Sales], REMOVEFILTERS ( 'Date' ), 'Date'[Year] = 2023 )
RETURN
    IF ( HASONEVALUE ( 'Date'[Year] ), DIVIDE ( [Total Sales] - Base2023, Base2023 ) )
```

## Plan

### Target Sales

Planned sales from the monthly sales plan (KES). Blank when a market, product or discount band is filtered. Format: `#,0`.

```dax
Target Sales =
-- The plan is set by segment and month only, so it is not defined for a
-- market, product or discount band. Return blank rather than a misleading total.
IF (
    ISCROSSFILTERED ( Markets ) || ISCROSSFILTERED ( Products ) || ISCROSSFILTERED ( 'Discount Band' ),
    BLANK (),
    SUM ( Targets[target_sales_kes] )
)
```

### Variance to Target

Total Sales minus Target Sales (KES). Positive means ahead of plan. Format: `#,0`.

```dax
Variance to Target =
VAR Plan = [Target Sales]
RETURN
    IF ( NOT ISBLANK ( Plan ), [Total Sales] - Plan )
```

### Variance to Target %

Variance to Target as a share of Target Sales. Format: `0.0%`.

```dax
Variance to Target % = DIVIDE ( [Variance to Target], [Target Sales] )
```

### Target Sales (Market)

Segment target allocated to markets by prior-year share of segment sales (from 2024). Format: `#,0`.

```dax
Target Sales (Market) =
-- The plan is set by segment and month. Allocate each segment-month target to
-- markets by the market's share of that segment's sales a year earlier.
SUMX (
    CROSSJOIN ( VALUES ( Segment[Segment] ), VALUES ( 'Date'[Month Start] ) ),
    VAR MonthLY = EDATE ( 'Date'[Month Start], -12 )
    VAR SegmentTarget = CALCULATE ( SUM ( Targets[target_sales_kes] ) )
    VAR MarketSalesLY =
        CALCULATE ( [Total Sales], REMOVEFILTERS ( 'Date' ), 'Date'[Month Start] = MonthLY )
    VAR SegmentSalesLY =
        CALCULATE (
            [Total Sales],
            REMOVEFILTERS ( 'Date' ),
            'Date'[Month Start] = MonthLY,
            REMOVEFILTERS ( Markets )
        )
    RETURN
        SegmentTarget * DIVIDE ( MarketSalesLY, SegmentSalesLY )
)
```

### Variance to Market Target %

Total Sales versus the market-allocated target. Format: `0.0%`.

```dax
Variance to Market Target % =
VAR Plan = [Target Sales (Market)]
RETURN
    IF ( NOT ISBLANK ( Plan ), DIVIDE ( [Total Sales] - Plan, Plan ) )
```
