import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import analyze_layers as layers


class LayerTests(unittest.TestCase):
    def fixture(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.executescript("""
        CREATE TABLE customers(CustomerID TEXT);
        CREATE TABLE products(ProductID TEXT,UnitCost REAL);
        CREATE TABLE stores(StoreID TEXT);
        CREATE TABLE date_reference(Date TEXT);
        CREATE TABLE sales_targets(Month TEXT,Region TEXT,RevenueTarget REAL);
        CREATE TABLE orders(OrderID TEXT,OrderLineID TEXT,CustomerID TEXT,ProductID TEXT,StoreID TEXT,OrderDate TEXT,Quantity REAL,UnitPrice REAL,DiscountPct REAL);
        CREATE TABLE returns(ReturnID TEXT,OrderID TEXT,OrderLineID TEXT,QuantityReturned REAL);
        INSERT INTO customers VALUES ('C');
        INSERT INTO products VALUES ('P',5);
        INSERT INTO stores VALUES ('S');
        INSERT INTO date_reference VALUES ('2024-01-01');
        INSERT INTO sales_targets VALUES ('2024-01-01','R',100);
        INSERT INTO orders VALUES ('A','1','C','P',NULL,'2024-01-01',-4,10,0);
        INSERT INTO orders VALUES ('A','2','C','P',NULL,'2024-01-01',2,10,0);
        INSERT INTO orders VALUES ('B','1','C','P','S','2024-01-01',3,10,0);
        INSERT INTO returns VALUES ('R1','A','1',4);
        INSERT INTO returns VALUES ('R2','A','2',1);
        """)
        db.commit()
        counts = dict(customers=1,products=1,stores=1,date_reference=1,sales_targets=1,orders=3,returns=2)
        return db, counts

    def test_raw_exceptions_are_explicit(self):
        db, counts = self.fixture()
        checks = layers.validate_raw(db, counts, negative=1, missing=2, linked_returns=1)
        self.assertEqual(checks['negative_quantity_lines']['actual'],1)

    def test_unexpected_negative_count_fails(self):
        db, counts = self.fixture()
        with self.assertRaisesRegex(ValueError,'negative_quantity_lines'):
            layers.validate_raw(db,counts,negative=0,missing=2,linked_returns=1)

    def test_known_store_negative_is_not_accepted(self):
        db, counts = self.fixture()
        db.execute("UPDATE orders SET StoreID='S' WHERE Quantity<0")
        with self.assertRaisesRegex(ValueError,'negative_with_known_store'):
            layers.validate_raw(db,counts,negative=1,missing=1,linked_returns=1)

    def test_other_domains_are_not_waived(self):
        db, counts = self.fixture()
        db.execute('UPDATE orders SET DiscountPct=2 WHERE Quantity<0')
        with self.assertRaisesRegex(ValueError,'invalid_domain_orders'):
            layers.validate_raw(db,counts,negative=1,missing=2,linked_returns=1)

    def test_positive_overreturn_fails(self):
        db, counts = self.fixture()
        db.execute("UPDATE returns SET QuantityReturned=3 WHERE ReturnID='R2'")
        with self.assertRaisesRegex(ValueError,'positive_sale_overreturn'):
            layers.validate_raw(db,counts,negative=1,missing=2,linked_returns=1)

    def test_partition_preserves_raw_and_links(self):
        raw, counts = self.fixture()
        sales = sqlite3.connect(':memory:')
        self.addCleanup(sales.close)
        raw.backup(sales)
        layers.partition(sales)
        self.assertEqual(raw.execute('SELECT COUNT(*) FROM orders').fetchone()[0],3)
        self.assertEqual(raw.execute('SELECT Quantity FROM orders WHERE Quantity<0').fetchone()[0],-4)
        self.assertEqual(sales.execute('SELECT COUNT(*) FROM orders').fetchone()[0],2)
        self.assertEqual(sales.execute('SELECT COUNT(*) FROM returns').fetchone()[0],1)
        self.assertEqual(sales.execute('SELECT Quantity FROM quarantined_orders').fetchone()[0],-4)
        self.assertEqual(sales.execute('SELECT QuantityReturned FROM quarantined_returns').fetchone()[0],4)
        self.assertEqual(sales.execute('SELECT COUNT(*) FROM orders WHERE StoreID IS NULL').fetchone()[0],1)
        self.assertEqual(sales.execute('SELECT ReturnID FROM returns').fetchone()[0],'R2')


if __name__ == '__main__':
    unittest.main()
