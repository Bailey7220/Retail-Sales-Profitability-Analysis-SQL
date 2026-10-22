#!/usr/bin/env python3
"""Collect failure evidence without changing validation expectations or source data."""
import csv
import hashlib
import json
import sqlite3
from pathlib import Path
import reproduce as r

EXCESS_SQL = """
WITH totals AS (
    SELECT OrderID, OrderLineID, COUNT(*) AS return_records,
           SUM(QuantityReturned) AS returned_units
    FROM returns GROUP BY OrderID, OrderLineID
)
SELECT o.OrderID, o.OrderLineID, o.ProductID, o.StoreID,
       o.Quantity AS sold_units, t.return_records, t.returned_units,
       t.returned_units - o.Quantity AS excess_units
FROM orders o JOIN totals t
  ON o.OrderID=t.OrderID AND o.OrderLineID=t.OrderLineID
WHERE t.returned_units > o.Quantity
ORDER BY o.OrderID, o.OrderLineID
"""
DETAIL_SQL = """
SELECT r.* FROM returns r
JOIN (SELECT OrderID, OrderLineID FROM (""" + EXCESS_SQL + """)) a
  ON r.OrderID=a.OrderID AND r.OrderLineID=a.OrderLineID
ORDER BY r.OrderID, r.OrderLineID
"""
CONTEXT_SQL = """
SELECT o.* FROM orders o
WHERE o.OrderID IN (SELECT OrderID FROM (""" + EXCESS_SQL + """))
ORDER BY o.OrderID, o.OrderLineID
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
              'note': 'Outputs are investigation material, not validated results. No inputs were changed.'}
    try:
        paths = list((root / 'data').glob('*.csv')) + list((root / 'sql').glob('*.sql'))
        report['sha256'] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        with sqlite3.connect(':memory:') as connection:
            r.load(connection, root / 'data')
            try:
                r.validate(connection, r.COUNTS)
            except Exception as error:
                report['errors'].append({'stage': 'strict_validation', 'error': str(error)})
            for name, sql in [('excess_return_lines', EXCESS_SQL),
                              ('affected_return_records', DETAIL_SQL),
                              ('affected_order_context', CONTEXT_SQL)]:
                headers, rows = export_query(connection, sql, output / (name + '.csv'))
                report[name + '_count'] = len(rows)
                report[name + '_rows'] = [dict(zip(headers, row)) for row in rows]
            report['interpretation_boundary'] = (
                'Order context can identify possible wrong-line associations, but a quantity match '
                'on another line does not prove a generator defect or justify relinking records. '
                'Original generator code and intent remain unverified.'
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
