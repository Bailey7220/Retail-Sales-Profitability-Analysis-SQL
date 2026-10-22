# Reproduce and test the SQL analysis

## Requirements and commands

Use Python 3.12 (the CI version) with its bundled SQLite library. No pip packages or network access are required after obtaining this repository. The runner uses SQLite window functions, so SQLite must be at least 3.25.0. Commands below run from the repository root; scripts/reproduce.py also resolves paths independently of the calling directory.

```sh
python -m unittest discover -s tests -v
python scripts/reproduce.py
```

On Windows, use py -3.12 instead of python if appropriate. The runner creates a fresh in-memory database; it does not overwrite a local database or modify source CSVs, SQL scripts, or committed results.

## Executable loading contract

scripts/reproduce.py contains the executable table-creation/loading logic. The CSV header defines the retained columns. Known measures (quantity, price, discount, cost, returned quantity, and target) load as REAL; identifiers and other fields load as TEXT to preserve identifier formatting. Extra columns are retained as TEXT. Empty CSV fields become NULL; strings such as NULL are not silently treated as missing values. UTF-8 and UTF-8 BOM input are supported.

Missing required columns, case-insensitive duplicate headers, malformed field counts, invalid known date fields, and nonfinite numeric values stop execution. This is a typed analytical staging model, not a physical warehouse schema with enforced foreign keys. The intentionally missing StoreID values are preserved; validation distinguishes them from unknown non-null store references.

## Validation contract

The default snapshot expects 600 customers, 1,096 calendar rows, 44,290 order lines, 160 products, 2,657 return records, 155 targets, and 38 stores. It expects exactly 485 NULL StoreID order lines and no unknown non-null store IDs. Change these expectations deliberately when replacing the dataset; do not weaken checks merely to obtain a green run.

Checks cover required dimension/order-line/month-region keys, duplicate keys, customer/product/calendar matching, return-to-order-line matching, cumulative returned units not exceeding sold quantities, and numeric domains. ReturnID uniqueness is checked if that column exists; without it, event uniqueness is not established. Repeated returns against an order line are allowed when cumulative units do not exceed sold units. This is a targeted validation suite, not proof of every possible data-quality condition.

## Exact SQL execution and reconciliation

The runner executes the ten existing numbered SQL files in order, without replacing their logic. It handles multiple result sets, including both queries in script 08, and exports each result set separately. Script 03 creates the shared view and has no CSV result set.

The executive and category outputs are compared against their existing reference CSVs. Comparisons cover the columns present in those reference files, not every additional query column. Category rows match by Category regardless of ordering. Count/rank fields are exact; other numeric comparisons allow an absolute difference of 0.005 in the reported units. Text must match exactly. A mismatch fails the run; reference figures are never automatically replaced.

Successful output appears under build/, with a manifest recording Python/SQLite versions, checks, and SHA-256 hashes for all seven input CSVs, all ten executed SQL files, and the two reference files. A failed rerun invalidates the previous manifest; old CSV outputs may remain and must not be treated as a fresh passing result without a current matching manifest. CI uses a clean checkout and uploads artifacts only after success.

## Test evidence and verification boundaries

The fixture-based unittest suite was executed during preparation. Its tests exercise loading, validation failures, multi-statement parsing, reference mismatches, exports, and manifest invalidation. Fixture SQL used to test runner plumbing is not the project's analytical SQL. Full-data execution of the actual repository SQL was not performed in that preparation environment. The CI workflow is configured to perform that separate check; its presence does not establish a passing run.

No analytical SQL or published result was changed by this batch. Existing limitations remain: revenue is after discounts but not adjusted for returns; regional target reporting includes matched combinations only; the final sales month is incomplete. Calendar validity does not prove period completeness, and matching saved outputs does not independently prove the business definitions correct.
