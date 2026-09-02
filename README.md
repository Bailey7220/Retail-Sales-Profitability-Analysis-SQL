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
