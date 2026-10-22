#!/usr/bin/env python3
"""Load the seven CSVs, validate them, and execute the repository SQL verbatim."""
import csv
import hashlib
import json
import math
import platform
import re
import sqlite3
import tempfile
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTS = dict(customers=600, date_reference=1096, orders=44290, products=160,
              returns=2657, sales_targets=155, stores=38)
REQUIRED = {
    'customers': 'CustomerID FirstName LastName MembershipTier State SignupDate',
    'date_reference': 'Date',
    'orders': 'OrderID OrderLineID OrderDate CustomerID ProductID StoreID Channel ShipStateRaw Quantity UnitPrice DiscountPct',
    'products': 'ProductID ProductName Category SubCategory Supplier UnitCost',
    'returns': 'OrderID OrderLineID QuantityReturned ReturnReason',
    'sales_targets': 'Month Region RevenueTarget',
    'stores': 'StoreID StoreName City State Region StoreType',
}
NUMBERS = {'Quantity', 'UnitPrice', 'DiscountPct', 'UnitCost', 'QuantityReturned', 'RevenueTarget'}
DATES = {'Date', 'OrderDate', 'ReturnDate', 'SignupDate', 'OpenDate', 'Month'}
KEYS = {'customers': ['CustomerID'], 'products': ['ProductID'], 'stores': ['StoreID'],
        'orders': ['OrderID', 'OrderLineID'], 'date_reference': ['Date'],
        'sales_targets': ['Month', 'Region']}
SCRIPTS = ['01_row_count_audit.sql', '02_key_integrity_check.sql',
           '03_create_orders_enriched_view.sql', '04_executive_kpi_summary.sql',
           '05_monthly_sales_profit_trend.sql', '06_category_profitability_analysis.sql',
           '07_channel_performance_and_returns.sql', '08_return_reason_and_category_rate_analysis.sql',
           '09_regional_revenue_target_attainment.sql', '10_product_return_risk_analysis.sql']


def quote(name):
    return '"' + name.replace('"', '""') + '"'


def load(connection, folder):
    for table, required in REQUIRED.items():
        path = Path(folder) / (table + '.csv')
        with path.open(newline='', encoding='utf-8-sig') as stream:
            reader = csv.reader(stream, strict=True)
            headers = next(reader)
            if not headers or any(not h for h in headers) or len({h.casefold() for h in headers}) != len(headers):
                raise ValueError(f'{table}: empty or duplicate column name')
            if not set(required.split()) <= set(headers):
                raise ValueError(f'{table}: missing required columns')
            columns = ', '.join(quote(h) + (' REAL' if h in NUMBERS else ' TEXT') for h in headers)
            connection.execute(f'CREATE TABLE {quote(table)} ({columns})')
            insert = f'INSERT INTO {quote(table)} VALUES ({", ".join("?" for _ in headers)})'
            for line, row in enumerate(reader, 2):
                if len(row) != len(headers):
                    raise ValueError(f'{table}:{line}: wrong field count')
                values = []
                for header, value in zip(headers, row):
                    if value == '':
                        values.append(None)
                    elif header in NUMBERS:
                        number = float(value)
                        if not math.isfinite(number):
                            raise ValueError(f'{table}:{line}: nonfinite {header}')
                        values.append(number)
                    elif header == 'StoreID':
                        # Normalize only an all-zero decimal suffix; preserve leading zeros.
                        values.append(re.sub(r'^([0-9]+)\.0+$', r'\1', value))
                    elif header in DATES:
                        if date.fromisoformat(value).isoformat() != value:
                            raise ValueError(f'{table}:{line}: noncanonical date')
                        values.append(value)
                    else:
                        values.append(value)
                connection.execute(insert, values)
    connection.commit()


def validate(connection, expected=None, missing_stores=485):
    checks = {}
    def check(name, sql, wanted=0):
        actual = connection.execute(sql).fetchone()[0]
        checks[name] = {'actual': actual, 'expected': wanted}
        if actual != wanted:
            raise ValueError(f'{name}: expected {wanted}, found {actual}')
    if expected is not None:
        for table, count in expected.items():
            check('rows_' + table, f'SELECT COUNT(*) FROM {quote(table)}', count)
    for table, keys in KEYS.items():
        nulls = ' OR '.join(quote(k) + " IS NULL OR trim(" + quote(k) + ") = ''" for k in keys)
        check('null_key_' + table, f'SELECT COUNT(*) FROM {quote(table)} WHERE {nulls}')
        grouped = ', '.join(quote(k) for k in keys)
        check('duplicate_key_' + table, f'SELECT COUNT(*) FROM (SELECT 1 FROM {quote(table)} GROUP BY {grouped} HAVING COUNT(*) > 1)')
    for column, target in [('CustomerID', 'customers'), ('ProductID', 'products')]:
        check('unmatched_' + column, f'SELECT COUNT(*) FROM orders o LEFT JOIN {target} d ON o.{column}=d.{column} WHERE d.{column} IS NULL')
    check('missing_store_ids', 'SELECT COUNT(*) FROM orders WHERE StoreID IS NULL', missing_stores)
    check('unknown_nonnull_stores', 'SELECT COUNT(*) FROM orders o LEFT JOIN stores s ON o.StoreID=s.StoreID WHERE o.StoreID IS NOT NULL AND s.StoreID IS NULL')
    check('unmatched_calendar_dates', 'SELECT COUNT(*) FROM orders o LEFT JOIN date_reference d ON o.OrderDate=d.Date WHERE d.Date IS NULL')
    check('unmatched_return_lines', 'SELECT COUNT(*) FROM returns r LEFT JOIN orders o ON r.OrderID=o.OrderID AND r.OrderLineID=o.OrderLineID WHERE o.OrderID IS NULL')
    check('excess_return_units', 'SELECT COUNT(*) FROM (SELECT r.OrderID,r.OrderLineID FROM returns r JOIN orders o ON r.OrderID=o.OrderID AND r.OrderLineID=o.OrderLineID GROUP BY r.OrderID,r.OrderLineID,o.Quantity HAVING SUM(r.QuantityReturned)>o.Quantity)')
    domains = {'orders': 'Quantity IS NULL OR Quantity<=0 OR UnitPrice IS NULL OR UnitPrice<0 OR DiscountPct IS NULL OR DiscountPct<0 OR DiscountPct>1 OR OrderDate IS NULL',
               'products': 'UnitCost IS NULL OR UnitCost<0',
               'returns': 'QuantityReturned IS NULL OR QuantityReturned<=0',
               'sales_targets': "RevenueTarget IS NULL OR RevenueTarget<=0 OR substr(Month,9,2)<>'01'"}
    for table, condition in domains.items():
        check('invalid_domain_' + table, f'SELECT COUNT(*) FROM {quote(table)} WHERE {condition}')
    headers = {row[1] for row in connection.execute('PRAGMA table_info(returns)')}
    if 'ReturnID' in headers:
        check('invalid_return_id', "SELECT COUNT(*) FROM returns WHERE ReturnID IS NULL OR trim(ReturnID)=''")
        check('duplicate_return_id', 'SELECT COUNT(*) FROM (SELECT ReturnID FROM returns GROUP BY ReturnID HAVING COUNT(*)>1)')
    return checks


def execute_script(connection, text):
    results, statement = [], ''
    for char in text:
        statement += char
        if char == ';' and sqlite3.complete_statement(statement):
            cursor = connection.execute(statement)
            if cursor.description:
                results.append(([col[0] for col in cursor.description], cursor.fetchall()))
            statement = ''
    if statement.strip():
        if not sqlite3.complete_statement(statement + '\n;'):
            raise ValueError('Incomplete SQL statement')
        cursor = connection.execute(statement)
        if cursor.description:
            results.append(([col[0] for col in cursor.description], cursor.fetchall()))
    return results


def compare(actual, baseline, key=None):
    with Path(baseline).open(newline='', encoding='utf-8-sig') as stream:
        expected = list(csv.DictReader(stream))
    if len(actual) != len(expected):
        raise ValueError(f'{baseline}: row count mismatch')
    if key:
        actual = sorted(actual, key=lambda row: str(row[key]))
        expected = sorted(expected, key=lambda row: str(row[key]))
    for observed, wanted in zip(actual, expected):
        for column, value in wanted.items():
            if column not in observed or observed[column] is None:
                raise ValueError(f'{baseline}: missing value for {column}')
            try:
                left, right = Decimal(str(observed[column])), Decimal(value)
            except InvalidOperation:
                matches = str(observed[column]) == value
            else:
                tolerance = Decimal('0') if column in {'total_orders', 'order_lines', 'units_sold', 'revenue_rank', 'gross_profit_rank'} else Decimal('0.005')
                matches = left.is_finite() and right.is_finite() and abs(left-right) <= tolerance
            if not matches:
                raise ValueError(f'{baseline}: mismatch for {column}: {observed[column]} != {value}')


def run(root):
    root = Path(root)
    (root / 'build' / 'manifest.json').unlink(missing_ok=True)
    outputs = {}
    with sqlite3.connect(':memory:') as connection:
        load(connection, root / 'data')
        checks = validate(connection, COUNTS)
        for filename in SCRIPTS:
            text = (root / 'sql' / filename).read_text(encoding='utf-8-sig')
            for number, (headers, rows) in enumerate(execute_script(connection, text), 1):
                outputs[f'{Path(filename).stem}_{number}.csv'] = (headers, rows)
        for filename, baseline, key in [('04_executive_kpi_summary_1.csv', 'executive_kpis.csv', None),
                                        ('06_category_profitability_analysis_1.csv', 'category_profitability.csv', 'Category')]:
            headers, rows = outputs[filename]
            compare([dict(zip(headers, row)) for row in rows], root / 'results' / baseline, key)
    sources = [root / 'data' / (name + '.csv') for name in REQUIRED]
    sources += [root / 'sql' / name for name in SCRIPTS]
    sources += [root / 'results' / name for name in ['executive_kpis.csv', 'category_profitability.csv']]
    manifest = {'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version,
                'checks': checks, 'reference_comparisons': ['executive_kpis.csv', 'category_profitability.csv'],
                'sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    destination = root / 'build'
    destination.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination) as directory:
        stage = Path(directory)
        for name, (headers, rows) in outputs.items():
            with (stage / name).open('w', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream)
                writer.writerow(headers)
                writer.writerows(rows)
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        for path in sorted(stage.iterdir(), key=lambda p: p.name == 'manifest.json'):
            path.replace(destination / path.name)
    return manifest


if __name__ == '__main__':
    run(ROOT)
    print('Validation, all ten SQL scripts, and baseline comparisons passed. Outputs: build/')
