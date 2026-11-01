# Report guide

The report has three pages, 1280 × 720, with every value coming from a measure in `Key Measures`. This guide lists each visual so you can check it, or rebuild it if Power BI asks you to fix one.

## Page 1 — Overview

| Visual | Type | Fields |
|---|---|---|
| Year, Segment, Market | Slicers (dropdown) | `Date[Year]`, `Segment[Segment]`, `Markets[market]` |
| Total sales (KES) | Card | `[Total Sales]` |
| Total profit (KES) | Card | `[Total Profit]` |
| Profit margin | Card | `[Profit Margin]` |
| Variance to target (KES) | Card | `[Variance to Target]`: blank when a market is selected, because the plan is set by segment |
| Monthly sales and profit, with sales last year | Line chart | X: `Date[Month Start]`; Y: `[Total Sales]`, `[Sales Last Year]`, `[Total Profit]` |
| Sales by calendar month and year | Clustered column | X: `Date[Month]`; legend: `Date[Year]`; Y: `[Total Sales]` |
| Sales against the sales plan by year | Clustered column | X: `Date[Year]`; Y: `[Total Sales]`, `[Target Sales]` |

## Page 2 — Profit drivers

| Visual | Type | Fields |
|---|---|---|
| Year, Market type | Slicers | `Date[Year]`, `Markets[market_type]` |
| Total profit by segment | Clustered bar | Y axis: `Segment[Segment]`; X: `[Total Profit]`, sorted descending |
| Profit margin by segment | Clustered column | `Segment[Segment]`, `[Profit Margin]` |
| Profit margin by discount band | Clustered column | `Discount Band[Discount Band]`, `[Profit Margin]` |
| Profit margin by segment and discount band | Matrix | Rows: `Segment[Segment]`; columns: `Discount Band[Discount Band]`; values: `[Profit Margin]` |
| Products | Table | `Products[product]`, `[Total Sales]`, `[Total Profit]`, `[Profit Margin]`, `[Sales Growth %]`, `[Discount %]` |
| Where the discounts go | Clustered bar | `Segment[Segment]`, `[Total Discounts]` |

## Page 3 — Markets and plan

| Visual | Type | Fields |
|---|---|---|
| Year, Segment | Slicers | `Date[Year]`, `Segment[Segment]` |
| Sales and profit by market | Clustered column | `Markets[market]`; `[Total Sales]`, `[Total Profit]` |
| Sales: domestic vs export | Donut | `Markets[market_type]`, `[Total Sales]` |
| Profit margin: domestic vs export | Clustered column | `Markets[market_type]`, `[Profit Margin]` |
| Actual sales against target by month | Line and clustered column | X: `Date[Month Start]`; columns: `[Total Sales]`; line: `[Target Sales]` |
| Variance to target by market | Matrix | Rows: `Markets[market]`; columns: `Date[Year]`; values: `[Variance to Market Target %]` |

## Optional finishing touches

These are worth adding in Power BI Desktop after the first open:

- **Conditional formatting** on the two matrices: Format → Cell elements → Background colour, diverging, red below 0 and green above, for *Variance to Market Target %*, and a sequential scale for *Profit Margin*.
- **Card subtitles:** under each card, add `[Sales Growth %]` or `[Variance to Target %]` with the new card visual's reference labels.
