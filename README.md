# Retail Sales & Profitability Analysis | SQL

## Business Problem

A synthetic multi-channel retailer needs to understand which products,
regions, membership tiers, and sales channels are driving profitable growth.
This analysis evaluates sales, gross profit, gross margin, returns, regional
target attainment, and customer purchasing patterns to identify operational
and financial improvement opportunities.

## Tools Used

- SQLite
- DB Browser for SQLite
- SQL
- GitHub
- Excel and Power BI for supporting analysis and visualization

## Dataset

This project uses a synthetic multi-channel retail dataset created for
portfolio and educational purposes. The dataset contains transactional
order-line data and supporting dimension tables for customers, products,
stores, returns, monthly sales targets, and dates.

The dataset covers sales activity from 2024 through 2026 and does not contain
real company, customer, or employer data.

## Data Model

The analysis uses seven related tables:

| Table | Description |
|---|---|
| `orders` | Transactional order-line sales data |
| `customers` | Customer name, membership tier, signup date, and state |
| `products` | Product hierarchy, unit cost, unit price, and supplier details |
| `stores` | Store location, region, type, and opening date |
| `returns` | Returned order-line quantities, dates, and return reasons |
| `sales_targets` | Monthly revenue targets by region |
| `date_reference` | Calendar reference table for time-based analysis |

## Data Grain

The `orders` table is the primary fact table. One row represents one product
line within a customer order, identified by the combination of `OrderID` and
`OrderLineID`.

## SQL Workflow

The `sql` folder contains one schema-documentation file and ten executable
SQL scripts.

### Documentation

- `01_database_schema.md` — Documents the database tables, relationships,
  business definitions, and data limitations

### SQL Scripts

1. `01_row_count_audit.sql` — Validates row counts after CSV import
2. `02_key_integrity_check.sql` — Checks customer, product, and store joins
3. `03_create_orders_enriched_view.sql` — Creates a reusable enriched view
   with revenue, discount, COGS, and gross-profit calculations
4. `04_executive_kpi_summary.sql` — Calculates executive-level sales and
   profitability KPIs
5. `05_monthly_sales_profit_trend.sql` — Analyzes monthly performance and
   running net revenue
6. `06_category_profitability_analysis.sql` — Compares category revenue,
   gross profit, and gross margin
7. `07_channel_performance_and_returns.sql` — Compares channel sales,
   profitability, and unit return rates
8. `08_return_reason_and_category_rate_analysis.sql` — Identifies return
   drivers and calculates true category return rates
9. `09_regional_revenue_target_attainment.sql` — Compares regional revenue
   against monthly targets
10. `10_product_return_risk_analysis.sql` — Identifies high-revenue products
    with elevated return risk

## Key Findings & Recommendations

### 1. Strong overall sales and profitability

The retailer generated $25.91M in net revenue and $6.61M in gross profit
across 14,671 orders, with a 25.50% gross margin and a $1,766.23 average
order value.

**Recommendation:** Continue monitoring net revenue, gross margin, average
order value, and discount activity as core executive KPIs. Review discounting
when revenue growth does not translate into proportional gross-profit growth.

### 2. Apparel drives sales; Electronics leads on margin

Apparel was the largest category, generating $7.55M in net revenue and
$1.99M in gross profit. Electronics produced the highest gross margin at
27.35%, while Grocery had the lowest at 22.20%.

**Recommendation:** Protect high-margin Electronics performance while
reviewing Grocery pricing, promotions, supplier costs, and product mix for
margin improvement opportunities.

### 3. Year-end seasonality drives the strongest monthly performance

December 2025 produced the highest observed monthly net revenue at $1.39M
and the highest gross profit at $355.2K. November and December were among
the strongest sales months in both 2024 and 2025.

**Recommendation:** Use demand forecasts, inventory planning, staffing, and
promotional calendars to prepare for elevated year-end volume while protecting
margin during peak periods.

### 4. Curbside has the highest channel return rate

In-Club was the largest channel, generating $14.35M in net revenue. Curbside
had the highest unit return rate at 5.83%, compared with 5.41% for In-Club
and 5.21% for Online.

**Recommendation:** Review curbside order accuracy, product substitutions,
pickup quality, and customer communication. The difference is modest, so this
should be treated as an investigation priority rather than proof of a process
failure.

### 5. Apparel and select products present return-risk opportunities

Apparel had the highest category return rate at 5.65% and the largest return
volume. Tools Item 2 generated $761.0K in net revenue but had a 7.06% return
rate and a 14.49% gross margin, making it a high-priority product for review.

**Recommendation:** Investigate high-return products by supplier, fulfillment
process, packaging, product quality, pricing, and customer-expectation factors.
Prioritize products with both high revenue and low margin because returns may
have an outsized profit impact.

### 6. Regional target performance varies by month

Regional performance varied by month. For example, Southeast exceeded its
October 2025 revenue target by $13.7K, achieving 107.9% of plan, while
Northeast missed its December 2024 target by $19.9K, achieving 92.8%.
In March 2026, all five regions met or exceeded their revenue targets.

**Recommendation:** Use monthly regional variance reporting to focus reviews
on persistent underperformance, replicate practices from regions that
consistently exceed target, and distinguish isolated misses from recurring
performance patterns.

## Data Quality Notes

- The dataset is synthetic and was created for portfolio and educational use.
  It does not contain real employer, customer, or company data.
- All order lines matched to valid customer and product records.
- 485 order lines did not have a store assignment. These records are retained
  in company-wide KPIs and labeled `Unassigned Store` in the enriched analysis
  view. They are excluded from regional target-attainment reporting because
  they cannot be assigned to a regional target.
- Revenue, discount, COGS, gross profit, and margin calculations are defined
  in `sql/03_create_orders_enriched_view.sql`.
