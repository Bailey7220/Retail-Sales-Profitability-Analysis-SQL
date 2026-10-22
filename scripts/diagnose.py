#!/usr/bin/env python3
"""Collect failure evidence without changing validation expectations or source data."""
import csv
import hashlib
import json
import sqlite3
from pathlib import Path
import reproduce as r

QUANTITY_PROFILE_SQL = """
SELECT COUNT(*) AS total_order_lines,
 COALESCE(SUM(CASE WHEN Quantity<0 THEN 1 ELSE 0 END),0) AS negative_quantity_lines,
 COALESCE(SUM(CASE WHEN Quantity=0 THEN 1 ELSE 0 END),0) AS zero_quantity_lines,
 COALESCE(SUM(CASE WHEN Quantity IS NULL THEN 1 ELSE 0 END),0) AS missing_quantity_lines,
 COALESCE(SUM(CASE WHEN StoreID IS NULL THEN 1 ELSE 0 END),0) AS missing_store_lines,
 COALESCE(SUM(CASE WHEN Quantity<0 AND StoreID IS NULL THEN 1 ELSE 0 END),0) AS negative_quantity_missing_store_lines,
 COALESCE(SUM(CASE WHEN Quantity<0 AND StoreID IS NOT NULL THEN 1 ELSE 0 END),0) AS negative_quantity_known_store_lines,
 COALESCE(SUM(CASE WHEN Quantity>0 AND StoreID IS NULL THEN 1 ELSE 0 END),0) AS positive_quantity_missing_store_lines
FROM orders
"""
INVALID_SQL = """
SELECT o.*,
 CASE WHEN Quantity IS NULL THEN 'missing' WHEN Quantity=0 THEN 'zero' ELSE 'negative' END AS quantity_issue
FROM orders o WHERE Quantity IS NULL OR Quantity<=0
ORDER BY OrderID,OrderLineID
"""
EXCESS_SQL = """
WITH totals AS (
 SELECT OrderID,OrderLineID,COUNT(*) AS return_records,SUM(QuantityReturned) AS returned_units
 FROM returns GROUP BY OrderID,OrderLineID
)
SELECT o.OrderID,o.OrderLineID,o.ProductID,o.StoreID,o.Quantity AS sold_units,
 t.return_records,t.returned_units,t.returned_units-o.Quantity AS excess_units
FROM orders o JOIN totals t ON o.OrderID=t.OrderID AND o.OrderLineID=t.OrderLineID
WHERE o.Quantity>0 AND t.returned_units>o.Quantity
ORDER BY o.OrderID,o.OrderLineID
"""
INVALID_RETURN_SQL = """
SELECT o.OrderID,o.OrderLineID,o.Quantity AS raw_order_quantity,o.StoreID,
 COUNT(*) AS return_records,SUM(r.QuantityReturned) AS returned_units
FROM orders o JOIN returns r ON o.OrderID=r.OrderID AND o.OrderLineID=r.OrderLineID
WHERE o.Quantity IS NULL OR o.Quantity<=0
GROUP BY o.OrderID,o.OrderLineID,o.Quantity,o.StoreID
ORDER BY o.OrderID,o.OrderLineID
"""


def export_query(connection, sql, destination):
    cursor = connection.execute(sql)
    headers = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    with destination.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)
    return headers, rows


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / 'build' / 'diagnostics'
    output.mkdir(parents=True, exist_ok=True)
    report = {'diagnostic_only': True, 'errors': [], 'reference_comparisons': {},
              'note': 'Raw quantities are unchanged. Matching references does not certify data quality.'}
    try:
        paths = list((root / 'data').glob('*.csv')) + list((root / 'sql').glob('*.sql'))
        report['sha256'] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        with sqlite3.connect(':memory:') as connection:
            r.load(connection, root / 'data')
            cursor = connection.execute(QUANTITY_PROFILE_SQL)
            report['quantity_profile'] = dict(zip([c[0] for c in cursor.description], cursor.fetchone()))
            try:
                r.validate(connection, r.COUNTS)
            except Exception as error:
                report['errors'].append({'stage': 'strict_validation', 'error': str(error)})
            for name, sql in [('invalid_order_quantities', INVALID_SQL),
                              ('excess_returns_on_positive_sales', EXCESS_SQL),
                              ('returns_against_invalid_order_quantities', INVALID_RETURN_SQL)]:
                headers, rows = export_query(connection, sql, output / (name + '.csv'))
                report[name + '_count'] = len(rows)
                report[name + '_rows'] = [dict(zip(headers, row)) for row in rows[:30]]
                report[name + '_inline_truncated'] = len(rows)>30
            report['interpretation_boundary'] = (
                'Negative quantities may be reversals or data anomalies; source intent is unverified. '
                'No ABS transformation, deletion, relinking, or exclusion has been applied. '
                'Return limits are evaluated only against positive sales; invalid sales still fail validation.'
            )
            for filename in r.SCRIPTS:
                try:
                    text = (root / 'sql' / filename).read_text(encoding='utf-8-sig')
                    for number, (headers, rows) in enumerate(r.execute_script(connection, text), 1):
                        destination = output / f'{Path(filename).stem}_{number}.csv'
                        with destination.open('w', newline='', encoding='utf-8') as stream:
                            writer = csv.writer(stream)
                            writer.writerow(headers)
                            writer.writerows(rows)
                except Exception as error:
                    report['errors'].append({'stage': filename, 'error': str(error)})
            for generated, baseline, key in [('04_executive_kpi_summary_1.csv', 'executive_kpis.csv', None),
                                              ('06_category_profitability_analysis_1.csv', 'category_profitability.csv', 'Category')]:
                try:
                    with (output / generated).open(newline='', encoding='utf-8') as stream:
                        rows = list(csv.DictReader(stream))
                    r.compare(rows, root / 'results' / baseline, key)
                    report['reference_comparisons'][baseline] = 'matched existing reference columns'
                except Exception as error:
                    report['reference_comparisons'][baseline] = 'failed'
                    report['errors'].append({'stage': baseline, 'error': str(error)})
    except Exception as error:
        report['errors'].append({'stage': 'diagnostic_collection', 'error': str(error)})
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    print('Diagnostic collection complete; the original validation failure is not waived.')


if __name__ == '__main__':
    main()
