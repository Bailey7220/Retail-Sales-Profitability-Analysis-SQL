# Retail-Sales-Profitability-Analysis-SQL

## Business Problem:
A simulated multi-channel retailer needs to understand which products,
regions, customer segments, and sales channels are driving profitable
growth. The analysis will evaluate sales, gross profit, gross margin,
returns, and customer purchasing patterns to identify operational and
financial improvement opportunities.

## Tools Used:
- SQLite / SQLiteOnline
- SQL
- GitHub
- Optional: Excel and Power BI for visualization

## Dataset:
This project uses a synthetic multi-channel retail dataset created for
portfolio and educational purposes. The dataset contains transactional
order-line data and supporting dimension tables for customers, products,
stores, returns, monthly sales targets, and dates.

The dataset covers sales activity from 2024 through 2026 and does not
contain real company, customer, or employer data.

## Data Grain:
The orders table is the primary fact table. One row represents one product
line within a customer order, identified by the combination of OrderID and
OrderLineID.



!!!!!!!!!!!

Sales displayed a strong year-end seasonal pattern, with December 2025 producing the highest observed monthly net revenue ($1.39M) and gross profit ($355.2K). Gross margin remained stable at approximately 25%, suggesting that revenue growth was not driven by substantial margin erosion.


Apparel was the largest contributor to both net revenue ($7.55M) and gross profit ($1.99M). Electronics generated the highest gross margin at 27.35%, while Grocery produced the weakest margin at 22.20%, indicating an opportunity to review pricing, promotion, product mix, or supplier costs within lower-margin categories.


In-Club was the largest sales channel, generating $14.35M in net revenue and $3.67M in gross profit. Curbside had the highest unit return rate at 5.83%, compared with 5.41% for In-Club and 5.21% for Online, indicating a potential opportunity to investigate order accuracy, product substitution, pickup quality, or customer-expectation issues in the curbside process.


Apparel had the highest true unit return rate at 5.65% and the largest return volume, with “Better Price Found” and “Damaged in Shipping” among the leading recorded reasons. The analysis recommends reviewing Apparel pricing/promotion competitiveness and fulfillment packaging or handling before expanding intervention to other categories.


Monthly revenue performance varied materially by region. Southeast exceeded target by $13.7K in October 2025, reaching 107.9% of plan, while Northeast missed target by $19.9K in December 2024, reaching 92.8%. March 2026 was a particularly strong period: all five regions met or exceeded their revenue targets.


Tools Item 2 generated $761.0K in net revenue but had a 7.06% unit return rate and only a 14.49% gross margin. Because it combines substantial sales volume, elevated returns, and low profitability, it is a high-priority candidate for product-quality, pricing, supplier-cost, packaging, or customer-expectation review.
