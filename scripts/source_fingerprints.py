"""Platform-independent labels for byte-level source fingerprints."""
import hashlib
from pathlib import Path


def fingerprint_sources(root, tables):
    root = Path(root)
    return {
        f'data/{table}.csv': hashlib.sha256((root / 'data' / f'{table}.csv').read_bytes()).hexdigest()
        for table in tables
    }
