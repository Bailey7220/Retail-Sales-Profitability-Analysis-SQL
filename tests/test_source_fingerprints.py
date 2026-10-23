import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from source_fingerprints import fingerprint_sources


class FingerprintTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'data').mkdir()
        self.payloads = {'orders': b'ID,Quantity\r\n1,2\r\n', 'stores': b'StoreID\n6201\n'}
        for table, payload in self.payloads.items():
            (self.root / 'data' / (table + '.csv')).write_bytes(payload)

    def test_forward_slash_keys_and_exact_bytes(self):
        actual = fingerprint_sources(self.root, self.payloads)
        self.assertEqual(set(actual), {'data/orders.csv', 'data/stores.csv'})
        self.assertTrue(all('\\' not in key for key in actual))
        for table, payload in self.payloads.items():
            self.assertEqual(actual[f'data/{table}.csv'], hashlib.sha256(payload).hexdigest())

    def test_string_root_supported(self):
        self.assertEqual(fingerprint_sources(str(self.root), self.payloads), fingerprint_sources(self.root, self.payloads))

    def test_changed_bytes_change_only_the_matching_hash(self):
        before = fingerprint_sources(self.root, self.payloads)
        (self.root / 'data' / 'orders.csv').write_bytes(b'ID,Quantity\n1,2\n')
        after = fingerprint_sources(self.root, self.payloads)
        self.assertNotEqual(before['data/orders.csv'], after['data/orders.csv'])
        self.assertEqual(before['data/stores.csv'], after['data/stores.csv'])

    def test_missing_file_fails(self):
        with self.assertRaises(FileNotFoundError):
            fingerprint_sources(self.root, ['missing'])


if __name__ == '__main__':
    unittest.main()
