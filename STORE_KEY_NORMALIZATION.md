# StoreID loading exception

The loader retains identifiers as TEXT with one explicit StoreID representation rule: an unsigned digit string followed by a decimal point and only zeros loses that decimal suffix. For example, 6201.0 and 6201.00 load as 6201 in both orders and stores. This is performed during in-memory loading; source CSVs are not edited.

Leading zeros are preserved: 006201.0 becomes 006201, not 6201. Blank fields remain NULL. Fractional or nonnumeric values are not silently truncated or converted. Duplicate normalized dimension keys and unknown non-null store references still fail validation. The expected missing-store count remains 485.

The original loader reproduces the reported failure pattern on decimal-formatted fixture keys. Seven new regression tests pass with this correction. The large source orders file could not be retrieved in the preparation environment, so the decimal-suffix explanation for the full-dataset failure remains a hypothesis until checked by the next full-data run. No full-data pass or reference-result reconciliation is claimed by this correction. Existing analytical SQL and reference figures are unchanged.
