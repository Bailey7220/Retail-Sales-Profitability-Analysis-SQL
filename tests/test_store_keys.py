import csv
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import reproduce as r


class StoreKeyRegressionTests(unittest.TestCase):
    def fixture(self, order_key, store_key, duplicate=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        folder = Path(temporary.name)
        rows = {
            'customers': [['C01','Test','Customer','Basic','OK','2024-01-01']],
            'date_reference': [['2024-01-01']],
            'orders': [['O01','L01','2024-01-01','C01','P01',order_key,'Web','OK','2','50','0.1']],
            'products': [['P01','Widget','Test','Sub','Supplier','20']],
            'returns': [],
            'sales_targets': [['2024-01-01','South','100']],
            'stores': [[store_key,'Store','City','OK','South','Club']],
        }
        if duplicate:
            rows['stores'].append(['6201.0','Other','City','OK','South','Club'])
        for table, values in rows.items():
            with (folder / (table + '.csv')).open('w', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream)
                writer.writerow(r.REQUIRED[table].split())
                writer.writerows(values)
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        r.load(db, folder)
        return db

    def test_decimal_export_matches_integer_dimension(self):
        db = self.fixture('6201.0', '6201')
        r.validate(db, missing_stores=0)
        count = db.execute('SELECT COUNT(*) FROM orders o JOIN stores s ON o.StoreID=s.StoreID').fetchone()[0]
        self.assertEqual(count, 1)

    def test_both_tables_use_the_same_normalization(self):
        db = self.fixture('6201', '6201.00')
        r.validate(db, missing_stores=0)

    def test_leading_zeros_are_preserved(self):
        db = self.fixture('006201.0', '006201')
        r.validate(db, missing_stores=0)
        self.assertEqual(db.execute('SELECT StoreID FROM orders').fetchone()[0], '006201')

    def test_distinct_leading_zero_key_is_not_merged(self):
        db = self.fixture('006201.0', '6201')
        with self.assertRaisesRegex(ValueError, 'unknown_nonnull_stores'):
            r.validate(db, missing_stores=0)

    def test_fractional_identifier_is_not_truncated(self):
        db = self.fixture('6201.5', '6201')
        with self.assertRaisesRegex(ValueError, 'unknown_nonnull_stores'):
            r.validate(db, missing_stores=0)

    def test_duplicate_created_by_normalization_is_rejected(self):
        db = self.fixture('6201.0', '6201', duplicate=True)
        with self.assertRaisesRegex(ValueError, 'duplicate_key_stores'):
            r.validate(db, missing_stores=0)

    def test_blank_key_remains_missing(self):
        db = self.fixture('', '6201')
        r.validate(db, missing_stores=1)
        self.assertIsNone(db.execute('SELECT StoreID FROM orders').fetchone()[0])


if __name__ == '__main__':
    unittest.main()
