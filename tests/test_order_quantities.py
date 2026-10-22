import unittest
import test_reproduce as fixtures
import reproduce as r


class OrderQuantityTests(unittest.TestCase):
    def fixture(self, quantity, returned):
        case = fixtures.WorkflowTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        case.rows['orders'][0][9] = quantity
        case.rows['returns'] = [['O01','L01',returned,'Reason']]
        return case.load()

    def test_negative_quantity_reported_before_return_limit(self):
        with self.assertRaisesRegex(ValueError, 'invalid_order_quantities'):
            r.validate(self.fixture('-4','4'), missing_stores=0)

    def test_zero_quantity_rejected(self):
        with self.assertRaisesRegex(ValueError, 'invalid_order_quantities'):
            r.validate(self.fixture('0','1'), missing_stores=0)

    def test_missing_quantity_rejected(self):
        with self.assertRaisesRegex(ValueError, 'invalid_order_quantities'):
            r.validate(self.fixture('','1'), missing_stores=0)

    def test_genuine_positive_sale_overreturn_still_rejected(self):
        with self.assertRaisesRegex(ValueError, 'excess_return_units'):
            r.validate(self.fixture('2','3'), missing_stores=0)


if __name__ == '__main__':
    unittest.main()
