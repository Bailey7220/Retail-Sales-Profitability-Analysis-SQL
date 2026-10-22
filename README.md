# Retail Sales & Profitability Analysis | SQL

A SQLite case study using synthetic retail data to investigate sales, profitability, returns, and regional revenue targets.

[Source data](data/) | [SQL scripts](sql/) | [Model and metric definitions](sql/01_database_schema.md)

> Portfolio project only. The dataset contains no real employer, company, customer, or transaction data. Results illustrate analytical methods, not real business impact.

## Business problem

Which products, categories, channels, and regions deserve closer attention when reviewing retail sales and profitability? This project combines order-line data with supporting tables, checks data quality, and uses SQL to produce decision-oriented summaries.

## Results at a glance

| Metric | Reported result |
|---|---:|
| Revenue after discounts | $25.91M |
| Gross profit | $6.61M |
| Gross margin | 25.50% |
| Distinct orders | 14,671 |
| Average order value | $1,766.23 |

These are the project's reported analysis results. Revenue is calculated after discounts, but revenue and gross profit are not adjusted for customer returns. Returns are analyzed separately. Gross profit is not net profit.

[Executive KPI query](sql/04_executive_kpi_summary.sql)

## Three findings and proposed next steps

### 1. Sales volume and margin tell different stories

Apparel generated $7.55M in revenue and $1.99M in gross profit. Electronics had the highest category gross margin at 27.35%, compared with Grocery at 22.20%.

Proposed next step: review Grocery pricing, discounts, supplier costs, and product mix rather than judging categories on revenue alone.

[Category profitability query](sql/06_category_profitability_analysis.sql)

### 2. Return risk deserves product-level investigation

Tools Item 2 generated $761.0K in revenue, with a 7.06% unit return rate and a 14.49% gross margin. Apparel had a 5.65% category return rate.

The product return-risk query screens products with at least $150,000 in revenue after discounts, then sorts them by unit return rate and revenue, both descending. This focuses the review on higher-revenue products rather than the entire catalog.

Proposed next step: investigate quality, fulfillment, packaging, and customer expectations for products combining substantial sales, elevated returns, and low margins. These patterns identify questions; they do not establish causes or quantify savings.

[Product return-risk query](sql/10_product_return_risk_analysis.sql)

### 3. Regional target attainment varies by month

Southeast achieved 107.9% of its October 2025 revenue target, while Northeast achieved 92.8% in December 2024. All five regions met or exceeded their targets in March 2026.

Regional target reporting includes month-region combinations with both recorded sales and a matching target. Missing sales-target matches are not separately reported.

Proposed next step: review monthly patterns to distinguish recurring underperformance from isolated misses.

[Regional target query](sql/09_regional_revenue_target_attainment.sql)

## Tools and methods

- SQLite and DB Browser for SQLite.
- Joins, CTEs, aggregations, window functions, and reusable views.
- Row-count checks, order-to-customer/product/store match checks, KPI calculations, and business interpretation.

## Data model

The synthetic dataset includes sales activity from 2024 through 2026. One row in `orders` represents one product line within an order, identified by `OrderID` and `OrderLineID` together.

| Table | Purpose |
|---|---|
| `orders` | Order-line sales, quantities, prices, and discounts |
| `customers` | Customer attributes and membership tiers |
| `products` | Product hierarchy, unit costs, and supplier details |
| `stores` | Store attributes and regional assignments |
| `returns` | Returned quantities, dates, and reasons |
| `sales_targets` | Monthly regional revenue targets |
| `date_reference` | Calendar reference attributes |

```text
customers -- CustomerID --> orders <-- ProductID -- products
stores    -- StoreID ----> orders
date_reference -- Date -> orders.OrderDate

returns -- OrderID + OrderLineID --> orders

sales_targets -- Month + Region --> monthly regional sales totals
```

This is a simplified relationship guide. Regional targets are compared with aggregated monthly regional sales, not joined directly to every order line.

## Calculation choices

- Revenue after discounts = quantity x selling price x (1 - discount percentage).
- COGS = quantity x product unit cost.
- Gross profit = revenue after discounts - COGS.
- Overall gross margin = total gross profit / total revenue, rather than an average of row-level margins.
- Unit return rate = returned units / units sold.
- The enriched view uses left joins to retain order lines and labels missing store information as `Unassigned Store`.
- The executive KPI query uses `NULLIF` to avoid division by zero in margin and average-order-value calculations.

[Enriched sales view](sql/03_create_orders_enriched_view.sql) | [Metric definitions](sql/01_database_schema.md)

## How to run

The following is a manual setup guide for DB Browser for SQLite. CSV import settings and inferred column types should be checked before relying on the outputs.

1. Download this repository and create a new SQLite database in DB Browser for SQLite.
2. Import each CSV in `data/` as a table. Use the first row as column names and retain the original headers. Name each table after its file without `.csv`: `customers`, `date_reference`, `orders`, `products`, `returns`, `sales_targets`, and `stores`.
3. Review the imported data: quantities, prices, costs, discounts, and targets should be numeric. Preserve identifier values and date strings; check for lost leading zeros or changed date formats. Save the imported changes.
4. Open and execute `sql/01_row_count_audit.sql`. Review the row counts for all seven tables. This script reports counts; it does not automatically assert that they are correct.
5. Run `sql/02_key_integrity_check.sql` and review the customer, product, and store match counts.
6. Run `sql/03_create_orders_enriched_view.sql` to create the shared analysis view. The script drops and recreates that view.
7. Run scripts `04` through `10` individually and inspect each result table.
8. Compare the executive KPI output with the rounded figures above. Investigate discrepancies rather than changing the data to match the summary.

For a reproducibility check, record the seven source-table counts, the three match-check counts, and the executive KPI outputs before rounding. Expected source-table counts and exact KPI outputs are not supplied here; the summary above is not a substitute for running the scripts.

## SQL workflow

| Script | Purpose |
|---|---|
| [01_row_count_audit.sql](sql/01_row_count_audit.sql) | Report imported row counts |
| [02_key_integrity_check.sql](sql/02_key_integrity_check.sql) | Check customer, product, and store references |
| [03_create_orders_enriched_view.sql](sql/03_create_orders_enriched_view.sql) | Centralize joins and sales calculations |
| [04_executive_kpi_summary.sql](sql/04_executive_kpi_summary.sql) | Summarize company-wide KPIs |
| [05_monthly_sales_profit_trend.sql](sql/05_monthly_sales_profit_trend.sql) | Analyze monthly results and running revenue |
| [06_category_profitability_analysis.sql](sql/06_category_profitability_analysis.sql) | Compare category profitability |
| [07_channel_performance_and_returns.sql](sql/07_channel_performance_and_returns.sql) | Compare channels and unit return rates |
| [08_return_reason_and_category_rate_analysis.sql](sql/08_return_reason_and_category_rate_analysis.sql) | Analyze return reasons and category rates |
| [09_regional_revenue_target_attainment.sql](sql/09_regional_revenue_target_attainment.sql) | Compare monthly regional revenue with targets |
| [10_product_return_risk_analysis.sql](sql/10_product_return_risk_analysis.sql) | Screen higher-revenue products for return-risk investigation |

## Data quality and limitations

- Validation scripts report table row counts and identify order lines without matching customer, product, or store records. They are targeted checks, not a complete data-quality test suite: duplicate keys, return-to-order matches, and target completeness are not checked by these two validation scripts.
- The documented validation results report that all order lines matched customer and product records.
- The documented results identify 485 order lines without a matching store record. They are retained in company-wide KPIs and labeled `Unassigned Store`, but excluded from regional target reporting. An unmatched reference can result from a missing store ID or an ID absent from the store table.
- Revenue and gross profit are not return-adjusted and do not represent net earnings after operating expenses.
- Product unit costs are taken from the product table; the calculation does not model historical cost changes.
- Findings are descriptive. Suggested actions have not been implemented or evaluated for business impact.
- The schema Markdown file documents the model; it is not an executable table-creation script.
