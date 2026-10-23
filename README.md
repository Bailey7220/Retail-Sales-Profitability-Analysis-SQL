# Retail Sales & Profitability Analysis | SQL

A SQLite portfolio case study using synthetic retail data to investigate sales, profitability, returns, and regional revenue targets.

> Data-quality notice: the raw dataset contains 249 negative-quantity order lines, all with missing StoreID. The figures and chart below reproduce the raw snapshot; they are not sales-only or corrected results. A separate sales-only workflow quarantines unresolved lines and their related returns without editing the source data. The maintainer reported a passing workflow on October 22, 2026; see the verification record for scope and evidence limits.

[Data-quality policy](DATA_QUALITY.md) | [Verification record](VERIFICATION.md) | [Source data](data/) | [SQL scripts](sql/) | [Model definitions](sql/01_database_schema.md) | [Raw reference outputs](results/)

Synthetic portfolio data only. No real employer, company, customer, or transaction data is included. Findings do not represent actual business impact.

## Business question

Which products, categories, channels, and regions deserve closer attention when reviewing retail sales and profitability, and how do unresolved source anomalies affect that analysis?

## Reproduce both layers

Use Python 3.12 with bundled SQLite. No pip dependencies are required.

```sh
python -m unittest discover -s tests -v
python scripts/analyze_layers.py
```

The runner preserves raw inputs, reproduces raw reference results, creates a separate sales-only population, runs strict checks, executes the same ten SQL scripts on both layers, and exports quarantine evidence and KPI differences. See DATA_QUALITY.md for the policy and output locations. The older scripts/reproduce.py deliberately remains strict and rejects the known-dirty raw snapshot.

## Historical raw-snapshot results

The diagnostic run matched these existing reference figures. Matching them establishes reproducibility, not source-data correctness.

| Metric | Raw-snapshot value |
|---|---:|
| Revenue after discounts | $25,912,424.37 |
| Gross profit | $6,607,883.84 |
| Gross margin | 25.50% |
| Distinct orders | 14,671 |
| Order lines | 44,290 |
| Average order value | $1,766.23 |

Revenue and gross profit are not adjusted for returns. Gross profit is not net profit. Sales-only figures must be calculated and reviewed before publication; they are not assumed to equal this table.

### Historical raw category chart

![Raw-snapshot gross margin by category](images/category_gross_margin.svg)

[Raw category reference](results/category_profitability.csv) | [Category query](sql/06_category_profitability_analysis.sql)

## Model and calculation choices

- One order row is one product line, keyed by OrderID and OrderLineID together. Returns match using both identifiers.
- Supporting tables: customers, products, stores, date_reference, and monthly regional sales_targets.
- Revenue after discounts = quantity x price x (1 - discount percentage).
- COGS = quantity x product unit cost; historical cost changes are not modeled.
- Gross profit = revenue after discounts - COGS. Overall margin uses total profit divided by total revenue.
- Unit return rate = returned units divided by sold units within the explicitly labeled population.
- The enriched view uses left joins and labels missing stores as unassigned.
- Regional targets are compared at month-region grain, not transaction grain.

## Scope and limitations

Raw order dates run from January 1, 2024 through July 28, 2026. July is incomplete. Regional reporting includes only matched sales/target combinations and excludes unassigned stores; it is not a complete target-coverage report.

The raw snapshot has 44,290 order lines and 2,657 returns. The selected sales-only policy excludes 249 order lines and their 23 linked returns, leaving 44,041 lines and 2,634 returns. The remaining 236 positive-quantity lines with missing stores stay in company-wide analysis.

The original generator and intended meaning of negative quantities are unverified. Exclusion is a transparent eligibility decision, not recovered truth. No source quantity is flipped, no return is capped, and no store is guessed. Existing product-risk and profitability conclusions must be reassessed against the labeled sales-only outputs before being presented as current findings.

Tools demonstrated include SQLite, joins, CTEs, aggregations, window functions, reusable views, Python standard-library ingestion, automated checks, and an auditable raw/analytical/quarantine separation. The chart is a static SVG, not an interactive dashboard.

## Licensing

Original code and written documentation are available under the [MIT License](LICENSE), subject to the [licensing scope](LICENSING.md). Source data, reference/output datasets, images, and third-party material are not relicensed by that grant.
