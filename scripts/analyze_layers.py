#!/usr/bin/env python3
"""Reproduce a known-dirty raw snapshot and validate a separate sales-only layer."""
import csv
import hashlib
import json
import sqlite3
import tempfile
from decimal import Decimal
from pathlib import Path
import reproduce as r
from source_fingerprints import fingerprint_sources

SOURCE_HASHES = {
    'stores': '8e6305ed4de31e398da49888c7d3233463e05eb1b92d58fe72f0826175f15bd1',
    'date_reference': 'b05f774e60a88b74c29b3218eba1dfc09dff514e84f25902325e6c84aa9dc3af',
    'sales_targets': '3a36c99e750bfc03a08e670cb13bbd97f8ca1e1db9cb4a1f24f2d74121b12feb',
    'returns': '912baca46588ac6bf1303880ecb3293f5aa95e25981dbc90b2576eb24360d65c',
    'orders': '77e7f97dd6f424e7dabd2ba27205f9f08eaae329d2b7804093f66d4a61f04d46',
    'products': '8487ef3d14325e23c83ef6d621c2ac75ebe9ae09a6716738ad12c0b963782c2c',
    'customers': '4fb0ef5faab9d4e85e4005e2db9a32d2ea2a7e8497a5ad42530e1b761caa6cf4',
}


def require_count(db, name, sql, expected=0):
    actual = db.execute(sql).fetchone()[0]
    if actual != expected:
        raise ValueError(f'{name}: expected {expected}, found {actual}')
    return {'actual': actual, 'expected': expected}


def validate_raw(db, counts, negative=249, missing=485, linked_returns=23):
    checks = {}
    def check(name, sql, expected=0):
        checks[name] = require_count(db, name, sql, expected)
    for table, count in counts.items():
        check('rows_' + table, f'SELECT COUNT(*) FROM {r.quote(table)}', count)
    keys = dict(r.KEYS, returns=['ReturnID'])
    for table, columns in keys.items():
        nulls = ' OR '.join(r.quote(c) + " IS NULL OR trim(" + r.quote(c) + ")=''" for c in columns)
        group = ','.join(r.quote(c) for c in columns)
        check('null_key_' + table, f'SELECT COUNT(*) FROM {r.quote(table)} WHERE {nulls}')
        check('duplicate_key_' + table, f'SELECT COUNT(*) FROM (SELECT 1 FROM {r.quote(table)} GROUP BY {group} HAVING COUNT(*)>1)')
    for key, dimension in [('CustomerID','customers'), ('ProductID','products')]:
        check('unmatched_' + key, f'SELECT COUNT(*) FROM orders o LEFT JOIN {dimension} d ON o.{key}=d.{key} WHERE d.{key} IS NULL')
    check('negative_quantity_lines', 'SELECT COUNT(*) FROM orders WHERE Quantity<0', negative)
    check('zero_or_missing_quantity', 'SELECT COUNT(*) FROM orders WHERE Quantity=0 OR Quantity IS NULL')
    check('missing_store_lines', 'SELECT COUNT(*) FROM orders WHERE StoreID IS NULL', missing)
    check('negative_with_known_store', 'SELECT COUNT(*) FROM orders WHERE Quantity<0 AND StoreID IS NOT NULL')
    check('unknown_nonnull_store', 'SELECT COUNT(*) FROM orders o LEFT JOIN stores s ON o.StoreID=s.StoreID WHERE o.StoreID IS NOT NULL AND s.StoreID IS NULL')
    check('unmatched_date', 'SELECT COUNT(*) FROM orders o LEFT JOIN date_reference d ON o.OrderDate=d.Date WHERE d.Date IS NULL')
    check('orphan_return', 'SELECT COUNT(*) FROM returns t LEFT JOIN orders o ON t.OrderID=o.OrderID AND t.OrderLineID=o.OrderLineID WHERE o.OrderID IS NULL')
    check('returns_on_negative_lines', 'SELECT COUNT(*) FROM returns t JOIN orders o ON t.OrderID=o.OrderID AND t.OrderLineID=o.OrderLineID WHERE o.Quantity<0', linked_returns)
    check('positive_sale_overreturn', 'SELECT COUNT(*) FROM (SELECT t.OrderID,t.OrderLineID FROM returns t JOIN orders o ON t.OrderID=o.OrderID AND t.OrderLineID=o.OrderLineID WHERE o.Quantity>0 GROUP BY t.OrderID,t.OrderLineID,o.Quantity HAVING SUM(t.QuantityReturned)>o.Quantity)')
    domains = {
        'orders': 'UnitPrice IS NULL OR UnitPrice<0 OR DiscountPct IS NULL OR DiscountPct<0 OR DiscountPct>1 OR OrderDate IS NULL',
        'products': 'UnitCost IS NULL OR UnitCost<0',
        'returns': 'QuantityReturned IS NULL OR QuantityReturned<=0',
        'sales_targets': "RevenueTarget IS NULL OR RevenueTarget<=0 OR substr(Month,9,2)<>'01'",
    }
    for table, condition in domains.items():
        check('invalid_domain_' + table, f'SELECT COUNT(*) FROM {r.quote(table)} WHERE {condition}')
    return checks


def partition(db):
    db.execute('CREATE TABLE quarantined_orders AS SELECT * FROM orders WHERE Quantity IS NULL OR Quantity<=0')
    db.execute('CREATE TABLE quarantined_returns AS SELECT t.* FROM returns t WHERE EXISTS (SELECT 1 FROM quarantined_orders q WHERE q.OrderID=t.OrderID AND q.OrderLineID=t.OrderLineID)')
    db.execute('DELETE FROM returns WHERE EXISTS (SELECT 1 FROM quarantined_orders q WHERE q.OrderID=returns.OrderID AND q.OrderLineID=returns.OrderLineID)')
    db.execute('DELETE FROM orders WHERE Quantity IS NULL OR Quantity<=0')
    db.commit()


def write_result(path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)


def analyze(db, root, destination):
    outputs = {}
    for filename in r.SCRIPTS:
        text = (root / 'sql' / filename).read_text(encoding='utf-8-sig')
        for number, (headers, rows) in enumerate(r.execute_script(db, text), 1):
            name = f'{Path(filename).stem}_{number}.csv'
            outputs[name] = [dict(zip(headers, row)) for row in rows]
            write_result(destination / name, headers, rows)
    return outputs


def run(root):
    root = Path(root)
    build = root / 'build'
    build.mkdir(exist_ok=True)
    (build / 'layers_manifest.json').unlink(missing_ok=True)
    inputs = fingerprint_sources(root, SOURCE_HASHES)
    for table, expected in SOURCE_HASHES.items():
        if inputs[f'data/{table}.csv'] != expected:
            raise ValueError(f'{table}: raw snapshot hash changed; review provenance and policy explicitly')
    with tempfile.TemporaryDirectory(dir=build) as directory:
        stage = Path(directory)
        with sqlite3.connect(':memory:') as raw, sqlite3.connect(':memory:') as sales:
            r.load(raw, root / 'data')
            raw_checks = validate_raw(raw, r.COUNTS)
            raw_outputs = analyze(raw, root, stage / 'raw')
            for generated, baseline, key in [('04_executive_kpi_summary_1.csv','executive_kpis.csv',None), ('06_category_profitability_analysis_1.csv','category_profitability.csv','Category')]:
                r.compare(raw_outputs[generated], root / 'results' / baseline, key)
            raw.backup(sales)
            partition(sales)
            require_count(sales, 'quarantined_orders', 'SELECT COUNT(*) FROM quarantined_orders', 249)
            require_count(sales, 'quarantined_returns', 'SELECT COUNT(*) FROM quarantined_returns', 23)
            expected = dict(r.COUNTS, orders=44041, returns=2634)
            sales_checks = r.validate(sales, expected, missing_stores=236)
            sales_outputs = analyze(sales, root, stage / 'sales_only')
            for table, reason in [('quarantined_orders','nonpositive or missing order quantity; intent unresolved'), ('quarantined_returns','linked sale has unresolved quantity; return not proven incorrect')]:
                cursor = sales.execute('SELECT * FROM ' + table + ' ORDER BY OrderID,OrderLineID')
                headers = [c[0] for c in cursor.description] + ['quarantine_reason']
                write_result(stage / 'quarantine' / (table + '.csv'), headers, [tuple(row) + (reason,) for row in cursor.fetchall()])
            first = raw_outputs['04_executive_kpi_summary_1.csv'][0]
            second = sales_outputs['04_executive_kpi_summary_1.csv'][0]
            comparison = [(metric, first[metric], second[metric], str(Decimal(str(second[metric])) - Decimal(str(first[metric])))) for metric in first]
            write_result(stage / 'kpi_comparison.csv', ['metric','raw_snapshot','sales_only','sales_only_minus_raw'], comparison)
            report = {'policy': 'sales-only eligibility exclusion; not source correction',
                      'raw_snapshot_is_clean': False, 'known_negative_order_lines':249,
                      'quarantined_return_records':23, 'positive_missing_store_lines_retained':236,
                      'raw_snapshot_checks':raw_checks, 'sales_only_checks':sales_checks,
                      'raw_kpis':first, 'sales_only_kpis':second,
                      'limitations':'Raw references include negative quantities. Sales-only excludes unresolved lines and related returns. Neither policy recovers source intent or proves all business definitions.'}
        for folder in ['sql','results']:
            for path in sorted((root / folder).glob('*')):
                if path.is_file():
                    inputs[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        for name in ['reproduce.py','analyze_layers.py','source_fingerprints.py']:
            inputs['scripts/' + name] = hashlib.sha256((root / 'scripts' / name).read_bytes()).hexdigest()
        report.update(python=r.platform.python_version(), sqlite=sqlite3.sqlite_version, sha256=inputs)
        (stage / 'layers_manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        for path in sorted(stage.rglob('*'), key=lambda p: p.name == 'layers_manifest.json'):
            if path.is_file():
                target = build / path.relative_to(stage)
                target.parent.mkdir(parents=True, exist_ok=True)
                path.replace(target)
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    run(Path(__file__).resolve().parents[1])
