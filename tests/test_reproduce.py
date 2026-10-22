import csv
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import reproduce as r


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.rows = {
            'customers': [['C01','Test','Customer','Basic','OK','2024-01-01']],
            'date_reference': [['2024-01-01']],
            'orders': [['O01','L01','2024-01-01','C01','P01','S01','Web','OK','2','50','0.1']],
            'products': [['P01','Widget','Test','Sub','Supplier','20']],
            'returns': [['O01','L01','1','Reason'], ['O01','L01','1','Reason']],
            'sales_targets': [['2024-01-01','South','100']],
            'stores': [['S01','Store','City','OK','South','Club']],
        }

    def load(self):
        for table, rows in self.rows.items():
            with (self.folder / (table + '.csv')).open('w', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream)
                writer.writerow(r.REQUIRED[table].split())
                writer.writerows(rows)
        connection = sqlite3.connect(':memory:')
        self.addCleanup(connection.close)
        r.load(connection, self.folder)
        return connection

    def test_valid_fixture_and_text_identifiers(self):
        db = self.load()
        checks = r.validate(db, {name: len(rows) for name, rows in self.rows.items()}, 0)
        self.assertTrue(checks)
        self.assertEqual(db.execute('SELECT OrderID FROM orders').fetchone()[0], 'O01')

    def test_duplicate_dimension_rejected(self):
        self.rows['products'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate_key_products'):
            r.validate(self.load(), missing_stores=0)

    def test_duplicate_order_line_rejected(self):
        self.rows['orders'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate_key_orders'):
            r.validate(self.load(), missing_stores=0)

    def test_missing_store_preserved(self):
        self.rows['orders'][0][5] = ''
        db = self.load()
        r.validate(db, missing_stores=1)
        self.assertIsNone(db.execute('SELECT StoreID FROM orders').fetchone()[0])

    def test_unknown_store_rejected(self):
        self.rows['orders'][0][5] = 'BAD'
        with self.assertRaisesRegex(ValueError, 'unknown_nonnull_stores'):
            r.validate(self.load(), missing_stores=0)

    def test_orphan_return_rejected(self):
        self.rows['returns'][0][0] = 'BAD'
        with self.assertRaisesRegex(ValueError, 'unmatched_return_lines'):
            r.validate(self.load(), missing_stores=0)

    def test_excess_cumulative_returns_rejected(self):
        self.rows['returns'][0][2] = '2'
        with self.assertRaisesRegex(ValueError, 'excess_return_units'):
            r.validate(self.load(), missing_stores=0)

    def test_discount_range_rejected(self):
        self.rows['orders'][0][-1] = '1.5'
        with self.assertRaisesRegex(ValueError, 'invalid_domain_orders'):
            r.validate(self.load(), missing_stores=0)

    def test_nonfinite_number_rejected(self):
        self.rows['orders'][0][-1] = 'nan'
        with self.assertRaises(ValueError):
            self.load()

    def test_invalid_date_rejected(self):
        self.rows['orders'][0][2] = '2024-02-30'
        with self.assertRaises(ValueError):
            self.load()

    def test_malformed_csv_row_rejected(self):
        self.rows['orders'][0].append('EXTRA')
        with self.assertRaisesRegex(ValueError, 'wrong field count'):
            self.load()

    def test_multiple_statements_and_quoted_semicolon(self):
        db = self.load()
        results = r.execute_script(db, "CREATE VIEW v AS SELECT 2 AS n; SELECT 'a;b' AS text; SELECT n FROM v; -- trailing comment")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][1], [('a;b',)])
        self.assertEqual(results[1][1], [(2,)])

    def test_baseline_mismatch_rejected(self):
        baseline = self.folder / 'baseline.csv'
        baseline.write_text('total_orders,net_revenue\n1,90.00\n', encoding='utf-8')
        r.compare([{'total_orders': 1, 'net_revenue': 90}], baseline)
        with self.assertRaises(ValueError):
            r.compare([{'total_orders': 2, 'net_revenue': 90}], baseline)
        with self.assertRaises(ValueError):
            r.compare([{'total_orders': 1, 'net_revenue': 91}], baseline)


    def test_full_fixture_pipeline_exports_and_hashes(self):
        from unittest.mock import patch
        db = self.load()
        db.close()
        (self.folder / 'data').mkdir()
        for path in self.folder.glob('*.csv'):
            path.replace(self.folder / 'data' / path.name)
        (self.folder / 'sql').mkdir()
        for name in r.SCRIPTS:
            (self.folder / 'sql' / name).write_text('SELECT 1 AS fixture_value;', encoding='utf-8')
        (self.folder / 'sql' / r.SCRIPTS[2]).write_text('CREATE VIEW fixture_view AS SELECT 1 AS n;', encoding='utf-8')
        (self.folder / 'sql' / r.SCRIPTS[3]).write_text('SELECT 1 AS total_orders, 90.0 AS net_revenue;', encoding='utf-8')
        (self.folder / 'sql' / r.SCRIPTS[5]).write_text("SELECT 'Test' AS Category, 90.0 AS net_revenue;", encoding='utf-8')
        (self.folder / 'sql' / r.SCRIPTS[7]).write_text('SELECT 1 AS a; SELECT 2 AS b;', encoding='utf-8')
        (self.folder / 'results').mkdir()
        (self.folder / 'results' / 'executive_kpis.csv').write_text('total_orders,net_revenue\n1,90.00\n', encoding='utf-8')
        (self.folder / 'results' / 'category_profitability.csv').write_text('Category,net_revenue\nTest,90.00\n', encoding='utf-8')
        # Match the production exception count without claiming a production-data test.
        (self.folder / 'data' / 'orders.csv').write_text(
            ','.join(r.REQUIRED['orders'].split()) + '\n' +
            '\n'.join(','.join([f'O{i}', 'L01', '2024-01-01', 'C01', 'P01', '', 'Web', 'OK', '2', '50', '0.1']) for i in range(485)) + '\n',
            encoding='utf-8')
        (self.folder / 'data' / 'returns.csv').write_text(','.join(r.REQUIRED['returns'].split()) + '\n', encoding='utf-8')
        counts = {name: len(rows) for name, rows in self.rows.items()}
        counts.update(orders=485, returns=0)
        with patch.object(r, 'COUNTS', counts):
            manifest = r.run(self.folder)
        self.assertEqual(len(list((self.folder / 'build').glob('*.csv'))), 10)
        self.assertEqual(len(manifest['sha256']), 19)
        self.assertTrue((self.folder / 'build' / 'manifest.json').is_file())
        (self.folder / 'results' / 'executive_kpis.csv').write_text('total_orders,net_revenue\n1,91.00\n', encoding='utf-8')
        with patch.object(r, 'COUNTS', counts), self.assertRaises(ValueError):
            r.run(self.folder)
        self.assertFalse((self.folder / 'build' / 'manifest.json').exists())


if __name__ == '__main__':
    unittest.main()
